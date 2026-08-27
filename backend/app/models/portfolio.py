"""Portfolio Models"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Single portfolio position"""
    ticker: str
    weight: float = Field(ge=0, le=1, description="Portfolio weight (0-1)")
    shares: Optional[float] = None
    price: Optional[float] = None
    value: Optional[float] = None


class Portfolio(BaseModel):
    """Portfolio definition"""
    name: str = "My Portfolio"
    positions: List[Position]
    cash: float = 0.0
    
    @property
    def total_value(self) -> float:
        """Total portfolio value"""
        return sum(p.value or 0 for p in self.positions) + self.cash
    
    @property
    def tickers(self) -> List[str]:
        """List of tickers in portfolio"""
        return [p.ticker for p in self.positions if p.weight > 0]
    
    def get_weights_dict(self) -> Dict[str, float]:
        """Get weights as dictionary"""
        return {p.ticker: p.weight for p in self.positions if p.weight > 0}


class RiskMetrics(BaseModel):
    """Risk metrics for a portfolio"""
    # Volatility metrics
    volatility: float = Field(description="Annualized volatility")
    downside_volatility: Optional[float] = None
    
    # Drawdown metrics
    max_drawdown: float = Field(description="Maximum drawdown")
    avg_drawdown: Optional[float] = None
    drawdown_duration: Optional[float] = None
    
    # VaR metrics
    var_95: float = Field(description="95% Value at Risk")
    var_99: Optional[float] = None
    cvar_95: Optional[float] = Field(description="95% Conditional VaR")
    cvar_99: Optional[float] = None
    
    # Ratio metrics
    sharpe_ratio: float = Field(description="Sharpe ratio")
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    
    # Correlation
    correlation_matrix: Optional[List[List[float]]] = None
    
    # Concentration
    herfindahl_index: float = Field(description="Concentration measure (0-1)")
    effective_number: float = Field(description="Effective number of holdings")
    
    # Risk contributions
    risk_contributions: Optional[Dict[str, float]] = None


class OptimizationResult(BaseModel):
    """Portfolio optimization result"""
    # Recommended weights
    recommended_weights: Dict[str, float]
    
    # Expected metrics
    expected_return: float
    expected_volatility: float
    expected_sharpe: float
    
    # Comparison with current
    current_weights: Optional[Dict[str, float]] = None
    current_return: Optional[float] = None
    current_volatility: Optional[float] = None
    current_sharpe: Optional[float] = None
    
    # Additional info
    method: str = Field(description="Optimization method used")
    constraints: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class EfficientFrontierPoint(BaseModel):
    """Point on efficient frontier"""
    return_rate: float
    volatility: float
    weights: Dict[str, float]
    sharpe: Optional[float] = None