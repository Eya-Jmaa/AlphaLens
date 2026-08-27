"""Pre-warm the SEC filing RAG cache for a list of tickers.

Fetches each ticker's recent 10-K/10-Q from SEC EDGAR, chunks and embeds them,
and stores them in Qdrant via the same SECRagService the SECAgent uses at
query time - this just lets you do that ahead of a demo instead of eating the
ingestion latency on the first live query.

Usage (from backend/, with the venv active):
    python scripts/ingest_sec.py AAPL MSFT NVDA
    python scripts/ingest_sec.py --filing-types 10-K TSLA
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.sec_rag_service import SECRagService  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finagent.ingest_sec")


async def ingest(tickers: list[str], filing_types: list[str] | None) -> None:
    service = SECRagService()
    for ticker in tickers:
        logger.info(f"Ingesting {ticker}...")
        result = await service.ensure_ingested(ticker, filing_types=filing_types)
        logger.info(f"{ticker}: {result['status']} ({len(result['filings'])} filing(s))")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to ingest, e.g. AAPL MSFT NVDA")
    parser.add_argument("--filing-types", nargs="+", default=None, help="e.g. --filing-types 10-K 10-Q")
    args = parser.parse_args()

    asyncio.run(ingest([t.upper() for t in args.tickers], args.filing_types))


if __name__ == "__main__":
    main()
