"""Risk analysis MCP tools - thin wrapper around app.services.risk_service"""
from typing import Any, Dict, List

from app.services.risk_service import RiskService

_risk_service = RiskService()


def register(server) -> None:
    @server.tool()
    async def calculate_risk(tickers: List[str], weights: List[float]) -> Dict[str, Any]:
        """Calculate portfolio risk metrics: annualized volatility, Sharpe ratio,
        max drawdown, VaR/CVaR (95%/99%), correlation matrix, and concentration
        (Herfindahl index / effective number of holdings).

        Args:
            tickers: List of stock tickers, e.g. ["AAPL", "MSFT", "NVDA"].
            weights: Portfolio weight for each ticker, in the same order, summing to ~1.0.
        """
        if len(tickers) != len(weights):
            return {"error": "tickers and weights must be the same length"}

        weight_map = dict(zip(tickers, weights))
        returns_data = await _risk_service.get_historical_returns(tickers)
        if returns_data.empty:
            return {"error": "No historical price data available for these tickers"}

        metrics = await _risk_service.calculate_risk_metrics(weights=weight_map, returns_data=returns_data)
        return {"tickers": tickers, "weights": weight_map, "metrics": metrics.model_dump()}
