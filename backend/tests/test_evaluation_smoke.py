"""Smoke test for the evaluation harness itself (not the full benchmark - that
hits live Groq/yfinance/etc. and is run manually via `python -m evaluation.runner`).
Marked slow: excluded from the default `pytest` run, included with `pytest -m slow`.
"""
import pytest

from app.api.dependencies import get_llm_provider, get_workflow
from evaluation.dataset import CASES
from evaluation.runner import run_case


@pytest.mark.slow
@pytest.mark.asyncio
async def test_single_case_runs_end_to_end():
    """Runs one cheap real case through the live workflow and checks the harness
    itself produces a structurally-valid pass - not a mock, an actual integration
    check that Groq/yfinance/the graph are wired together correctly."""
    case = next(c for c in CASES if c.name == "single_company_overview")
    workflow = get_workflow()
    llm_provider = get_llm_provider()

    result = await run_case(case, workflow, llm_provider, use_judge=False)

    assert result.passed, f"Eval case failed: {result.failures}"
    assert "NVDA" in result.tickers_found
    assert result.latency_seconds > 0
