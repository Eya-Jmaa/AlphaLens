"""Sentiment Analysis Tools"""
import logging
from typing import Any, Dict, List

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Sentiment analysis using multiple approaches"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        logger.info("SentimentAnalyzer initialized")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a text
        
        Returns:
            {
                "sentiment": "positive" | "neutral" | "negative",
                "score": float between -1 and 1,
                "confidence": float,
                "details": {...}
            }
        """
        if not text:
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "confidence": 0.0,
                "details": {"error": "Empty text"}
            }
        
        try:
            # VADER sentiment
            vader_scores = self.vader.polarity_scores(text)
            vader_score = vader_scores["compound"]
            
            # TextBlob sentiment
            blob = TextBlob(text)
            blob_score = blob.sentiment.polarity
            
            # Combine scores (weighted average)
            combined_score = (vader_score * 0.7) + (blob_score * 0.3)
            
            # Determine sentiment
            if combined_score > 0.05:
                sentiment = "positive"
            elif combined_score < -0.05:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            confidence = min(abs(vader_scores["compound"]), 1.0)
            
            return {
                "sentiment": sentiment,
                "score": combined_score,
                "confidence": confidence,
                "details": {
                    "vader": vader_scores,
                    "textblob": {
                        "polarity": blob_score,
                        "subjectivity": blob.sentiment.subjectivity,
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "confidence": 0.0,
                "details": {"error": str(e)}
            }
    
    def analyze_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze sentiment for multiple articles"""
        results = []
        
        for article in articles:
            # Combine title and description for better analysis
            text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
            
            sentiment = self.analyze_text(text)
            
            results.append({
                **article,
                "sentiment_analysis": sentiment,
            })
        
        return results
    
    def aggregate_sentiment(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate sentiment from multiple articles"""
        if not articles:
            return {
                "overall_sentiment": "neutral",
                "average_score": 0.0,
                "confidence": 0.0,
                "counts": {"positive": 0, "neutral": 0, "negative": 0},
                "total_articles": 0,
            }
        
        scores = []
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        
        for article in articles:
            sentiment = article.get("sentiment_analysis", {})
            score = sentiment.get("score", 0)
            sentiment_label = sentiment.get("sentiment", "neutral")
            
            scores.append(score)
            counts[sentiment_label] = counts.get(sentiment_label, 0) + 1
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score > 0.05:
            overall = "positive"
        elif avg_score < -0.05:
            overall = "negative"
        else:
            overall = "neutral"
        
        confidence = min(abs(avg_score), 1.0)
        
        return {
            "overall_sentiment": overall,
            "average_score": avg_score,
            "confidence": confidence,
            "counts": counts,
            "total_articles": len(articles),
            "sentiment_distribution": {
                "positive": f"{counts['positive'] / len(articles) * 100:.1f}%",
                "neutral": f"{counts['neutral'] / len(articles) * 100:.1f}%",
                "negative": f"{counts['negative'] / len(articles) * 100:.1f}%",
            }
        }
    
    def detect_key_events(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect key events from news articles"""
        events = []
        
        # Keywords for event detection
        event_keywords = {
            "earnings": ["earnings", "revenue", "profit", "loss", "beat", "miss", "report"],
            "product": ["launch", "release", "announce", "new", "update", "upgrade"],
            "acquisition": ["acquire", "merger", "deal", "buy", "takeover"],
            "partnership": ["partner", "collaboration", "alliance", "agreement"],
            "regulation": ["regulatory", "investigation", "fine", "compliance", "lawsuit"],
            "leadership": ["ceo", "executive", "appoint", "resign", "hire", "fire"],
            "market": ["market share", "competition", "competitor", "position"],
            "technology": ["ai", "cloud", "quantum", "innovation", "patent", "technology"],
        }
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            for event_type, keywords in event_keywords.items():
                if any(kw in text for kw in keywords):
                    events.append({
                        "type": event_type,
                        "title": article.get("title", ""),
                        "source": article.get("source", ""),
                        "url": article.get("url", ""),
                        "published_at": article.get("published_at", ""),
                        "sentiment": article.get("sentiment_analysis", {}).get("sentiment", "neutral"),
                    })
                    break  # Only tag with first matching event type
        
        return events