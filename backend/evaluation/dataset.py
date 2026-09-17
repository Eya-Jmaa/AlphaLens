"""Evaluation benchmark: structural expectations, not exact-text matches (LLM
output is non-deterministic - see spec §30). Each case checks that the right
agents ran, the right tickers were extracted, and the output is structurally
valid, not that the prose says any particular thing.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class EvalCase:
    name: str
    query: str
    expected_tickers: List[str] = field(default_factory=list)
    expected_agents: List[str] = field(default_factory=list)
    debate: bool = False
    min_report_chars: int = 100


DATASET_NAME = "alphalens-core-v1"

CASES: List[EvalCase] = [
    EvalCase(
        name="single_company_overview",
        query="Analyze NVIDIA",
        expected_tickers=["NVDA"],
        expected_agents=["Supervisor", "StockAnalysis", "FinalAnalyst"],
    ),
    EvalCase(
        name="sec_10k_risk_question",
        query="What are Apple's main risks according to its latest 10-K?",
        expected_tickers=["AAPL"],
        expected_agents=["Supervisor", "StockAnalysis", "SECAnalysis", "FinalAnalyst"],
    ),
    EvalCase(
        name="fundamentals_question",
        query="What was NVIDIA's revenue growth?",
        expected_tickers=["NVDA"],
        expected_agents=["Supervisor", "StockAnalysis", "FinalAnalyst"],
    ),
    EvalCase(
        name="technical_trend_question",
        query="Analyze Tesla's technical trend",
        expected_tickers=["TSLA"],
        expected_agents=["Supervisor", "StockAnalysis", "FinalAnalyst"],
    ),
    EvalCase(
        name="multi_company_comparison",
        query="Compare Microsoft and Google",
        expected_tickers=["MSFT", "GOOGL"],
        expected_agents=["Supervisor", "StockAnalysis", "FinalAnalyst"],
    ),
    EvalCase(
        name="risk_focused_question",
        query="What are Tesla's biggest risks?",
        expected_tickers=["TSLA"],
        expected_agents=["Supervisor", "StockAnalysis", "RiskAnalysis", "FinalAnalyst"],
    ),
    EvalCase(
        name="news_and_risk_combined",
        query="Analyze NVIDIA including recent news and risk",
        expected_tickers=["NVDA"],
        expected_agents=["Supervisor", "StockAnalysis", "NewsAnalysis", "RiskAnalysis", "FinalAnalyst"],
    ),
    EvalCase(
        name="bull_bear_debate",
        query="Give me the bull and bear case for NVIDIA",
        expected_tickers=["NVDA"],
        expected_agents=["Supervisor", "StockAnalysis", "BullCase", "BearCase", "Judge", "FinalAnalyst"],
        debate=True,
    ),
]
