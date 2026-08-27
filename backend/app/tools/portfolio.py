"""Portfolio Optimization Tools"""
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns, risk_models

from app.models.portfolio import EfficientFrontierPoint, OptimizationResult

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """Portfolio optimization using PyPortfolioOpt"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def optimize_max_sharpe(
        self,
        returns_data: pd.DataFrame,
        risk_free_rate: float = 0.02,
        weight_bounds: Tuple[float, float] = (0, 1),
        constraints: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        Optimize portfolio for maximum Sharpe ratio
        
        Args:
            returns_data: DataFrame of historical returns
            risk_free_rate: Annual risk-free rate
            weight_bounds: Min/max weight bounds
            constraints: Additional constraints
        
        Returns:
            OptimizationResult
        """
        try:
            # Calculate expected returns and covariance
            mu = expected_returns.mean_historical_return(returns_data, returns_data=True)
            S = risk_models.sample_cov(returns_data, returns_data=True)
            
            # Create efficient frontier
            ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
            
            # Add constraints if provided
            if constraints:
                if constraints.get("max_weight"):
                    ef.add_constraint(lambda w: w <= constraints["max_weight"])
                if constraints.get("min_weight"):
                    ef.add_constraint(lambda w: w >= constraints["min_weight"])
                if constraints.get("sector_limits"):
                    # Sector limits would need sector data
                    pass
            
            # Optimize for max Sharpe
            ef.max_sharpe(risk_free_rate=risk_free_rate)
            
            # Get weights
            weights = ef.clean_weights()
            
            # Calculate metrics
            performance = ef.portfolio_performance(risk_free_rate=risk_free_rate)
            
            return OptimizationResult(
                recommended_weights=weights,
                expected_return=performance[0],
                expected_volatility=performance[1],
                expected_sharpe=performance[2],
                method="max_sharpe",
                constraints={
                    "weight_bounds": weight_bounds,
                    "risk_free_rate": risk_free_rate,
                },
                warnings=[],
            )
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return OptimizationResult(
                recommended_weights={},
                expected_return=0.0,
                expected_volatility=0.0,
                expected_sharpe=0.0,
                method="max_sharpe",
                constraints={},
                warnings=[str(e)],
            )
    
    def optimize_min_volatility(
        self,
        returns_data: pd.DataFrame,
        weight_bounds: Tuple[float, float] = (0, 1),
        constraints: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """Optimize portfolio for minimum volatility"""
        try:
            mu = expected_returns.mean_historical_return(returns_data, returns_data=True)
            S = risk_models.sample_cov(returns_data, returns_data=True)
            
            ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
            
            # Add constraints
            if constraints and constraints.get("max_weight"):
                ef.add_constraint(lambda w: w <= constraints["max_weight"])
            
            # Optimize for min volatility
            ef.min_volatility()
            weights = ef.clean_weights()
            performance = ef.portfolio_performance(risk_free_rate=0.02)
            
            return OptimizationResult(
                recommended_weights=weights,
                expected_return=performance[0],
                expected_volatility=performance[1],
                expected_sharpe=performance[2],
                method="min_volatility",
                constraints={
                    "weight_bounds": weight_bounds,
                },
                warnings=[],
            )
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return OptimizationResult(
                recommended_weights={},
                expected_return=0.0,
                expected_volatility=0.0,
                expected_sharpe=0.0,
                method="min_volatility",
                constraints={},
                warnings=[str(e)],
            )
    
    def optimize_efficient_frontier(
        self,
        returns_data: pd.DataFrame,
        target_return: Optional[float] = None,
        weight_bounds: Tuple[float, float] = (0, 1),
        num_points: int = 20
    ) -> List[EfficientFrontierPoint]:
        """
        Generate efficient frontier points
        
        Args:
            returns_data: DataFrame of historical returns
            target_return: Target return (optional)
            weight_bounds: Min/max weight bounds
            num_points: Number of points on frontier
        
        Returns:
            List of EfficientFrontierPoint
        """
        try:
            mu = expected_returns.mean_historical_return(returns_data, returns_data=True)
            S = risk_models.sample_cov(returns_data, returns_data=True)
            
            ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
            
            # Generate frontier points
            points = []
            
            if target_return:
                # Single point at target return
                weights = ef.efficient_return(target_return)
                performance = ef.portfolio_performance()
                points.append(
                    EfficientFrontierPoint(
                        return_rate=performance[0],
                        volatility=performance[1],
                        weights=weights,
                    )
                )
            else:
                # Generate multiple points
                min_ret = mu.min()
                max_ret = mu.max()
                returns_range = np.linspace(min_ret, max_ret, num_points)
                
                for ret in returns_range:
                    try:
                        weights = ef.efficient_return(ret)
                        perf = ef.portfolio_performance()
                        points.append(
                            EfficientFrontierPoint(
                                return_rate=perf[0],
                                volatility=perf[1],
                                weights=weights,
                                sharpe=(perf[0] - 0.02) / perf[1] if perf[1] > 0 else 0,
                            )
                        )
                    except Exception:
                        continue
            
            return points
            
        except Exception as e:
            self.logger.error(f"Efficient frontier generation failed: {e}")
            return []
    
    def calculate_diversification_ratio(
        self,
        weights: Dict[str, float],
        returns_data: pd.DataFrame
    ) -> float:
        """Calculate diversification ratio"""
        try:
            tickers = list(weights.keys())
            valid_tickers = [t for t in tickers if t in returns_data.columns]
            
            if not valid_tickers:
                return 1.0
            
            weights_array = np.array([weights[t] for t in valid_tickers])
            returns_subset = returns_data[valid_tickers]
            
            # Weighted average volatility
            avg_vol = np.average(returns_subset.std() * np.sqrt(252), weights=weights_array)
            
            # Portfolio volatility
            cov_matrix = returns_subset.cov().values
            portfolio_vol = np.sqrt(weights_array @ cov_matrix @ weights_array) * np.sqrt(252)
            
            if portfolio_vol == 0:
                return 1.0
            
            return avg_vol / portfolio_vol
            
        except Exception as e:
            self.logger.error(f"Diversification ratio calculation failed: {e}")
            return 1.0
    
    def compare_portfolios(
        self,
        current_weights: Dict[str, float],
        recommended_weights: Dict[str, float],
        returns_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compare current vs recommended portfolio
        
        Returns:
            Dict with comparison metrics
        """
        result = {}
        
        # Calculate metrics for both portfolios
        tickers = list(set(current_weights.keys()) | set(recommended_weights.keys()))
        valid_tickers = [t for t in tickers if t in returns_data.columns]
        
        if not valid_tickers:
            return {"error": "No valid tickers found"}
        
        returns_subset = returns_data[valid_tickers]
        
        # Helper function to calculate portfolio metrics
        def get_metrics(weights):
            w = np.array([weights.get(t, 0) for t in valid_tickers])
            if w.sum() == 0:
                return None
            
            w = w / w.sum()
            returns = returns_subset @ w
            annual_return = returns.mean() * 252
            annual_vol = returns.std() * np.sqrt(252)
            sharpe = (annual_return - 0.02) / annual_vol if annual_vol > 0 else 0
            
            return {
                "return": annual_return,
                "volatility": annual_vol,
                "sharpe": sharpe,
            }
        
        current_metrics = get_metrics(current_weights)
        recommended_metrics = get_metrics(recommended_weights)
        
        if current_metrics and recommended_metrics:
            result["current"] = current_metrics
            result["recommended"] = recommended_metrics
            result["improvement"] = {
                "return": recommended_metrics["return"] - current_metrics["return"],
                "volatility": recommended_metrics["volatility"] - current_metrics["volatility"],
                "sharpe": recommended_metrics["sharpe"] - current_metrics["sharpe"],
            }
            result["turnover"] = sum(
                abs(current_weights.get(t, 0) - recommended_weights.get(t, 0))
                for t in valid_tickers
            ) / 2
        
        return result