"""Judge Agent - evaluates the Bull vs. Bear debate against the evidence"""
import json
import logging
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent
from app.agents.evidence import build_evidence_dossier

logger = logging.getLogger(__name__)

VALID_VERDICTS = {"bull", "bear", "even"}


class JudgeAgent(BaseAgent):
    """Weighs the Bull and Bear cases against the evidence and renders a verdict."""

    def __init__(self, llm_provider):
        super().__init__("Judge", llm_provider)

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        debate = state.get("debate_results", {})
        bull_case = debate.get("bull_case", "")
        bear_case = debate.get("bear_case", "")

        if not bull_case and not bear_case:
            return {"debate_results": {"verdict": self._empty_verdict()}}

        evidence_text, _ = build_evidence_dossier(state)

        prompt = f"""
        Tickers: {state.get("tickers", [])}

        EVIDENCE:
        {evidence_text}

        BULL CASE:
        {bull_case}

        BEAR CASE:
        {bear_case}

        Evaluate which case is better SUPPORTED BY THE EVIDENCE (not which is more persuasively
        written). Respond with ONLY a JSON object (no markdown fences):
        {{
          "stronger_case": "bull" | "bear" | "even",
          "reasoning": "2-4 sentences on why, citing which specific points held up under the evidence",
          "key_disagreements": ["short bullet", "..."],
          "unresolved_uncertainty": ["short bullet describing what the evidence doesn't settle either way", "..."],
          "confidence": float between 0 and 1
        }}
        """
        system_prompt = """You are an impartial Judge in an internal investment debate. You evaluate
        arguments strictly on evidentiary support, not rhetoric. You are willing to call it "even" when
        the evidence is genuinely mixed or thin. Output raw JSON only."""

        response = await self.call_llm(prompt, system_prompt, temperature=0.1, max_tokens=700)
        verdict = self._extract_json(response) or self._empty_verdict()

        return {"debate_results": {"verdict": verdict}}

    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        if not response or response.startswith("Error"):
            return None
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start < 0 or end <= start:
                return None
            data = json.loads(response[start:end])
            if data.get("stronger_case") not in VALID_VERDICTS:
                data["stronger_case"] = "even"
            return data
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse judge verdict JSON: {e}")
            return None

    def _empty_verdict(self) -> Dict[str, Any]:
        return {
            "stronger_case": "even",
            "reasoning": "Insufficient debate evidence to render a verdict.",
            "key_disagreements": [],
            "unresolved_uncertainty": [],
            "confidence": 0.0,
        }
