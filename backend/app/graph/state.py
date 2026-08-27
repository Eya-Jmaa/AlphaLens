"""Financial Analysis State Definition (LangGraph state schema)"""
import operator
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, TypedDict


def _merge_dicts(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer for dict-valued channels written by parallel branches."""
    merged = dict(left or {})
    merged.update(right or {})
    return merged


class FinancialAnalysisState(TypedDict, total=False):
    """State for the financial analysis workflow.

    Fields written by exactly one node (e.g. stock_analysis_results) use plain
    last-write-wins semantics. Fields that multiple parallel agent nodes may
    write to in the same superstep (errors, warnings, completed_agents,
    agent_timings, evidence) use an additive reducer so LangGraph merges
    partial updates instead of raising a concurrent-update conflict.
    """

    # User Input
    user_query: str
    tickers: List[str]
    company_names: List[str]

    # Analysis Requests
    requested_analysis: List[str]
    required_agents: List[str]
    debate_mode: bool

    # Agent Results - each written by exactly one node
    stock_analysis_results: List[Dict[str, Any]]
    news_analysis_results: List[Dict[str, Any]]
    sec_analysis_results: List[Dict[str, Any]]
    technical_analysis_results: Dict[str, Any]
    risk_analysis_results: Dict[str, Any]
    portfolio_optimization_results: Dict[str, Any]

    # Bull/Bear/Judge debate (optional - only populated in debate mode). Bull and
    # Bear run in parallel and both write into this dict, so it needs the same
    # merge reducer as agent_timings.
    debate_results: Annotated[Dict[str, Any], _merge_dicts]

    # Final Output
    final_report: str
    overall_assessment: Dict[str, Any]
    confidence: float
    evidence: Annotated[List[Dict[str, str]], operator.add]

    # Metadata - additive/mergeable across parallel branches
    errors: Annotated[List[str], operator.add]
    warnings: Annotated[List[str], operator.add]
    completed_agents: Annotated[List[str], operator.add]
    agent_timings: Annotated[Dict[str, float], _merge_dicts]
    start_time: datetime
    end_time: Optional[datetime]

    # User Profile / Portfolio (for future features)
    user_profile: Optional[Dict[str, Any]]
    portfolio: Optional[Dict[str, Any]]


def create_initial_state(query: str, debate_mode: bool = False) -> FinancialAnalysisState:
    """Create initial state for a new analysis"""
    return {
        "user_query": query,
        "tickers": [],
        "company_names": [],
        "requested_analysis": [],
        "required_agents": [],
        "debate_mode": debate_mode,
        "stock_analysis_results": [],
        "news_analysis_results": [],
        "sec_analysis_results": [],
        "technical_analysis_results": {},
        "risk_analysis_results": {},
        "portfolio_optimization_results": {},
        "debate_results": {},
        "final_report": "",
        "overall_assessment": {},
        "confidence": 0.0,
        "evidence": [],
        "errors": [],
        "warnings": [],
        "completed_agents": [],
        "agent_timings": {},
        "start_time": datetime.now(),
        "end_time": None,
    }
