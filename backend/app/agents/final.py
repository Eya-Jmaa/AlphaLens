"""Final Analyst Agent - Synthesizes every specialized agent's output into one report"""
import json
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.agents.evidence import build_evidence_dossier, truncate

logger = logging.getLogger(__name__)

VALID_OUTLOOKS = {
    "Strongly Positive", "Positive", "Neutral", "Negative",
    "Strongly Negative", "Insufficient Evidence",
}


class FinalAnalystAgent(BaseAgent):
    """Synthesizes stock/news/SEC/risk/technical results (and, when present, the
    Bull/Bear/Judge debate) into one cited report."""

    def __init__(self, llm_provider):
        super().__init__("FinalAnalyst", llm_provider)

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize all populated agent results into a final report + assessment"""
        self.logger.info("Synthesizing final report")

        evidence_text, has_any_evidence = build_evidence_dossier(state)
        debate_text = self._format_debate(state)

        if not has_any_evidence:
            assessment = self._empty_assessment(state)
            return {
                "final_report": (
                    "No analysis data was available to synthesize (no tickers matched, "
                    "or all specialized agents failed). See errors/warnings for details."
                ),
                "overall_assessment": assessment,
                "confidence": 0.0,
            }

        parsed = await self._generate_structured_report(state, evidence_text, debate_text)

        if parsed:
            report_text = self._render_markdown(state, parsed)
            assessment = {
                "tickers": state.get("tickers", []),
                "overall_outlook": parsed.get("overall_outlook", "Neutral"),
                "confidence": float(parsed.get("confidence", 0.5)),
                "strengths": parsed.get("strengths", []),
                "risks": parsed.get("risks", []),
                "key_uncertainties": parsed.get("key_uncertainties", []),
            }
            self.logger.info("Final report generated (structured)")
            return {
                "final_report": report_text,
                "overall_assessment": assessment,
                "confidence": assessment["confidence"],
            }

        # Structured parse failed - fall back to a plain-text report from the same call
        self.logger.warning("Final report JSON parse failed, falling back to raw text")
        fallback_text = await self._generate_fallback_report(state, evidence_text, debate_text)
        assessment = self._heuristic_assessment(state, fallback_text)
        return {
            "final_report": fallback_text,
            "overall_assessment": assessment,
            "confidence": assessment["confidence"],
        }

    # ------------------------------------------------------------------
    # Debate (optional - only present when Bull/Bear/Judge ran)
    # ------------------------------------------------------------------

    def _format_debate(self, state: Dict[str, Any]) -> str:
        debate = state.get("debate_results")
        if not debate:
            return ""

        parts = ["=== BULL VS. BEAR DEBATE ==="]
        if debate.get("bull_case"):
            parts.append("BULL CASE:\n" + truncate(debate["bull_case"]))
        if debate.get("bear_case"):
            parts.append("BEAR CASE:\n" + truncate(debate["bear_case"]))
        verdict = debate.get("verdict")
        if verdict:
            parts.append(
                "JUDGE'S VERDICT:\n"
                f"Stronger case: {verdict.get('stronger_case', 'N/A')}\n"
                f"{truncate(verdict.get('reasoning', ''))}"
            )
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # LLM synthesis
    # ------------------------------------------------------------------

    async def _generate_structured_report(
        self, state: Dict[str, Any], evidence_text: str, debate_text: str
    ) -> Dict[str, Any] | None:
        debate_block = f"\n\n{debate_text}\n" if debate_text else ""
        debate_field = (
            '"debate_summary": "1-2 sentence summary of which side of the bull/bear debate the evidence favors, '
            'omit if no debate section was provided",\n          '
            if debate_text
            else ""
        )

        prompt = f"""
        Synthesize a complete investment research report from the evidence below.

        User query: {state.get("user_query", "N/A")}
        Tickers: {state.get("tickers", [])}

        EVIDENCE FROM SPECIALIZED AGENTS:
        {evidence_text}
        {debate_block}
        Respond with ONLY a JSON object (no markdown fences) with exactly these keys:
        {{
          "executive_summary": "2-4 sentence overview",
          "fundamental_analysis": "valuation, growth, financial health",
          "news_sentiment": "summary of news/sentiment evidence, or 'Insufficient recent news data.' if none was provided",
          "sec_insights": "summary of SEC filing evidence with citations, or 'No SEC filing evidence available.' if none",
          "technical_analysis": "trend/momentum summary from indicators, or 'No technical data available.' if none",
          "risk_analysis": "volatility/drawdown/VaR summary, or 'No risk data available.' if none",
          {debate_field}"strengths": ["short bullet", "..."],
          "risks": ["short bullet", "..."],
          "key_uncertainties": ["short bullet", "..."],
          "overall_outlook": one of "Strongly Positive", "Positive", "Neutral", "Negative", "Strongly Negative", "Insufficient Evidence",
          "confidence": float between 0 and 1 reflecting how much evidence actually backs this
        }}

        Rules:
        - Base every claim ONLY on the evidence above. Never invent metrics, news, or filing content.
        - If a section has no supporting evidence, say so explicitly in that field instead of guessing.
        - Never claim certainty about future prices; use evidence-consistent language (e.g. "the available evidence is consistent with...").
        """

        system_prompt = """You are the Final Analyst: a senior financial analyst who synthesizes
        other agents' evidence into one objective report. You never introduce facts that
        aren't present in the evidence you were given. Output raw JSON only."""

        response = await self.call_llm(prompt, system_prompt, temperature=0.2, max_tokens=1800)
        return self._extract_json(response)

    async def _generate_fallback_report(self, state: Dict[str, Any], evidence_text: str, debate_text: str) -> str:
        debate_block = f"\n\n{debate_text}\n" if debate_text else ""
        prompt = f"""
        Write a comprehensive financial analysis report based on the evidence below.
        Query: {state.get("user_query", "N/A")}
        Tickers: {state.get("tickers", [])}

        EVIDENCE:
        {evidence_text}
        {debate_block}
        Structure: Executive Summary, Fundamental Analysis, News & Sentiment, SEC Insights,
        Technical Analysis, Risk Analysis, Strengths, Risks, Key Uncertainties, Overall Assessment.
        Be objective and data-driven. Do not invent information.
        """
        system_prompt = """You are a senior financial analyst. Base your analysis solely on the
        evidence provided. Clearly distinguish facts from interpretation."""
        return await self.call_llm(prompt, system_prompt, max_tokens=1800)

    def _extract_json(self, response: str) -> Dict[str, Any] | None:
        if not response or response.startswith("Error"):
            return None
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start < 0 or end <= start:
                return None
            data = json.loads(response[start:end])
            if data.get("overall_outlook") not in VALID_OUTLOOKS:
                data["overall_outlook"] = "Neutral"
            return data
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse final report JSON: {e}")
            return None

    def _render_markdown(self, state: Dict[str, Any], parsed: Dict[str, Any]) -> str:
        tickers = ", ".join(state.get("tickers", [])) or "N/A"
        sections = [
            f"# Investment Research Report: {tickers}",
            "## Executive Summary\n" + parsed.get("executive_summary", ""),
            "## Fundamental Analysis\n" + parsed.get("fundamental_analysis", ""),
            "## News & Sentiment\n" + parsed.get("news_sentiment", ""),
            "## SEC Filing Insights\n" + parsed.get("sec_insights", ""),
            "## Technical Analysis\n" + parsed.get("technical_analysis", ""),
            "## Risk Analysis\n" + parsed.get("risk_analysis", ""),
        ]
        if parsed.get("debate_summary"):
            sections.append("## Bull vs. Bear Debate\n" + parsed["debate_summary"])
        sections.extend([
            "## Strengths\n" + "\n".join(f"- {s}" for s in parsed.get("strengths", [])),
            "## Risks\n" + "\n".join(f"- {r}" for r in parsed.get("risks", [])),
            "## Key Uncertainties\n" + "\n".join(f"- {u}" for u in parsed.get("key_uncertainties", [])),
            f"## Overall Assessment\n{parsed.get('overall_outlook', 'Neutral')} "
            f"(confidence: {float(parsed.get('confidence', 0.5)):.0%})",
        ])
        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Fallbacks
    # ------------------------------------------------------------------

    def _empty_assessment(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "tickers": state.get("tickers", []),
            "overall_outlook": "Insufficient Evidence",
            "confidence": 0.0,
            "strengths": [],
            "risks": [],
            "key_uncertainties": ["No agent data was available to analyze."],
        }

    def _heuristic_assessment(self, state: Dict[str, Any], report_text: str) -> Dict[str, Any]:
        text_lower = report_text.lower()
        outlook = "Neutral"
        if "strong" in text_lower and "growth" in text_lower:
            outlook = "Positive"
        elif "risk" in text_lower or "uncertain" in text_lower:
            outlook = "Negative"
        return {
            "tickers": state.get("tickers", []),
            "overall_outlook": outlook,
            "confidence": 0.4,
            "strengths": [],
            "risks": [],
            "key_uncertainties": ["Structured synthesis unavailable; this is a heuristic fallback assessment."],
        }
