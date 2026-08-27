"""Technical analysis MCP tools - thin wrapper around app.tools.technical"""
from typing import Any, Dict

from app.services.company_service import CompanyService
from app.tools.technical import TechnicalAnalyzer

_company_service = CompanyService()


def register(server) -> None:
    @server.tool()
    async def calculate_technical_indicators(ticker: str) -> Dict[str, Any]:
        """Calculate technical indicators for a ticker: SMA(20/50/200), RSI(14),
        MACD, Bollinger Bands, ATR, and recent price-change percentages.
        """
        history = await _company_service.get_historical_data(ticker, period="1y")
        if history.empty:
            return {"ticker": ticker.upper(), "error": "No historical data available"}

        indicators = TechnicalAnalyzer.analyze_all(history)
        return {"ticker": ticker.upper(), **indicators}
