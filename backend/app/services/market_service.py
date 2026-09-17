"""Real Market Data Service using yfinance with Financial Data API support"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import pandas as pd
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import settings
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class MarketService:
    """Service for fetching real market data with API fallback"""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache = cache_service or CacheService()
        self.api_key = settings.FINANCIAL_DATA_API_KEY
        self.use_api = bool(self.api_key)
        
        if self.use_api:
            logger.info("Financial Data API key found. Will use for enhanced data.")
        else:
            logger.info("No Financial Data API key. Using yfinance only.")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """Get stock information with API fallback"""
        ticker = ticker.upper()
        cache_key = self.cache.cache_key("stock_info", ticker)
        
        # Check cache first
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {ticker}")
            return cached
        
        data = None
        
        # Try Alpha Vantage if API key is available
        if self.use_api:
            data = await self._fetch_alpha_vantage(ticker)
        
        # Fallback to yfinance
        if not data or data.get("error"):
            data = await self._fetch_yfinance(ticker)
        
        # Cache for 5 minutes
        if data and not data.get("error"):
            await self.cache.set(cache_key, data, ttl=300)
            logger.info(f"Fetched data for {ticker}")
        
        return data or {"ticker": ticker, "error": "No data available"}
    
    async def _fetch_alpha_vantage(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch from Alpha Vantage API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "OVERVIEW",
                    "symbol": ticker,
                    "apikey": self.api_key,
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "Symbol" in data and data.get("Symbol"):
                            return {
                                "ticker": data.get("Symbol", ticker),
                                "name": data.get("Name", ticker),
                                "sector": data.get("Sector", "Unknown"),
                                "industry": data.get("Industry", "Unknown"),
                                "country": data.get("Country", "Unknown"),
                                "market_cap": self._safe_float(data.get("MarketCapitalization")),
                                "pe_ratio": self._safe_float(data.get("PERatio")),
                                "eps": self._safe_float(data.get("EPS")),
                                "revenue": self._safe_float(data.get("RevenueTTM")),
                                "gross_margin": self._safe_float(data.get("GrossProfitTTM")),
                                "profit_margin": self._safe_float(data.get("ProfitMargin")),
                                "debt_to_equity": self._safe_float(data.get("DebtToEquityMRQ")),
                                "return_on_equity": self._safe_float(data.get("ReturnOnEquityTTM")),
                                "dividend_yield": self._safe_float(data.get("DividendYield")),
                                "beta": self._safe_float(data.get("Beta")),
                                "fifty_two_week_high": self._safe_float(data.get("52WeekHigh")),
                                "fifty_two_week_low": self._safe_float(data.get("52WeekLow")),
                                "updated_at": datetime.now().isoformat(),
                                "source": "alpha_vantage",
                            }
                    else:
                        logger.warning(f"Alpha Vantage API error: {response.status}")
                        
        except asyncio.TimeoutError:
            logger.warning(f"Alpha Vantage timeout for {ticker}")
        except Exception as e:
            logger.error(f"Alpha Vantage error for {ticker}: {e}")
        
        return None
    
    async def _fetch_yfinance(self, ticker: str) -> Dict[str, Any]:
        """Fetch from yfinance (fallback)"""
        try:
            # Run yfinance in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, yf.Ticker, ticker)
            info = await loop.run_in_executor(None, lambda: stock.info)
            
            if not info:
                logger.warning(f"No data found for {ticker}")
                return {"ticker": ticker, "error": "No data available"}
            
            return {
                "ticker": ticker,
                "name": info.get("longName", info.get("shortName", ticker)),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "country": info.get("country", "Unknown"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("forwardPE", info.get("trailingPE")),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "price": info.get("currentPrice", info.get("regularMarketPrice")),
                "previous_close": info.get("regularMarketPreviousClose"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "volume": info.get("volume"),
                "avg_volume": info.get("averageVolume"),
                "target_price": info.get("targetMeanPrice"),
                "revenue": info.get("totalRevenue"),
                "gross_margin": info.get("grossMargins"),
                "profit_margin": info.get("profitMargins"),
                "debt_to_equity": info.get("debtToEquity"),
                "return_on_equity": info.get("returnOnEquity"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "updated_at": datetime.now().isoformat(),
                "source": "yfinance",
            }
            
        except Exception as e:
            logger.error(f"yfinance failed for {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}
    
    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert to float"""
        if value is None or value == "None":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    async def get_historical_data(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical price data"""
        ticker = ticker.upper()
        cache_key = self.cache.cache_key("historical", ticker, period, interval)
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for historical {ticker}")
            return pd.DataFrame(cached)
        
        try:
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, yf.Ticker, ticker)
            history = await loop.run_in_executor(
                None, 
                lambda: stock.history(period=period, interval=interval)
            )
            
            if history.empty:
                logger.warning(f"No historical data for {ticker}")
                return pd.DataFrame()
            
            # Convert to dict for caching
            history_dict = history.reset_index().to_dict('records')
            
            # Cache for 1 hour
            await self.cache.set(cache_key, history_dict, ttl=3600)
            logger.info(f"Fetched historical data for {ticker}")
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {ticker}: {e}")
            return pd.DataFrame()
    
    async def get_multiple_stocks(
        self,
        tickers: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Get data for multiple stocks"""
        results = {}
        for ticker in tickers:
            results[ticker] = await self.get_stock_info(ticker)
        return results
    
    async def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Lightweight last-price + day-change quotes for a set of symbols (indices,
        ETFs, or stocks - yfinance handles '^'-prefixed index tickers like ^VIX the
        same as any other symbol). Reuses get_stock_info's existing 5-minute cache,
        so this is cheap on repeat calls within the TTL."""
        quotes = []
        for symbol in symbols:
            data = await self.get_stock_info(symbol)
            price = data.get("price")
            previous_close = data.get("previous_close")

            change = None
            change_percent = None
            if price is not None and previous_close:
                change = price - previous_close
                change_percent = (change / previous_close) * 100

            quotes.append({
                "symbol": data.get("ticker", symbol.upper()),
                "name": data.get("name"),
                "price": price,
                "change": change,
                "change_percent": change_percent,
                "error": data.get("error"),
            })
        return quotes
    
    def get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        return self.cache.cache_key(prefix, *args)