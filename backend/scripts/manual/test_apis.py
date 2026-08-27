"""Test Financial Data and News APIs"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.services.market_service import MarketService
from app.services.news_service import NewsService


async def test_apis():
    print("🔍 Testing Financial Data & News APIs")
    print("=" * 50)
    
    # Test Market Service
    print("\n📈 Testing Market Service...")
    market = MarketService()
    
    # Test single stock
    print("\n1. Fetching NVIDIA data...")
    data = await market.get_stock_info("NVDA")
    print(f"   Name: {data.get('name', 'N/A')}")
    print(f"   Price: ${data.get('price', 'N/A')}")
    print(f"   Source: {data.get('source', 'unknown')}")
    print(f"   Market Cap: ${data.get('market_cap', 'N/A')}")
    
    # Test News Service
    print("\n📰 Testing News Service...")
    news = NewsService()
    
    # Test news for NVIDIA
    print("\n2. Fetching news for NVIDIA...")
    articles = await news.get_news("NVDA", days_back=3, limit=5)
    print(f"   Found {len(articles)} articles")
    
    if articles:
        real_count = sum(1 for a in articles if not a.get('is_mock', True))
        mock_count = sum(1 for a in articles if a.get('is_mock', False))
        print(f"   Real: {real_count}, Mock: {mock_count}")
        
        print("\n   Latest articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"   {i}. {article.get('title', 'N/A')[:60]}...")
            print(f"      Source: {article.get('source', 'Unknown')}")
    
    # Test market news
    print("\n3. Fetching market news...")
    market_news = await news.get_market_news(limit=5)
    print(f"   Found {len(market_news)} market news articles")
    
    if market_news:
        print("\n   Top market headlines:")
        for i, article in enumerate(market_news[:3], 1):
            print(f"   {i}. {article.get('title', 'N/A')[:60]}...")

if __name__ == "__main__":
    asyncio.run(test_apis())