"""Bear Agent - argues the strongest evidence-backed negative case"""
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.agents.evidence import build_evidence_dossier

logger = logging.getLogger(__name__)


class BearAgent(BaseAgent):
    """Argues the strongest negative case using only the gathered evidence."""

    def __init__(self, llm_provider):
        super().__init__("BearCase", llm_provider)

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        evidence_text, has_evidence = build_evidence_dossier(state)
        if not has_evidence:
            return {"debate_results": {"bear_case": "Insufficient evidence to construct a bear case."}}

        prompt = f"""
        Tickers: {state.get("tickers", [])}

        EVIDENCE:
        {evidence_text}

        Argue the STRONGEST negative/cautionary investment case supported by this evidence. Structure it as:
        1. Thesis (1-2 sentences)
        2. 3-5 supporting points, each citing a specific figure or fact from the evidence above

        Rules: Use ONLY the evidence provided - never invent metrics or news. If the evidence is
        genuinely weak, say so rather than overstating the case. Write in plain prose paragraphs -
        no markdown headers, bold/asterisks, or tables (this text is rendered as-is in a UI card).
        """
        system_prompt = """You are the Bear Case analyst in an internal investment debate. Your job is
        to make the strongest evidence-backed case AGAINST the investment, arguing in good faith - not
        to mislead. Every point must trace back to the evidence given. Plain prose, no markdown."""

        response = await self.call_llm(prompt, system_prompt, max_tokens=800)
        return {"debate_results": {"bear_case": response}}
