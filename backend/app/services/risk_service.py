"""Risk Calculation Service"""
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd  # Add this if missing

from app.models.portfolio import Portfolio, RiskMetrics
from app.services.market_service import MarketService

logger = logging.getLogger(__name__)


class RiskService:
    """Service for calculating risk metrics"""
    
    def __init__(self, market_service: Optional[MarketService] = None):
        self.market = market_service or MarketService()
    
    async def calculate_risk_metrics(
        self,
        weights: Dict[str, float],
        returns_data: pd.DataFrame,
        risk_free_rate: float = 0.02
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for a portfolio
        
        Args:
            weights: Dictionary of ticker -> weight
            returns_data: DataFrame of historical returns
            risk_free_rate: Annual risk-free rate
        
        Returns:
            RiskMetrics object
        """
        # Ensure weights sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        # Filter returns for assets in portfolio
        tickers = list(weights.keys())
        available_tickers = [t for t in tickers if t in returns_data.columns]
        
        if not available_tickers:
            logger.warning("No available tickers for risk calculation")
            return self._empty_risk_metrics()
        
        # Get returns for available tickers
        portfolio_returns = returns_data[available_tickers]
        weights_array = np.array([weights[t] for t in available_tickers])
        
        # Calculate portfolio returns
        portfolio_series = portfolio_returns.dot(weights_array)
        
        # Annualize
        annual_return = portfolio_series.mean() * 252
        annual_volatility = portfolio_series.std() * np.sqrt(252)
        
        # Drawdowns
        cumulative = (1 + portfolio_series).cumprod()
        running_max = cumulative.expanding().max()
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = drawdowns.min()
        avg_drawdown = drawdowns.mean()
        
        # VaR (Historical)
        var_95 = np.percentile(portfolio_series, 5) * np.sqrt(252)
        var_99 = np.percentile(portfolio_series, 1) * np.sqrt(252)
        cvar_95 = portfolio_series[portfolio_series <= np.percentile(portfolio_series, 5)].mean() * np.sqrt(252)
        cvar_99 = portfolio_series[portfolio_series <= np.percentile(portfolio_series, 1)].mean() * np.sqrt(252)
        
        # Ratios
        excess_returns = portfolio_series - risk_free_rate / 252
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
        
        # Sortino (downside risk)
        downside_returns = excess_returns[excess_returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else annual_volatility
        sortino_ratio = (annual_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
        
        # Calmar
        calmar_ratio = (annual_return - risk_free_rate) / abs(max_drawdown) if max_drawdown < 0 else 0
        
        # Correlation matrix
        correlation_matrix = portfolio_returns.corr().values.tolist()
        
        # Concentration (Herfindahl-Hirschman Index)
        herfindahl = sum(w ** 2 for w in weights_array)
        effective_number = 1 / herfindahl if herfindahl > 0 else 0
        
        # Risk contributions (marginal contribution to risk)
        risk_contributions = self._calculate_risk_contributions(
            portfolio_returns, weights_array, annual_volatility
        )
        
        return RiskMetrics(
            volatility=annual_volatility,
            downside_volatility=downside_volatility,
            max_drawdown=max_drawdown,
            avg_drawdown=avg_drawdown,
            drawdown_duration=None,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            correlation_matrix=correlation_matrix,
            herfindahl_index=herfindahl,
            effective_number=effective_number,
            risk_contributions=risk_contributions,
        )
    
    def _calculate_risk_contributions(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_volatility: float
    ) -> Dict[str, float]:
        """Calculate risk contributions of each asset"""
        if returns.empty or portfolio_volatility == 0:
            return {}
        
        # Covariance matrix
        cov_matrix = returns.cov().values
        
        # Marginal risk contributions
        marginal_contrib = cov_matrix @ weights / portfolio_volatility
        
        # Total risk contributions
        risk_contrib = weights * marginal_contrib / portfolio_volatility
        
        tickers = returns.columns.tolist()
        return {ticker: float(risk_contrib[i]) for i, ticker in enumerate(tickers)}
    
    def _empty_risk_metrics(self) -> RiskMetrics:
        """Return empty risk metrics"""
        return RiskMetrics(
            volatility=0.0,
            max_drawdown=0.0,
            var_95=0.0,
            sharpe_ratio=0.0,
            herfindahl_index=0.0,
            effective_number=0.0,
            downside_volatility=None,
            avg_drawdown=None,
            drawdown_duration=None,
            var_99=None,
            cvar_95=None,
            cvar_99=None,
            sortino_ratio=None,
            calmar_ratio=None,
            correlation_matrix=None,
            risk_contributions=None,
        )
    
    async def get_historical_returns(
        self,
        tickers: List[str],
        period: str = "1y"
    ) -> pd.DataFrame:
        """Get historical returns for a list of tickers"""
        returns_dict = {}
        
        for ticker in tickers:
            try:
                # Get historical data
                history = await self.market.get_historical_data(ticker, period=period)
                
                if not history.empty:
                    # Calculate daily returns
                    returns = history['Close'].pct_change().dropna()
                    returns_dict[ticker] = returns
                    
            except Exception as e:
                logger.error(f"Failed to get returns for {ticker}: {e}")
        
        if not returns_dict:
            return pd.DataFrame()
        
        # Align data by date
        df = pd.DataFrame(returns_dict)
        df = df.dropna(axis=1, how='all')
        df = df.fillna(0)
        
        return df
    
    async def monte_carlo_simulation(
        self,
        portfolio: Portfolio,
        num_simulations: int = 1000,
        num_days: int = 252,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for a portfolio
        
        Returns:
            Dict with simulation results
        """
        weights = portfolio.get_weights_dict()
        tickers = list(weights.keys())
        
        if not tickers:
            return {"error": "No assets in portfolio"}
        
        # Get historical returns
        returns_data = await self.get_historical_returns(tickers)
        if returns_data.empty:
            return {"error": "No historical data available"}
        
        # Calculate mean returns and covariance
        mean_returns = returns_data.mean().values
        cov_matrix = returns_data.cov().values
        
        # Run simulation
        results = []
        portfolio_values = []
        
        for _ in range(num_simulations):
            # Generate random returns using Cholesky decomposition
            random_returns = np.random.multivariate_normal(
                mean_returns, cov_matrix, num_days
            )
            
            # Calculate portfolio returns
            portfolio_returns = random_returns @ np.array(list(weights.values()))
            
            # Calculate final portfolio value
            initial_value = portfolio.total_value
            final_value = initial_value * (1 + portfolio_returns).prod()
            portfolio_values.append(final_value)
            
            # Calculate metrics
            annual_return = portfolio_returns.mean() * 252
            annual_volatility = portfolio_returns.std() * np.sqrt(252)
            
            # Calculate VaR
            var_95 = np.percentile(portfolio_returns, (1 - confidence_level) * 100) * np.sqrt(252)
            
            results.append({
                "final_value": final_value,
                "return": annual_return,
                "volatility": annual_volatility,
                "var_95": var_95,
            })
        
        # Calculate percentiles
        final_values = np.array(portfolio_values)
        var_value = np.percentile(final_values, (1 - confidence_level) * 100)
        
        return {
            "simulations": num_simulations,
            "days": num_days,
            "confidence_level": confidence_level,
            "initial_value": portfolio.total_value,
            "final_value_percentiles": {
                "5th": float(np.percentile(final_values, 5)),
                "25th": float(np.percentile(final_values, 25)),
                "50th": float(np.percentile(final_values, 50)),
                "75th": float(np.percentile(final_values, 75)),
                "95th": float(np.percentile(final_values, 95)),
            },
            "var_value": float(var_value),
            "var_percent": float((var_value - portfolio.total_value) / portfolio.total_value * 100),
            "mean_final_value": float(final_values.mean()),
            "std_final_value": float(final_values.std()),
            "results": results[:10],  # Sample of first 10 simulations
        }
    
    async def calculate_beta(
        self,
        ticker: str,
        market_ticker: str = "SPY",
        period: str = "1y"
    ) -> float:
        """Calculate beta for a stock against market"""
        try:
            # Get returns
            returns_dict = {}
            
            for t in [ticker, market_ticker]:
                history = await self.market.get_historical_data(t, period=period)
                if not history.empty:
                    returns_dict[t] = history['Close'].pct_change().dropna()
            
            if len(returns_dict) < 2:
                return 1.0
            
            # Align data
            df = pd.DataFrame(returns_dict)
            df = df.dropna()
            
            if df.empty:
                return 1.0
            
            # Calculate beta
            covariance = df[ticker].cov(df[market_ticker])
            variance = df[market_ticker].var()
            
            if variance == 0:
                return 1.0
            
            return covariance / variance
            
        except Exception as e:
            logger.error(f"Beta calculation failed for {ticker}: {e}")
            return 1.0