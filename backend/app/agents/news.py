"""News Agent - Analyzes financial news and sentiment"""
import logging
from datetime import datetime
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.services.news_service import NewsService
from app.tools.sentiment import SentimentAnalyzer

logger = logging.getLogger(__name__)


class NewsAgent(BaseAgent):
    """News Analysis Agent"""
    
    def __init__(
        self,
        llm_provider,
        news_service: NewsService = None,
        sentiment_analyzer: SentimentAnalyzer = None,
    ):
        super().__init__("NewsAnalysis", llm_provider)
        self.news_service = news_service or NewsService()
        self.sentiment = sentiment_analyzer or SentimentAnalyzer()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process news and sentiment analysis for tickers in state"""
        tickers = state.get("tickers", [])
        self.logger.info(f"Analyzing news for: {tickers}")

        if not tickers:
            return {"errors": ["No tickers for news analysis"]}

        news_results = []
        errors: List[str] = []

        for ticker in tickers:
            try:
                articles = await self.news_service.get_news(
                    ticker=ticker,
                    days_back=7,
                    limit=15,
                )
                
                if not articles:
                    news_results.append({
                        "ticker": ticker,
                        "articles": [],
                        "sentiment_summary": {
                            "overall_sentiment": "neutral",
                            "average_score": 0.0,
                            "total_articles": 0,
                        },
                        "key_events": [],
                        "status": "no_news",
                    })
                    continue
                
                analyzed_articles = self.sentiment.analyze_articles(articles)
                sentiment_summary = self.sentiment.aggregate_sentiment(analyzed_articles)
                key_events = self.sentiment.detect_key_events(analyzed_articles)
                
                llm_analysis = await self._analyze_news(
                    ticker=ticker,
                    articles=analyzed_articles,
                    sentiment_summary=sentiment_summary,
                    key_events=key_events,
                )
                
                news_results.append({
                    "ticker": ticker,
                    "articles": analyzed_articles[:5],
                    "sentiment_summary": sentiment_summary,
                    "key_events": key_events[:3],
                    "llm_analysis": llm_analysis,
                    "total_articles": len(articles),
                    "timestamp": datetime.now().isoformat(),
                })
                
            except Exception as e:
                self.logger.error(f"News analysis failed for {ticker}: {e}")
                errors.append(f"News analysis failed for {ticker}: {str(e)}")

        self.logger.info(f"Completed news analysis for {len(news_results)} stocks")

        return {"news_analysis_results": news_results, "errors": errors}
    
    async def _analyze_news(
        self,
        ticker: str,
        articles: List[Dict[str, Any]],
        sentiment_summary: Dict[str, Any],
        key_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate news analysis using LLM"""
        
        article_summaries = []
        for i, article in enumerate(articles[:5], 1):
            article_summaries.append(f"""
            {i}. {article.get('title', '')}
               Sentiment: {article.get('sentiment_analysis', {}).get('sentiment', 'neutral')}
               Score: {article.get('sentiment_analysis', {}).get('score', 0):.2f}
               Source: {article.get('source', 'Unknown')}
            """)
        
        events_text = "\n".join([
            f"- {e.get('type')}: {e.get('title')} (Sentiment: {e.get('sentiment', 'neutral')})"
            for e in key_events[:5]
        ]) if key_events else "No significant events detected."
        
        prompt = f"""
        Analyze the news sentiment and market intelligence for {ticker}.
        
        NEWS SENTIMENT SUMMARY:
        Overall Sentiment: {sentiment_summary.get('overall_sentiment', 'neutral')}
        Average Score: {sentiment_summary.get('average_score', 0):.2f}
        Distribution: {sentiment_summary.get('sentiment_distribution', {})}
        Total Articles: {sentiment_summary.get('total_articles', 0)}
        
        KEY EVENTS:
        {events_text}
        
        RECENT ARTICLES:
        {''.join(article_summaries)}
        
        Based on this news data, provide:
        1. Overall market sentiment for {ticker}
        2. Key themes and trends in recent news
        3. Potential market impact of key events
        4. Any emerging risks or opportunities
        5. Summary conclusion for investors
        
        Be specific and reference the news data. Write in 3-5 short plain-text paragraphs -
        no markdown headers, bold/asterisks, tables, or bullet lists. This is a prose summary
        shown directly in a UI card, not a formatted document.
        """

        system_prompt = """You are a financial news analyst. Provide objective, data-driven analysis
        based on the news sentiment data provided as plain prose (no markdown/tables - this text is
        rendered as-is in a UI card). Do not invent information."""

        response = await self.call_llm(prompt, system_prompt, max_tokens=700)
        
        return {
            "analysis": response,
            "sentiment_summary": sentiment_summary,
            "key_events": key_events[:5],
        }