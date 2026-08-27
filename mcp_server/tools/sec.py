"""SEC filing MCP tools - thin wrappers around app.services.sec_service / sec_rag_service"""
import logging
from typing import Any, Dict, List, Optional

from app.services.sec_service import SECService

logger = logging.getLogger(__name__)

_sec_service = SECService()
_rag_service = None  # lazy: loads an embedding model + connects to Qdrant on first use


def _get_rag_service():
    global _rag_service
    if _rag_service is None:
        from app.services.sec_rag_service import SECRagService

        _rag_service = SECRagService(sec_service=_sec_service)
    return _rag_service


def register(server) -> None:
    @server.tool()
    async def get_sec_filings(ticker: str, filing_types: Optional[List[str]] = None, limit: int = 5) -> Dict[str, Any]:
        """List a company's recent SEC EDGAR filings (10-K, 10-Q, 8-K by default).

        Args:
            ticker: Stock ticker symbol, e.g. "AAPL".
            filing_types: Filing types to include, e.g. ["10-K", "10-Q"]. Defaults to 10-K/10-Q/8-K.
            limit: Maximum number of filings to return.
        """
        filings = await _sec_service.get_recent_filings(ticker, limit=limit, filing_types=filing_types)
        return {"ticker": ticker.upper(), "filings": filings}

    @server.tool()
    async def search_sec_documents(ticker: str, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Answer a question about a company's SEC filings using retrieval-augmented
        generation over its ingested 10-K/10-Q text (fetches + indexes the filing on
        first use for that ticker). Every claim is grounded in retrieved excerpts.

        Args:
            ticker: Stock ticker symbol, e.g. "TSLA".
            question: The question to answer from the filing, e.g. "What are the main risk factors?"
            top_k: Number of filing excerpts to retrieve.
        """
        try:
            rag = _get_rag_service()
        except Exception as e:
            logger.error(f"SEC RAG unavailable: {e}")
            return {"ticker": ticker.upper(), "error": f"SEC document search is unavailable: {e}"}

        result = await rag.answer(ticker, question, top_k=top_k)
        return {
            "ticker": ticker.upper(),
            "question": question,
            "ingestion_status": result["ingestion_status"],
            "is_live_edgar_data": any(r["metadata"].get("source") == "sec_edgar" for r in result["results"]),
            "sources": [
                {
                    "filing_type": r["metadata"].get("filing_type"),
                    "filing_date": r["metadata"].get("filing_date"),
                    "section": r["metadata"].get("section"),
                }
                for r in result["results"]
            ],
            "context": result["context"],
        }
