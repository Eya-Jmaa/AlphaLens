"""Shared evidence-dossier assembly.

Extracted from FinalAnalystAgent so it, BullAgent, BearAgent, and JudgeAgent all
synthesize from exactly one evidence-formatting implementation (and one
token/context budget), rather than four slightly-different copies.
"""
import json
from typing import Any, Dict, List, Tuple

# Each specialized agent already produced its own LLM prose; re-including all of
# it verbatim in a downstream prompt is what blows the context/TPM budget, so
# every section below is capped to a fixed character budget.
SECTION_CHAR_BUDGET = 700


def truncate(text: str) -> str:
    text = text or ""
    if len(text) <= SECTION_CHAR_BUDGET:
        return text
    return text[:SECTION_CHAR_BUDGET].rsplit(" ", 1)[0] + "..."


def format_stock_analysis(results: List[Dict[str, Any]]) -> str:
    formatted = []
    for result in results:
        if not isinstance(result, dict):
            continue
        ticker = result.get("ticker", "Unknown")
        data = result.get("company_data", {})
        analysis = result.get("analysis", {})
        analysis_text = analysis if isinstance(analysis, str) else json.dumps(analysis)
        formatted.append(
            f"[{ticker}] {data.get('name', 'N/A')} | Sector: {data.get('sector', 'N/A')} | "
            f"Market Cap: {data.get('market_cap', 'N/A')} | P/E: {data.get('pe_ratio', 'N/A')}\n"
            f"Analysis: {truncate(analysis_text)}"
        )
    return "\n\n".join(formatted) if formatted else "No fundamental data available."


def format_technical(technical_results: Dict[str, Any]) -> str:
    formatted = []
    for ticker, tech in technical_results.items():
        if not tech or tech.get("error"):
            continue
        formatted.append(
            f"[{ticker}] Price: {tech.get('latest_price')} | SMA20/50/200: "
            f"{tech.get('sma_20')}/{tech.get('sma_50')}/{tech.get('sma_200')} | "
            f"RSI: {tech.get('rsi')} | 1d/1w/1m change: "
            f"{tech.get('price_change', {}).get('1d')}%/"
            f"{tech.get('price_change', {}).get('1w')}%/"
            f"{tech.get('price_change', {}).get('1m')}%"
        )
    return "\n".join(formatted) if formatted else "No technical data available."


def format_news(results: List[Dict[str, Any]]) -> str:
    formatted = []
    for result in results:
        ticker = result.get("ticker", "Unknown")
        summary = result.get("sentiment_summary", {})
        llm_analysis = result.get("llm_analysis", {})
        analysis_text = llm_analysis.get("analysis", "") if isinstance(llm_analysis, dict) else str(llm_analysis)
        formatted.append(
            f"[{ticker}] Sentiment: {summary.get('overall_sentiment', 'neutral')} "
            f"(score {summary.get('average_score', 0):.2f}, {summary.get('total_articles', 0)} articles)\n"
            f"{truncate(analysis_text)}"
        )
    return "\n\n".join(formatted) if formatted else "No news data available."


def format_risk(risk_results: Dict[str, Any]) -> str:
    metrics = risk_results.get("portfolio_metrics", {})
    stock_risks = risk_results.get("stock_risks", {})
    lines = [
        f"Portfolio volatility: {metrics.get('volatility', 'N/A')}, "
        f"Sharpe: {metrics.get('sharpe_ratio', 'N/A')}, "
        f"Max drawdown: {metrics.get('max_drawdown', 'N/A')}, "
        f"VaR95: {metrics.get('var_95', 'N/A')}",
    ]
    for ticker, r in stock_risks.items():
        lines.append(
            f"[{ticker}] volatility={r.get('volatility')}, beta={r.get('beta')}, "
            f"max_drawdown={r.get('max_drawdown')}"
        )
    llm_analysis = risk_results.get("llm_analysis")
    if llm_analysis:
        lines.append(truncate(str(llm_analysis)))
    return "\n".join(lines)


def format_sec(results: List[Dict[str, Any]]) -> str:
    formatted = []
    for result in results:
        ticker = result.get("ticker", "Unknown")
        if result.get("status") != "ok":
            formatted.append(f"[{ticker}] {result.get('message', 'No SEC evidence available.')}")
            continue
        sources = result.get("sources", [])
        source_str = "; ".join(f"{s.get('filing_type')} ({s.get('filing_date')})" for s in sources)
        formatted.append(f"[{ticker}] Sources: {source_str}\n{truncate(result.get('analysis', ''))}")
    return "\n\n".join(formatted) if formatted else "No SEC filing evidence available."


def build_evidence_dossier(state: Dict[str, Any]) -> Tuple[str, bool]:
    """Combine every populated agent result into one evidence block for the LLM."""
    parts: List[str] = []
    has_any = False

    stock_results = state.get("stock_analysis_results", [])
    if stock_results:
        has_any = True
        parts.append("=== FUNDAMENTAL & MARKET DATA ===\n" + format_stock_analysis(stock_results))

    technical_results = state.get("technical_analysis_results", {})
    if technical_results:
        has_any = True
        parts.append("=== TECHNICAL INDICATORS ===\n" + format_technical(technical_results))

    news_results = state.get("news_analysis_results", [])
    if news_results:
        has_any = True
        parts.append("=== NEWS & SENTIMENT ===\n" + format_news(news_results))

    risk_results = state.get("risk_analysis_results", {})
    if risk_results:
        has_any = True
        parts.append("=== RISK ANALYSIS ===\n" + format_risk(risk_results))

    sec_results = state.get("sec_analysis_results", [])
    if sec_results:
        has_any = True
        parts.append("=== SEC FILING EVIDENCE ===\n" + format_sec(sec_results))

    return ("\n\n".join(parts) if parts else "No agent data available."), has_any
