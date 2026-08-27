"""SEC Filing Agent - RAG-based analysis over real SEC EDGAR filings"""
import logging
from typing import Any, Dict, List

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class SECAgent(BaseAgent):
    """SEC Filing Agent: retrieves cited evidence from ingested 10-K/10-Q filings via RAG."""

    def __init__(self, llm_provider, sec_rag_service=None):
        super().__init__("SECAnalysis", llm_provider)
        self.rag_service = sec_rag_service
        if self.rag_service is None:
            # Constructed lazily by the caller (app/graph/workflow.py) which
            # catches ImportError/other init failures and drops this agent
            # from the graph, so the rest of the analysis still works.
            from app.services.sec_rag_service import SECRagService
            self.rag_service = SECRagService()
        logger.info("SECAgent initialized with RAG pipeline")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve and analyze SEC filing evidence for tickers in state"""
        tickers = state.get("tickers", [])
        self.logger.info(f"Analyzing SEC filings for: {tickers}")

        if not tickers:
            return {"errors": ["No tickers for SEC analysis"]}

        question = state.get("user_query") or "What are the company's key risks and financial highlights?"

        results: List[Dict[str, Any]] = []
        errors: List[str] = []

        for ticker in tickers:
            try:
                rag_result = await self.rag_service.answer(ticker, question, top_k=5)

                if not rag_result["results"]:
                    results.append({
                        "ticker": ticker,
                        "status": "insufficient_evidence",
                        "message": (
                            "No SEC filing evidence could be retrieved for this ticker "
                            "(filing may be unavailable or SEC EDGAR rate-limited this request)."
                        ),
                        "filings": rag_result.get("filings", []),
                    })
                    continue

                is_live = any(
                    r["metadata"].get("source") == "sec_edgar" for r in rag_result["results"]
                )
                analysis = await self._analyze_filing_evidence(
                    ticker, question, rag_result["context"], is_live_edgar_data=is_live
                )

                results.append({
                    "ticker": ticker,
                    "status": "ok",
                    "analysis": analysis,
                    "is_live_edgar_data": is_live,
                    "filings": rag_result["filings"],
                    "sources": [
                        {
                            "filing_type": r["metadata"].get("filing_type"),
                            "filing_date": r["metadata"].get("filing_date"),
                            "section": r["metadata"].get("section"),
                            "url": r["metadata"].get("source_url"),
                            "source": r["metadata"].get("source", "sample_data"),
                        }
                        for r in rag_result["results"]
                    ],
                })

            except Exception as e:
                self.logger.error(f"SEC analysis failed for {ticker}: {e}")
                errors.append(f"SEC analysis failed for {ticker}: {str(e)}")

        return {"sec_analysis_results": results, "errors": errors}

    async def _analyze_filing_evidence(
        self, ticker: str, question: str, context: str, is_live_edgar_data: bool
    ) -> str:
        """Ask the LLM to answer strictly from retrieved filing evidence, with citations."""
        provenance_notice = (
            ""
            if is_live_edgar_data
            else (
                "\nIMPORTANT: These excerpts are bundled SAMPLE/DEMO filing data, not a live "
                "SEC EDGAR fetch (EDGAR was unavailable or rate-limited for this request). "
                "You MUST open your answer with a one-line notice that this is sample data, "
                "not the company's actual current filing.\n"
            )
        )

        prompt = f"""
        Using ONLY the SEC filing excerpts below, answer this question about {ticker}:
        "{question}"
        {provenance_notice}
        RETRIEVED FILING EXCERPTS:
        {context}

        Rules:
        - Base every claim strictly on the excerpts above. Do not use outside knowledge.
        - Cite the filing type and date for each claim (e.g. "per the 10-K filed 2025-XX-XX").
        - If the excerpts don't fully answer the question, explicitly say what is missing.
        - Keep it concise: key risks, notable financial/business points, and direct quotes where useful.
        - Write in plain prose paragraphs - no markdown headers, bold/asterisks, or bullet lists.
          This text is shown as-is in a UI card, not rendered as a formatted document.
        """

        system_prompt = """You are the SEC Filing Analyst. You only answer from retrieved evidence,
        never from memory, and you write in plain prose (no markdown formatting - this text is
        rendered as-is in a UI card). Every factual claim must be traceable to the provided excerpts.
        If the evidence is insufficient, say so explicitly rather than filling gaps."""

        return await self.call_llm(prompt, system_prompt, max_tokens=900)
