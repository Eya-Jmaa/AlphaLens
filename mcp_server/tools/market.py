"""Market data MCP tools - thin wrappers around app.services.company_service"""
from typing import Any, Dict

from app.services.company_service import CompanyService

_company_service = CompanyService()


def register(server) -> None:
    @server.tool()
    async def get_stock_price(ticker: str) -> Dict[str, Any]:
        """Get the current price and quote details for a stock ticker (yfinance,
        with Alpha Vantage fallback if configured)."""
        info = await _company_service.get_company_info(ticker)
        return {
            "ticker": info.get("ticker", ticker.upper()),
            "price": info.get("price"),
            "previous_close": info.get("previous_close"),
            "day_high": info.get("day_high"),
            "day_low": info.get("day_low"),
            "volume": info.get("volume"),
            "source": info.get("source"),
            "updated_at": info.get("updated_at"),
            "error": info.get("error"),
        }

    @server.tool()
    async def get_historical_prices(ticker: str, period: str = "6mo") -> Dict[str, Any]:
        """Get historical OHLCV price data for a ticker.

        Args:
            ticker: Stock ticker symbol, e.g. "AAPL".
            period: One of "1mo", "3mo", "6mo", "1y", "2y", "5y", "max".
        """
        history = await _company_service.get_historical_data(ticker, period=period)
        if history.empty:
            return {"ticker": ticker.upper(), "period": period, "error": "No historical data available"}

        records = history.reset_index().tail(120).to_dict("records")
        return {
            "ticker": ticker.upper(),
            "period": period,
            "points": len(history),
            # Trimmed to the most recent 120 rows to keep the response compact for an LLM caller.
            "recent": [
                {
                    "date": str(r.get("Date", r.get("index", "")))[:10],
                    "open": r.get("Open"),
                    "high": r.get("High"),
                    "low": r.get("Low"),
                    "close": r.get("Close"),
                    "volume": r.get("Volume"),
                }
                for r in records
            ],
        }

    @server.tool()
    async def get_company_profile(ticker: str) -> Dict[str, Any]:
        """Get company profile information: name, sector, industry, country, exchange."""
        info = await _company_service.get_company_info(ticker)
        return {
            "ticker": info.get("ticker", ticker.upper()),
            "name": info.get("name"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "error": info.get("error"),
        }

    @server.tool()
    async def get_financial_metrics(ticker: str) -> Dict[str, Any]:
        """Get fundamental financial metrics: market cap, P/E, EPS, margins, dividend yield, beta."""
        info = await _company_service.get_company_info(ticker)
        return {
            "ticker": info.get("ticker", ticker.upper()),
            "market_cap": info.get("market_cap"),
            "pe_ratio": info.get("pe_ratio"),
            "eps": info.get("eps"),
            "dividend_yield": info.get("dividend_yield"),
            "beta": info.get("beta"),
            "revenue": info.get("revenue"),
            "gross_margin": info.get("gross_margin"),
            "profit_margin": info.get("profit_margin"),
            "debt_to_equity": info.get("debt_to_equity"),
            "return_on_equity": info.get("return_on_equity"),
            "fifty_two_week_high": info.get("fifty_two_week_high"),
            "fifty_two_week_low": info.get("fifty_two_week_low"),
            "error": info.get("error"),
        }
