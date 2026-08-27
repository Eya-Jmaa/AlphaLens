"""News Service - Fetch financial news from NewsAPI with fallback"""
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.core.known_companies import company_name_for
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching financial news with NewsAPI and fallback"""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache = cache_service or CacheService()
        self.api_key = settings.NEWS_API_KEY
        self.newsapi = None
        
        # Initialize NewsAPI if key exists
        if self.api_key:
            try:
                from newsapi import NewsApiClient
                self.newsapi = NewsApiClient(api_key=self.api_key)
                logger.info("NewsAPI client initialized successfully")
            except ImportError:
                logger.warning("newsapi-python not installed. Install with: pip install newsapi-python")
                self.newsapi = None
            except Exception as e:
                logger.error(f"Failed to initialize NewsAPI: {e}")
                self.newsapi = None
        else:
            logger.warning("NEWS_API_KEY not set. Using mock data only.")
    
    async def get_news(
        self,
        ticker: str,
        days_back: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get news articles for a ticker"""
        cache_key = self.cache.cache_key("news", ticker, days_back, limit)
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for news: {ticker}")
            return cached
        
        articles = []
        
        # Try NewsAPI first
        if self.newsapi and self.api_key:
            try:
                articles = await self._fetch_newsapi(ticker, days_back, limit)
                if articles:
                    logger.info(f"Fetched {len(articles)} real articles for {ticker}")
            except Exception as e:
                logger.error(f"NewsAPI failed for {ticker}: {e}")
        
        # Fallback to mock data if no articles
        if not articles:
            articles = self._fetch_mock_news(ticker, days_back, limit)
            logger.info(f"Generated {len(articles)} mock articles for {ticker}")
        
        # Cache for 5 minutes
        await self.cache.set(cache_key, articles, ttl=300)
        
        return articles
    
    async def _fetch_newsapi(
        self,
        ticker: str,
        days_back: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch news from NewsAPI"""
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

            # Use the company name for a better search match when known
            company_name = company_name_for(ticker)
            query = company_name.split()[0] if company_name else ticker
            
            # Search with query
            results = self.newsapi.get_everything(
                q=query,
                from_param=from_date,
                language="en",
                sort_by="relevancy",
                page_size=limit,
            )
            
            articles = []
            for article in results.get("articles", []):
                # Skip articles without title
                if not article.get("title"):
                    continue
                    
                articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", datetime.now().isoformat()),
                    "author": article.get("author", ""),
                    "ticker": ticker,
                    "is_mock": False,
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []
    
    def _fetch_mock_news(
        self,
        ticker: str,
        days_back: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Generate realistic mock news data"""
        
        # Realistic news templates by ticker
        news_templates = {
            "NVDA": [
                {
                    "title": "NVIDIA Announces Next-Gen AI Chips with 4x Performance Boost",
                    "description": "NVIDIA unveiled its new Blackwell architecture for AI computing, claiming 4x performance improvement over previous generation. The new chips are expected to ship in Q4 2024.",
                    "source": "TechCrunch",
                    "sentiment": "positive",
                },
                {
                    "title": "NVIDIA Q2 Earnings Beat Expectations on AI Demand",
                    "description": "NVIDIA reported record revenue of $22.1 billion, driven by strong demand for AI chips in data centers. The company raised its full-year guidance.",
                    "source": "Reuters",
                    "sentiment": "positive",
                },
                {
                    "title": "Competition Heats Up in AI Chip Market as AMD and Intel Ramp Up",
                    "description": "AMD and Intel are aggressively expanding their AI chip portfolios, creating competitive pressure for NVIDIA. Market share dynamics are shifting.",
                    "source": "Wall Street Journal",
                    "sentiment": "neutral",
                },
                {
                    "title": "NVIDIA's CUDA Ecosystem Strengthens Competitive Moat",
                    "description": "NVIDIA's CUDA platform has become the de facto standard for AI development, with over 2 million developers building on the platform.",
                    "source": "Forbes",
                    "sentiment": "positive",
                },
                {
                    "title": "China Export Restrictions Could Impact NVIDIA's Growth",
                    "description": "New US export restrictions on AI chips to China could impact up to 15% of NVIDIA's revenue, analysts warn.",
                    "source": "Financial Times",
                    "sentiment": "negative",
                },
            ],
            "AAPL": [
                {
                    "title": "Apple Intelligence: New AI Features Coming to iPhone 16",
                    "description": "Apple announced new AI features for iOS, including enhanced Siri, generative AI capabilities, and on-device processing.",
                    "source": "Bloomberg",
                    "sentiment": "positive",
                },
                {
                    "title": "iPhone Sales Slip as Competition Intensifies in China",
                    "description": "Apple reported a slight decline in iPhone sales amid intense competition from Huawei and other Chinese manufacturers.",
                    "source": "Financial Times",
                    "sentiment": "negative",
                },
                {
                    "title": "Apple Services Revenue Hits Record $85.2 Billion",
                    "description": "Apple's services business continues to grow, with App Store, Apple Music, and iCloud driving record revenue.",
                    "source": "CNBC",
                    "sentiment": "positive",
                },
            ],
            "MSFT": [
                {
                    "title": "Azure AI Revenue Soars as Microsoft Invests Heavily",
                    "description": "Microsoft's Azure AI services grew 50% year-over-year, driven by enterprise adoption of AI and cloud services.",
                    "source": "CNBC",
                    "sentiment": "positive",
                },
                {
                    "title": "Microsoft's Copilot AI Integration Boosts Productivity",
                    "description": "Microsoft's Copilot AI assistant is seeing rapid adoption across Office 365 and Windows, creating new revenue streams.",
                    "source": "TechCrunch",
                    "sentiment": "positive",
                },
                {
                    "title": "Regulatory Scrutiny Intensifies on Microsoft's AI Practices",
                    "description": "EU and US regulators are examining Microsoft's AI partnerships and market dominance in enterprise software.",
                    "source": "Reuters",
                    "sentiment": "negative",
                },
            ],
            "GOOGL": [
                {
                    "title": "Google's AI Search Features Drive User Engagement",
                    "description": "Google's new AI-powered search features are improving user engagement and ad revenue, early data shows.",
                    "source": "Wall Street Journal",
                    "sentiment": "positive",
                },
                {
                    "title": "YouTube Ad Revenue Surges as Google AI Optimizes Content",
                    "description": "YouTube's advertising revenue jumped 15% as Google's AI algorithms improve content recommendations.",
                    "source": "Bloomberg",
                    "sentiment": "positive",
                },
            ],
            "AMZN": [
                {
                    "title": "Amazon's Cloud Business Resilience Despite Competition",
                    "description": "AWS maintains market leadership with 30% market share, though Microsoft Azure is gaining ground.",
                    "source": "Financial Times",
                    "sentiment": "neutral",
                },
                {
                    "title": "Amazon's AI-Powered Logistics Drive Efficiency Gains",
                    "description": "Amazon's AI investments in supply chain and logistics are reducing costs and improving delivery times.",
                    "source": "TechCrunch",
                    "sentiment": "positive",
                },
            ],
            "TSLA": [
                {
                    "title": "Tesla's Cybertruck Production Ramping Amid Strong Demand",
                    "description": "Tesla is accelerating Cybertruck production with over 1 million pre-orders, signaling strong demand for the electric truck.",
                    "source": "Reuters",
                    "sentiment": "positive",
                },
                {
                    "title": "Tesla's AI Day Shows Ambition in Self-Driving Technology",
                    "description": "Tesla's AI Day highlighted progress in autonomous driving technology, with full self-driving v12 expected by year-end.",
                    "source": "TechCrunch",
                    "sentiment": "positive",
                },
                {
                    "title": "Competition from Chinese EV Makers Intensifies",
                    "description": "Chinese EV manufacturers are aggressively expanding globally, posing a threat to Tesla's market dominance.",
                    "source": "Wall Street Journal",
                    "sentiment": "negative",
                },
            ],
        }
        
        # Get templates for this ticker, or use generic
        templates = news_templates.get(ticker, [
            {
                "title": f"{ticker} Shows Strong Performance in Q2",
                "description": f"{ticker} reported better-than-expected results, driven by strong demand and operational efficiency.",
                "source": "Reuters",
                "sentiment": "positive",
            },
            {
                "title": f"{ticker} Faces Headwinds from Competition",
                "description": f"Competitive pressures are weighing on {ticker} as rivals gain market share.",
                "source": "Financial Times",
                "sentiment": "negative",
            },
        ])
        
        articles = []
        for i, item in enumerate(templates[:limit]):
            days_ago = random.randint(0, days_back)
            
            articles.append({
                "title": item["title"],
                "description": item["description"],
                "content": item["description"] + " Full story available on source website.",
                "source": item["source"],
                "url": f"https://example.com/news/{ticker}_{datetime.now().strftime('%Y%m%d')}_{i}",
                "published_at": (datetime.now() - timedelta(days=days_ago)).isoformat(),
                "author": ["John Smith", "Jane Doe", "Mike Johnson", "Sarah Lee"][random.randint(0, 3)],
                "ticker": ticker,
                "is_mock": True,
            })
        
        return articles
    
    async def get_market_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get general market news"""
        cache_key = self.cache.cache_key("market_news", limit)
        
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        articles = []
        
        # Try NewsAPI for top headlines
        if self.newsapi and self.api_key:
            try:
                results = self.newsapi.get_top_headlines(
                    category="business",
                    language="en",
                    country="us",
                    page_size=limit,
                )
                
                for article in results.get("articles", []):
                    if article.get("title"):
                        articles.append({
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "source": article.get("source", {}).get("name", "Unknown"),
                            "url": article.get("url", ""),
                            "published_at": article.get("publishedAt", datetime.now().isoformat()),
                            "is_mock": False,
                        })
            except Exception as e:
                logger.error(f"Failed to fetch market news: {e}")
        
        # Fallback to mock market news
        if not articles:
            articles = self._fetch_mock_market_news(limit)
        
        await self.cache.set(cache_key, articles, ttl=300)
        return articles
    
    def _fetch_mock_market_news(self, limit: int) -> List[Dict[str, Any]]:
        """Generate mock market news"""
        headlines = [
            ("Fed Signals Potential Rate Cut as Inflation Cools", "The Federal Reserve indicated it may begin cutting interest rates in 2024 as inflation shows signs of cooling."),
            ("Stock Market Rallies on Strong Tech Earnings", "Major indexes climbed as tech companies reported better-than-expected earnings."),
            ("Oil Prices Slip on Demand Concerns", "Crude oil prices declined amid concerns about global demand."),
            ("Gold Hits Record High as Safe-Haven Demand Grows", "Gold prices reached a new record as investors seek safe-haven assets."),
            ("Dollar Weakens on Rate Cut Expectations", "The US dollar fell against major currencies as rate cut expectations grow."),
            ("Tech Sector Leads Market Gains", "Technology stocks led the market higher as AI optimism continues."),
            ("Banking Sector Faces Headwinds", "Regional banks face pressure from commercial real estate exposure."),
            ("Retail Sales Surprise to the Upside", "Retail sales data beat expectations, indicating resilient consumer spending."),
            ("Job Market Shows Signs of Cooling", "Recent data suggests the job market is beginning to cool."),
            ("AI Investment Boom Continues", "Companies continue to invest heavily in AI infrastructure and capabilities."),
        ]
        
        articles = []
        for i, (title, desc) in enumerate(headlines[:limit]):
            articles.append({
                "title": title,
                "description": desc,
                "source": ["Reuters", "Bloomberg", "CNBC", "FT", "WSJ"][i % 5],
                "url": f"https://example.com/market_news/{i}",
                "published_at": (datetime.now() - timedelta(hours=i * 2)).isoformat(),
                "is_mock": True,
            })
        
        return articles