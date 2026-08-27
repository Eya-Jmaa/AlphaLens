"""Financial Calculations"""
import logging
from typing import Dict

import numpy as np  # Add this import
import pandas as pd

logger = logging.getLogger(__name__)


class FinancialCalculator:
    """Financial calculations and ratios"""
    
    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe Ratio"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0
        
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)    
    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sortino Ratio (downside risk only)"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        return excess_returns.mean() / downside_returns.std() * np.sqrt(252)
    
    @staticmethod
    def calculate_calmar_ratio(
        returns: pd.Series,
        max_drawdown: float
    ) -> float:
        """Calculate Calmar Ratio"""
        if max_drawdown == 0:
            return 0.0
        
        annual_return = returns.mean() * 252
        return annual_return / abs(max_drawdown)
    
    @staticmethod
    def calculate_max_drawdown(returns: pd.Series) -> float:
        """Calculate Maximum Drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    @staticmethod
    def calculate_var(
        returns: pd.Series,
        confidence_level: float = 0.95,
        horizon_days: int = 1
    ) -> Dict[str, float]:
        """Calculate Value at Risk"""
        if len(returns) < 10:
            return {"var": 0.0, "cvar": 0.0}
        
        # Historical VaR
        var = np.percentile(returns, (1 - confidence_level) * 100)
        
        # Conditional VaR (Expected Shortfall)
        cvar = returns[returns <= var].mean()
        
        # Scale to horizon
        var_scaled = var * np.sqrt(horizon_days)
        cvar_scaled = cvar * np.sqrt(horizon_days)
        
        return {
            "var": float(var_scaled),
            "cvar": float(cvar_scaled),
            "confidence": confidence_level,
            "horizon_days": horizon_days,
        }
    
    @staticmethod
    def calculate_beta(
        stock_returns: pd.Series,
        market_returns: pd.Series
    ) -> float:
        """Calculate Beta"""
        if len(stock_returns) < 10 or len(market_returns) < 10:
            return 1.0
        
        covariance = stock_returns.cov(market_returns)
        variance = market_returns.var()
        
        if variance == 0:
            return 1.0
        
        return covariance / variance
    
    @staticmethod
    def calculate_correlation_matrix(
        returns_dict: Dict[str, pd.Series]
    ) -> pd.DataFrame:
        """Calculate correlation matrix for multiple assets"""
        df = pd.DataFrame(returns_dict)
        return df.corr()
    
    @staticmethod
    def calculate_rolling_volatility(
        returns: pd.Series,
        window: int = 21
    ) -> pd.Series:
        """Calculate rolling volatility"""
        return returns.rolling(window=window).std() * np.sqrt(252)
    
    @staticmethod
    def calculate_expected_return(
        returns: pd.Series,
        method: str = "historical"
    ) -> float:
        """Calculate expected return"""
        if method == "historical":
            return returns.mean() * 252
        elif method == "ewma":
            # Exponentially weighted
            weights = np.exp(np.linspace(-1, 0, len(returns)))
            weights /= weights.sum()
            return (returns * weights).sum() * 252
        else:
            return returns.mean() * 252