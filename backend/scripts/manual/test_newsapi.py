"""Test NewsAPI Directly"""
import os

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NEWS_API_KEY")
print(f"API Key: {api_key[:10] if api_key else 'NOT SET'}...")

if api_key:
    try:
        from newsapi import NewsApiClient
        client = NewsApiClient(api_key=api_key)
        
        # Test top headlines
        result = client.get_top_headlines(
            category="business",
            language="en",
            country="us",
            page_size=5,
        )
        
        articles = result.get("articles", [])
        print(f"\n✅ Found {len(articles)} articles")
        
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article.get('title', 'N/A')}")
            print(f"   Source: {article.get('source', {}).get('name', 'Unknown')}")
            print(f"   URL: {article.get('url', 'N/A')}")
            
    except ImportError:
        print("❌ newsapi-python not installed. Run: pip install newsapi-python")
    except Exception as e:
        print(f"❌ NewsAPI error: {e}")
else:
    print("❌ NEWS_API_KEY not set in .env")