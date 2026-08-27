"""Evaluation harness runner.

Usage (from backend/, with the venv active):
    python -m evaluation.runner                  # run the full dataset
    python -m evaluation.runner --case bull_bear_debate
    python -m evaluation.runner --judge           # + an LLM-judge quality pass (extra Groq calls)

Each case is checked structurally (right tickers, right agents, valid
overall_assessment shape, non-trivial report) rather than against exact text,
since LLM output is non-deterministic (see spec §30 / this project's plan).
Results are persisted via app.repositories.evaluation when DATABASE_URL is
configured; the harness still runs and prints its summary without one.
"""
import argparse
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.api.dependencies import get_llm_provider, get_workflow
from evaluation.dataset import CASES, DATASET_NAME, EvalCase

logging.basicConfig(level=logging.WARNING)  # keep the summary table readable
logger = logging.getLogger("finagent.evaluation")

VALID_OUTLOOKS = {
    "Strongly Positive", "Positive", "Neutral", "Negative",
    "Strongly Negative", "Insufficient Evidence",
}


@dataclass
class EvalResult:
    case: EvalCase
    passed: bool
    latency_seconds: float
    tickers_found: List[str] = field(default_factory=list)
    agents_run: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    judge_score: Optional[int] = None
    judge_reasoning: Optional[str] = None


def _check_structure(case: EvalCase, state: Dict[str, Any]) -> List[str]:
    """Return a list of failure reasons (empty = structurally valid)."""
    failures = []

    tickers = state.get("tickers", [])
    missing_tickers = [t for t in case.expected_tickers if t not in tickers]
    if missing_tickers:
        failures.append(f"missing expected tickers: {missing_tickers} (got {tickers})")

    agents_run = state.get("completed_agents", [])
    missing_agents = [a for a in case.expected_agents if a not in agents_run]
    if missing_agents:
        failures.append(f"missing expected agents: {missing_agents} (got {agents_run})")

    assessment = state.get("overall_assessment", {})
    for key in ("overall_outlook", "confidence", "strengths", "risks", "key_uncertainties"):
        if key not in assessment:
            failures.append(f"overall_assessment missing key '{key}'")
    if assessment.get("overall_outlook") not in VALID_OUTLOOKS:
        failures.append(f"invalid overall_outlook: {assessment.get('overall_outlook')!r}")
    if not isinstance(assessment.get("confidence"), (int, float)):
        failures.append("confidence is not numeric")

    report = state.get("final_report", "")
    if len(report) < case.min_report_chars:
        failures.append(f"final_report too short ({len(report)} chars < {case.min_report_chars})")

    if case.debate:
        debate = state.get("debate_results", {})
        if not debate.get("bull_case") or not debate.get("bear_case"):
            failures.append("debate mode requested but bull_case/bear_case missing")

    unexpected_errors = state.get("errors", [])
    if unexpected_errors:
        failures.append(f"agent(s) reported errors: {unexpected_errors}")

    return failures


async def _judge_quality(llm_provider, case: EvalCase, state: Dict[str, Any]) -> tuple[Optional[int], Optional[str]]:
    """Optional lightweight LLM-as-judge pass: is the report grounded and on-topic?"""
    report = state.get("final_report", "")[:3000]
    prompt = f"""
    Question asked: {case.query}

    Generated report:
    {report}

    Rate this report 1-5 on: (a) it directly addresses the question, (b) claims
    read as grounded in specific data/evidence rather than generic filler,
    (c) it does not claim certainty about future prices. Respond with ONLY a
    JSON object: {{"score": int 1-5, "reasoning": "one sentence"}}
    """
    response = await llm_provider.generate(
        prompt=prompt,
        system_prompt="You are a strict grader of financial research reports. Output raw JSON only.",
        temperature=0.0,
        max_tokens=200,
    )
    if not response.success:
        return None, f"judge call failed: {response.error}"
    try:
        start = response.content.find("{")
        end = response.content.rfind("}") + 1
        data = json.loads(response.content[start:end])
        return int(data.get("score", 0)), data.get("reasoning")
    except (ValueError, json.JSONDecodeError):
        return None, "judge response was not valid JSON"


async def run_case(case: EvalCase, workflow, llm_provider, use_judge: bool = False) -> EvalResult:
    start = time.monotonic()
    state = await workflow.run(case.query, debate=case.debate)
    latency = time.monotonic() - start

    failures = _check_structure(case, state)
    result = EvalResult(
        case=case,
        passed=not failures,
        latency_seconds=round(latency, 2),
        tickers_found=state.get("tickers", []),
        agents_run=state.get("completed_agents", []),
        failures=failures,
    )

    if use_judge:
        score, reasoning = await _judge_quality(llm_provider, case, state)
        result.judge_score = score
        result.judge_reasoning = reasoning

    # Best-effort persistence; the harness still works with no database configured.
    from app.repositories.evaluation import record_evaluation_run

    await record_evaluation_run(
        dataset_name=DATASET_NAME,
        case_name=case.name,
        query=case.query,
        passed=result.passed,
        latency_seconds=result.latency_seconds,
        details={
            "tickers_found": result.tickers_found,
            "agents_run": result.agents_run,
            "failures": result.failures,
            "judge_score": result.judge_score,
            "judge_reasoning": result.judge_reasoning,
        },
    )

    return result


def _print_summary(results: List[EvalResult]) -> None:
    passed = sum(1 for r in results if r.passed)
    print(f"\n{'Case':<28} {'Result':<8} {'Latency':>8}  {'Judge':>6}  Notes")
    print("-" * 100)
    for r in results:
        note = "; ".join(r.failures) if r.failures else ""
        judge = f"{r.judge_score}/5" if r.judge_score is not None else "-"
        print(f"{r.case.name:<28} {'PASS' if r.passed else 'FAIL':<8} {r.latency_seconds:>7.1f}s  {judge:>6}  {note}")
    print("-" * 100)
    print(f"{passed}/{len(results)} cases passed. Average latency: {sum(r.latency_seconds for r in results) / len(results):.1f}s")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FinAgent evaluation harness")
    parser.add_argument("--case", help="Run only the named case")
    parser.add_argument("--judge", action="store_true", help="Also run an LLM-judge quality pass (extra Groq calls)")
    args = parser.parse_args()

    cases = [c for c in CASES if c.name == args.case] if args.case else CASES
    if not cases:
        print(f"No case named '{args.case}'. Available: {[c.name for c in CASES]}")
        return

    llm_provider = get_llm_provider()
    workflow = get_workflow()

    results = []
    for case in cases:
        print(f"Running: {case.name} ...")
        result = await run_case(case, workflow, llm_provider, use_judge=args.judge)
        results.append(result)

    _print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
