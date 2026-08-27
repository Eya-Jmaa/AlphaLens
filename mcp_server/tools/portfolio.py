"""Portfolio MCP tools - thin wrappers around app.services.risk_service / app.tools.portfolio"""
from typing import Any, Dict, List, Optional

from app.models.portfolio import Portfolio, Position
from app.services.risk_service import RiskService
from app.tools.portfolio import PortfolioOptimizer

_risk_service = RiskService()
_optimizer = PortfolioOptimizer()


def register(server) -> None:
    @server.tool()
    async def calculate_portfolio_metrics(
        tickers: List[str], weights: List[float], initial_value: float = 10000.0
    ) -> Dict[str, Any]:
        """Run a Monte Carlo simulation (500 scenarios, 1yr horizon) for a portfolio,
        returning projected value percentiles and simulated Value-at-Risk in dollar terms.

        Args:
            tickers: List of stock tickers, e.g. ["AAPL", "MSFT", "NVDA"].
            weights: Portfolio weight for each ticker, in the same order, summing to ~1.0.
            initial_value: Starting portfolio value in dollars (default $10,000).
        """
        if len(tickers) != len(weights):
            return {"error": "tickers and weights must be the same length"}

        portfolio = Portfolio(
            positions=[Position(ticker=t, weight=w, value=initial_value * w) for t, w in zip(tickers, weights)],
        )
        simulation = await _risk_service.monte_carlo_simulation(portfolio=portfolio, num_simulations=500)
        return {"tickers": tickers, "weights": dict(zip(tickers, weights)), "simulation": simulation}

    @server.tool()
    async def optimize_portfolio(
        tickers: List[str],
        method: str = "max_sharpe",
        max_weight: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Recommend portfolio weights across a set of tickers for maximum Sharpe
        ratio or minimum volatility, using 1 year of historical returns.

        Args:
            tickers: List of stock tickers to allocate across, e.g. ["AAPL", "MSFT", "NVDA"].
            method: "max_sharpe" or "min_volatility".
            max_weight: Optional cap on any single position's weight (0-1).
        """
        if len(tickers) < 2:
            return {"error": "Provide at least two tickers to optimize across"}

        returns_data = await _risk_service.get_historical_returns(tickers)
        if returns_data.empty or len(returns_data.columns) < 2:
            return {"error": "Not enough overlapping historical data to optimize this portfolio"}

        constraints = {"max_weight": max_weight} if max_weight else None
        if method == "min_volatility":
            result = _optimizer.optimize_min_volatility(returns_data, constraints=constraints)
        else:
            result = _optimizer.optimize_max_sharpe(returns_data, constraints=constraints)

        return result.model_dump()
