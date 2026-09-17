"""Test Full Agent System"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

from app.graph.workflow import AlphaLensWorkflow
from app.llm import GroqProvider, LLMConfig

load_dotenv()

async def test_full_system():
    print("🔍 Testing Full Agent System")
    print("=" * 60)
    
    config = LLMConfig(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0.3,
        max_tokens=4096,
        timeout=60,
    )
    llm = GroqProvider(config)
    workflow = AlphaLensWorkflow(llm)

    queries = [
        "Analyze NVIDIA including recent news and risk",
        "Analyze my portfolio with AAPL, MSFT, NVDA",
    ]

    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 40)

        result = await workflow.run(query)

        print(f"✅ Tickers: {result.get('tickers', [])}")
        print(f"✅ Agents Run: {result.get('completed_agents', [])}")
        
        report = result.get("final_report", "")
        if report:
            print(f"\n📄 Report Preview:\n{report[:500]}...")

if __name__ == "__main__":
    asyncio.run(test_full_system())