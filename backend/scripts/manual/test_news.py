"""Test News Agent"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import os

from dotenv import load_dotenv

from app.agents.news import NewsAgent
from app.graph.state import create_initial_state
from app.llm import GroqProvider, LLMConfig

load_dotenv()

async def test_news():
    print("🔍 Testing News Agent...")
    print("=" * 50)
    
    # Initialize
    config = LLMConfig(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        temperature=0.3,
        max_tokens=4096,
        timeout=60,
    )
    llm = GroqProvider(config)
    
    # Create agent
    agent = NewsAgent(llm)
    
    # Create state
    state = create_initial_state("Analyze NVIDIA")
    state["tickers"] = ["NVDA"]
    
    # Run agent
    print("\n📰 Fetching and analyzing news for NVIDIA...")
    result = await agent.process(state)
    
    # Display results
    news_results = result.get("news_analysis_results", [])
    
    for nr in news_results:
        print(f"\n📊 {nr['ticker']} News Analysis")
        print("-" * 40)
        
        sentiment = nr.get("sentiment_summary", {})
        print(f"Overall Sentiment: {sentiment.get('overall_sentiment', 'N/A')}")
        print(f"Average Score: {sentiment.get('average_score', 0):.2f}")
        print(f"Total Articles: {sentiment.get('total_articles', 0)}")
        
        dist = sentiment.get("sentiment_distribution", {})
        print(f"Distribution: Positive: {dist.get('positive', '0%')}, Neutral: {dist.get('neutral', '0%')}, Negative: {dist.get('negative', '0%')}")
        
        events = nr.get("key_events", [])
        if events:
            print("\nKey Events:")
            for e in events[:3]:
                print(f"  - {e.get('type')}: {e.get('title')[:60]}...")
        
        analysis = nr.get("llm_analysis", {})
        if analysis.get("analysis"):
            print("\n📝 LLM Analysis Preview:")
            print(f"{analysis['analysis'][:300]}...")

if __name__ == "__main__":
    asyncio.run(test_news())