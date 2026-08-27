"""Shared ticker <-> company name lookup.

This is a small, fast-path convenience map, not the source of truth for
ticker validity. Any ticker not listed here still works end-to-end via the
supervisor's LLM-based extraction fallback (see app/agents/supervisor.py).
"""
from typing import Dict, List, Optional

KNOWN_COMPANIES: Dict[str, str] = {
    "AAPL": "Apple Inc.",
    "NVDA": "NVIDIA Corporation",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "META": "Meta Platforms Inc.",
    "AMD": "Advanced Micro Devices Inc.",
    "INTC": "Intel Corporation",
    "IBM": "International Business Machines",
    "NFLX": "Netflix Inc.",
    "ORCL": "Oracle Corporation",
    "CRM": "Salesforce Inc.",
    "AVGO": "Broadcom Inc.",
    "QCOM": "Qualcomm Inc.",
}

# A few tickers whose plain company name doesn't contain a substring match
# for the symbol itself (e.g. "NVIDIA" doesn't contain "NVDA"), used to widen
# the cheap keyword-matching pass before falling back to the LLM.
COMPANY_NAME_ALIASES: Dict[str, str] = {
    "nvidia": "NVDA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "tesla": "TSLA",
    "meta": "META",
    "facebook": "META",
    "amd": "AMD",
    "intel": "INTC",
    "netflix": "NFLX",
    "oracle": "ORCL",
    "salesforce": "CRM",
    "broadcom": "AVGO",
    "qualcomm": "QCOM",
}


def find_tickers_in_text(text: str) -> List[str]:
    """Cheap keyword-based ticker extraction (no LLM call)."""
    upper = text.upper()
    lower = text.lower()
    found: List[str] = []

    for ticker in KNOWN_COMPANIES:
        if ticker in upper.split() or f" {ticker} " in f" {upper} " or upper == ticker:
            found.append(ticker)

    for alias, ticker in COMPANY_NAME_ALIASES.items():
        if alias in lower and ticker not in found:
            found.append(ticker)

    return found


def search_companies(query: str) -> List[Dict[str, str]]:
    """Search known companies by ticker or name substring."""
    query_lower = query.lower()
    results = []
    for ticker, name in KNOWN_COMPANIES.items():
        if query_lower in ticker.lower() or query_lower in name.lower():
            results.append({"ticker": ticker, "name": name})
    return results


def company_name_for(ticker: str) -> Optional[str]:
    return KNOWN_COMPANIES.get(ticker.upper())
