"""Test Risk Analysis"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

from app.agents.risk import RiskAgent
from app.graph.state import create_initial_state
from app.llm import GroqProvider, LLMConfig
from app.services.market_service import MarketService
from app.services.risk_service import RiskService
from app.tools.portfolio import PortfolioOptimizer

load_dotenv()

async def test_risk():
    print("🔍 Testing Risk Analysis")
    print("=" * 50)
    
    # Initialize
    config = LLMConfig(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0.3,
        max_tokens=4096,
        timeout=60,
    )
    llm = GroqProvider(config)
    
    # Create risk agent
    market_service = MarketService()
    risk_service = RiskService(market_service)
    optimizer = PortfolioOptimizer()
    agent = RiskAgent(llm, risk_service, market_service, optimizer)
    
    # Create state
    state = create_initial_state("Analyze risk for NVIDIA, Apple, and Microsoft")
    state["tickers"] = ["NVDA", "AAPL", "MSFT"]
    
    # Run agent
    print("\n📊 Running risk analysis...")
    result = await agent.process(state)
    
    # Display results
    risk_results = result.get("risk_analysis_results", {})
    
    if risk_results:
        print("\n📈 Individual Stock Risks:")
        for ticker, data in risk_results.get("stock_risks", {}).items():
            print(f"\n{ticker}:")
            print(f"  Volatility: {data.get('volatility', 0):.2%}")
            print(f"  VaR 95%: {data.get('var_95', 0):.2%}")
            print(f"  Max Drawdown: {data.get('max_drawdown', 0):.2%}")
            print(f"  Beta: {data.get('beta', 0):.2f}")
        
        metrics = risk_results.get("portfolio_metrics", {})
        if metrics:
            print("\n📊 Portfolio Metrics:")
            print(f"  Volatility: {metrics.get('volatility', 0):.2%}")
            print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
            print(f"  VaR 95%: {metrics.get('var_95', 0):.2%}")
            print(f"  Effective Holdings: {metrics.get('effective_number', 0):.1f}")
        
        # Show LLM analysis preview
        analysis = risk_results.get("llm_analysis", "")
        if analysis:
            print("\n🤖 Risk Analysis Preview:")
            print(f"{analysis[:500]}...")

if __name__ == "__main__":
    asyncio.run(test_risk())