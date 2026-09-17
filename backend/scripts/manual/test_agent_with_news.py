"""Test Agent System with News"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

from app.graph.workflow import AlphaLensWorkflow
from app.llm import GroqProvider, LLMConfig

load_dotenv()

async def test_full_analysis():
    print("🔍 Testing Full Agent Analysis with News")
    print("=" * 50)
    
    # Initialize LLM
    config = LLMConfig(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        temperature=0.3,
        max_tokens=4096,
        timeout=60,
    )
    llm = GroqProvider(config)
    workflow = AlphaLensWorkflow(llm)

    # Test queries
    queries = [
        "Analyze NVIDIA including recent news sentiment",
        "What's the latest news and performance of Apple?",
        "Analyze Microsoft's market position and recent news",
    ]

    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 40)

        result = await workflow.run(query)

        # Show results
        tickers = result.get("tickers", [])
        print(f"✅ Tickers: {tickers}")

        # Show which agents ran
        completed = result.get("completed_agents", [])
        print(f"✅ Agents: {completed}")
        
        # Show errors if any
        errors = result.get("errors", [])
        if errors:
            print(f"❌ Errors: {errors}")
        
        # Show report preview
        report = result.get("final_report", "")
        if report:
            print(f"📄 Report Preview: {report[:300]}...")
        else:
            print("⚠️ No report generated")

if __name__ == "__main__":
    asyncio.run(test_full_analysis())