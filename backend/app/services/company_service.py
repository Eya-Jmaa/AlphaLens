"""Enhanced Company Service with Real Data"""
import logging
from typing import Any, Dict, List, Optional

import numpy as np  # Add this import

from app.core.known_companies import search_companies
from app.services.cache_service import CacheService
from app.services.market_service import MarketService
from app.tools.financial import FinancialCalculator
from app.tools.technical import TechnicalAnalyzer

logger = logging.getLogger(__name__)


class CompanyService:
    """Service for fetching company and market data with real data"""
    
    def __init__(
        self,
        market_service: Optional[MarketService] = None,
        cache_service: Optional[CacheService] = None
    ):
        self.cache = cache_service or CacheService()
        self.market = market_service or MarketService(self.cache)
        self.technical = TechnicalAnalyzer()
        self.financial = FinancialCalculator()
    
    async def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """Get company information with real data"""
        return await self.market.get_stock_info(ticker)

    async def get_historical_data(self, ticker: str, period: str = "1y"):
        """Get historical OHLCV data (pass-through, for charting)"""
        return await self.market.get_historical_data(ticker, period=period)
    
    async def get_market_data(self, ticker: str) -> Dict[str, Any]:
        """Get market data including technical analysis"""
        ticker = ticker.upper()
        
        # Get stock info
        info = await self.market.get_stock_info(ticker)
        
        # Get historical data for technical analysis
        history = await self.market.get_historical_data(ticker, period="1y")
        
        result = {
            "ticker": ticker,
            "info": info,
            "technical": {},
            "returns": {},
            "risk": {},
        }
        
        # Calculate technical indicators
        if not history.empty and len(history) >= 20:
            try:
                technical_analysis = self.technical.analyze_all(history)
                result["technical"] = technical_analysis
            except Exception as e:
                logger.error(f"Technical analysis failed for {ticker}: {e}")
        
        # Calculate returns and risk
        if not history.empty and len(history) >= 2:
            try:
                close = history['Close']
                returns = close.pct_change().dropna()
                
                result["returns"] = {
                    "daily_returns": returns.tolist()[-30:],  # Last 30 days
                    "volatility": float(returns.std() * np.sqrt(252)) if len(returns) > 0 else None,
                    "sharpe_ratio": self.financial.calculate_sharpe_ratio(returns) if len(returns) > 0 else None,
                    "max_drawdown": float(self.financial.calculate_max_drawdown(returns)) if len(returns) > 0 else None,
                }
                
                # Risk metrics
                if len(returns) > 10:
                    var = self.financial.calculate_var(returns)
                    result["risk"] = {
                        "var_95": var.get("var"),
                        "cvar_95": var.get("cvar"),
                    }
            except Exception as e:
                logger.error(f"Return calculation failed for {ticker}: {e}")
        
        return result
    
    async def search_company(self, query: str) -> List[Dict[str, str]]:
        """Search for companies matching the query"""
        return search_companies(query)

    async def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Lightweight last-price + day-change quotes for a set of symbols"""
        return await self.market.get_quotes(symbols)