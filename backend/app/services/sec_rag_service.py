"""SEC Filing RAG orchestration: fetch -> chunk -> embed -> store -> retrieve"""
import logging
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.rag.chunking import DocumentChunker
from app.rag.embeddings import EmbeddingService
from app.rag.retriever import RetrieverService
from app.rag.vector_store import VectorStoreService
from app.services.cache_service import CacheService
from app.services.sec_service import SECService

logger = logging.getLogger(__name__)

INGESTION_TTL_SECONDS = 60 * 60 * 12  # re-check for new filings twice a day


class SECRagService:
    """Ties SEC EDGAR fetching together with the chunking/embedding/vector-store RAG pipeline."""

    def __init__(
        self,
        sec_service: Optional[SECService] = None,
        cache_service: Optional[CacheService] = None,
    ):
        self.sec_service = sec_service or SECService()
        self.cache = cache_service or CacheService()
        self.chunker = DocumentChunker()
        self.embeddings = EmbeddingService()
        self.vector_store = VectorStoreService(self.embeddings, url=settings.QDRANT_URL)
        self.retriever = RetrieverService(self.vector_store, self.embeddings)

    async def ensure_ingested(
        self,
        ticker: str,
        filing_types: Optional[List[str]] = None,
        limit: int = 2,
    ) -> Dict[str, Any]:
        """Fetch + chunk + embed the most recent filings for a ticker, unless already done recently."""
        ticker = ticker.upper()
        cache_key = self.cache.cache_key("sec_ingested", ticker, ",".join(filing_types or ["10-K", "10-Q"]))

        cached = await self.cache.get(cache_key)
        if cached is not None:
            logger.info(f"SEC ingestion status for {ticker} served from cache ({len(cached)} filing(s))")
            return {"status": "cached", "filings": cached}

        logger.info(f"Fetching live SEC EDGAR filings for {ticker}...")
        filings = await self.sec_service.get_recent_filings(
            ticker, limit=limit, filing_types=filing_types
        )
        if not filings:
            logger.info(f"No live SEC EDGAR filings found for {ticker}; will fall back to any bundled sample data")
            return {"status": "no_filings", "filings": []}

        ingested: List[Dict[str, Any]] = []
        for filing in filings:
            filing_url = filing.get("url")
            if not filing_url:
                continue

            text = await self.sec_service.get_filing_text(filing_url)
            if not text:
                continue

            metadata = {
                "ticker": ticker,
                "filing_type": filing.get("filing_type"),
                "filing_date": filing.get("filing_date"),
                "accession_number": filing.get("accession_number"),
                "source_url": filing_url,
                "source": "sec_edgar",
                "doc_id": f"{ticker}_{filing.get('accession_number') or filing.get('filing_date') or 'unknown'}",
            }

            chunks = self.chunker.chunk_filing(text, metadata)
            if chunks:
                added = self.vector_store.add_documents(chunks)
                logger.info(f"Ingested {added} chunks for {ticker} {metadata['filing_type']}")
                ingested.append(metadata)

        # Cache the outcome even if empty, so a filing with no parseable text
        # doesn't get re-fetched on every query.
        await self.cache.set(cache_key, ingested, ttl=INGESTION_TTL_SECONDS)

        return {"status": "ingested" if ingested else "no_content", "filings": ingested}

    async def answer(self, ticker: str, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Ensure filings are ingested, then retrieve the most relevant chunks for a question."""
        ingestion = await self.ensure_ingested(ticker)
        retrieval = self.retriever.retrieve_for_question(question, ticker, top_k=top_k)

        return {
            "ingestion_status": ingestion["status"],
            "filings": ingestion["filings"],
            "results": retrieval["results"],
            "context": retrieval["context"],
        }
