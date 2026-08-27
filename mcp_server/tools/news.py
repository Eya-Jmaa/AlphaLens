"""News/sentiment MCP tools - thin wrappers around app.services.news_service"""
from typing import Any, Dict

from app.services.news_service import NewsService
from app.tools.sentiment import SentimentAnalyzer

_news_service = NewsService()
_sentiment = SentimentAnalyzer()


def register(server) -> None:
    @server.tool()
    async def search_news(ticker: str, days_back: int = 7, limit: int = 10) -> Dict[str, Any]:
        """Search recent financial news for a ticker and score its sentiment.

        Args:
            ticker: Stock ticker symbol, e.g. "NVDA".
            days_back: How many days back to search (default 7).
            limit: Maximum number of articles to return (default 10).
        """
        articles = await _news_service.get_news(ticker=ticker, days_back=days_back, limit=limit)
        if not articles:
            return {"ticker": ticker.upper(), "articles": [], "sentiment": None, "status": "no_news"}

        analyzed = _sentiment.analyze_articles(articles)
        summary = _sentiment.aggregate_sentiment(analyzed)

        return {
            "ticker": ticker.upper(),
            "sentiment_summary": summary,
            "articles": [
                {
                    "title": a.get("title"),
                    "source": a.get("source"),
                    "published_at": a.get("published_at"),
                    "url": a.get("url"),
                    "sentiment": a.get("sentiment_analysis", {}).get("sentiment"),
                    "is_mock": a.get("is_mock", False),
                }
                for a in analyzed[:limit]
            ],
        }
