"""Pydantic Schemas for API"""
import re
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalyzeRequest(BaseModel):
    """Analysis request schema"""
    query: str = Field(..., description="User's financial query")
    debate: bool = Field(
        False, description="Run the Bull/Bear/Judge debate branch (also auto-detected from the query text)"
    )


class Source(BaseModel):
    """Source reference"""
    name: str
    url: Optional[str] = None
    type: str  # "news", "sec", "api", "report"
    retrieved_at: datetime = Field(default_factory=datetime.now)


class AnalyzeResponse(BaseModel):
    """Analysis response schema"""
    query: str
    analysis: str
    confidence: float = Field(..., ge=0, le=1)
    sources: List[Source] = []
    warnings: List[str] = []
    disclaimer: str = "This is an informational analysis, not financial advice."
    timestamp: datetime = Field(default_factory=datetime.now)


class CompanyInfo(BaseModel):
    """Company information"""
    ticker: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    description: Optional[str] = None


class PortfolioPositionRequest(BaseModel):
    """A single position in a portfolio request"""
    ticker: str = Field(..., description="Stock ticker symbol")
    weight: float = Field(..., ge=0, le=1, description="Portfolio weight (0-1)")

    @field_validator("ticker")
    @classmethod
    def _validate_ticker(cls, value: str) -> str:
        value = value.strip().upper()
        if not TICKER_PATTERN.fullmatch(value):
            raise ValueError(f"'{value}' is not a valid ticker symbol")
        return value


class PortfolioAnalyzeRequest(BaseModel):
    """Request to analyze the risk of a given portfolio"""
    positions: List[PortfolioPositionRequest] = Field(..., min_length=1)
    cash: float = Field(0.0, ge=0)

    @field_validator("positions")
    @classmethod
    def _validate_weights(cls, positions: List[PortfolioPositionRequest]) -> List[PortfolioPositionRequest]:
        total = sum(p.weight for p in positions)
        if total <= 0:
            raise ValueError("Portfolio weights must sum to a positive number")
        return positions


class PortfolioOptimizeRequest(BaseModel):
    """Request to optimize a given portfolio"""
    positions: List[PortfolioPositionRequest] = Field(..., min_length=2)
    method: Literal["max_sharpe", "min_volatility"] = "max_sharpe"
    max_weight: Optional[float] = Field(None, gt=0, le=1)


class SavePortfolioRequest(BaseModel):
    """Request to persist a portfolio definition for later reuse"""
    name: str = Field("My Portfolio", max_length=120)
    positions: List[PortfolioPositionRequest] = Field(..., min_length=1)
    cash: float = Field(0.0, ge=0)