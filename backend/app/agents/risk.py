"""Risk Analysis Agent"""
import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.agents.base import BaseAgent
from app.models.portfolio import Portfolio, Position
from app.services.market_service import MarketService
from app.services.risk_service import RiskService
from app.tools.portfolio import PortfolioOptimizer

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """Risk Analysis Agent"""
    
    def __init__(
        self,
        llm_provider,
        risk_service: RiskService = None,
        market_service: MarketService = None,
        optimizer: PortfolioOptimizer = None,
    ):
        super().__init__("RiskAnalysis", llm_provider)
        self.risk_service = risk_service or RiskService(market_service)
        self.optimizer = optimizer or PortfolioOptimizer()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process risk analysis for tickers in state"""
        tickers = state.get("tickers", [])
        self.logger.info(f"Analyzing risk for: {tickers}")

        if not tickers:
            return {"errors": ["No tickers for risk analysis"]}

        try:
            # Get historical returns
            returns_data = await self.risk_service.get_historical_returns(tickers)

            if returns_data.empty:
                return {"warnings": ["No historical data available for risk analysis"]}

            # Calculate individual stock risks
            stock_risks = {}
            
            for ticker in tickers:
                if ticker not in returns_data.columns:
                    continue
                
                stock_returns = returns_data[ticker]
                
                volatility = stock_returns.std() * np.sqrt(252)
                var_95 = np.percentile(stock_returns, 5) * np.sqrt(252)
                max_drawdown = self._calculate_max_drawdown(stock_returns)
                beta = await self.risk_service.calculate_beta(ticker)
                
                stock_risks[ticker] = {
                    "volatility": float(volatility),
                    "var_95": float(var_95),
                    "max_drawdown": float(max_drawdown),
                    "beta": float(beta),
                }
            
            # Create equal-weighted portfolio
            equal_weights = {t: 1 / len(tickers) for t in tickers if t in returns_data.columns}
            if not equal_weights:
                return {"warnings": ["No overlapping historical data across tickers for risk analysis"]}

            portfolio = Portfolio(
                name="Analysis Portfolio",
                positions=[
                    Position(ticker=t, weight=w)
                    for t, w in equal_weights.items()
                ],
            )

            risk_metrics = await self.risk_service.calculate_risk_metrics(
                weights=equal_weights,
                returns_data=returns_data,
            )

            simulation = await self.risk_service.monte_carlo_simulation(
                portfolio=portfolio,
                num_simulations=500,
            )

            llm_analysis = await self._analyze_risks(
                tickers=tickers,
                stock_risks=stock_risks,
                portfolio_metrics=risk_metrics,
                simulation=simulation,
            )

            self.logger.info("Risk analysis completed")

            return {
                "risk_analysis_results": {
                    "stock_risks": stock_risks,
                    "portfolio_metrics": risk_metrics.model_dump(),
                    "simulation": simulation,
                    "llm_analysis": llm_analysis,
                    "tickers": tickers,
                }
            }

        except Exception as e:
            self.logger.error(f"Risk analysis failed: {e}")
            return {"errors": [f"Risk analysis failed: {str(e)}"]}
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min() if not drawdown.empty else 0.0
    
    async def _analyze_risks(
        self,
        tickers: List[str],
        stock_risks: Dict[str, Dict],
        portfolio_metrics: Any,
        simulation: Dict,
    ) -> str:
        """Generate risk analysis using LLM"""
        
        stock_risk_text = "\n".join([
            f"""
            {ticker}:
            - Volatility: {data['volatility']:.2%}
            - VaR 95%: {data['var_95']:.2%}
            - Max Drawdown: {data['max_drawdown']:.2%}
            - Beta: {data['beta']:.2f}
            """
            for ticker, data in stock_risks.items()
        ])
        
        prompt = f"""
        Analyze the risk profile for the following stocks: {', '.join(tickers)}
        
        INDIVIDUAL STOCK RISKS:
        {stock_risk_text}
        
        PORTFOLIO RISK METRICS:
        - Portfolio Volatility: {portfolio_metrics.volatility:.2%}
        - Sharpe Ratio: {portfolio_metrics.sharpe_ratio:.2f}
        - Max Drawdown: {portfolio_metrics.max_drawdown:.2%}
        - VaR 95%: {portfolio_metrics.var_95:.2%}
        - Effective Number of Holdings: {portfolio_metrics.effective_number:.1f}
        
        MONTE CARLO SIMULATION (500 scenarios):
        - Initial Value: ${simulation.get('initial_value', 0):.2f}
        - 5th Percentile: ${simulation.get('final_value_percentiles', {}).get('5th', 0):.2f}
        - 50th Percentile: ${simulation.get('final_value_percentiles', {}).get('50th', 0):.2f}
        - 95th Percentile: ${simulation.get('final_value_percentiles', {}).get('95th', 0):.2f}
        
        Based on this risk data, provide:
        1. Overall risk assessment for the portfolio
        2. Key risk drivers (which stocks contribute most to risk)
        3. Diversification assessment
        4. Potential risk mitigation strategies
        5. Recommended risk management actions
        
        Be specific and reference the data provided. Write in 4-6 short plain-text paragraphs -
        no markdown headers, bold/asterisks, tables, bullet lists, or LaTeX/formulas. This is a
        prose summary shown directly in a UI card, not a formatted document.
        """

        system_prompt = """You are a risk management expert. Provide objective, data-driven risk analysis
        as plain prose (no markdown, tables, or formulas - this text is rendered as-is in a UI card).
        Focus on quantifiable risks and practical risk management strategies."""

        response = await self.call_llm(prompt, system_prompt, max_tokens=900)
        return response