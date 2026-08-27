"""Tests for the LangGraph-based multi-agent workflow"""
from unittest.mock import AsyncMock, patch

import pytest

from app.graph.workflow import FinAgentWorkflow
from app.llm.provider import LLMResponse


def _mock_llm_provider(responses):
    """A fake LLMProvider whose .generate() returns each response in sequence."""
    provider = AsyncMock()
    provider.generate = AsyncMock(side_effect=[
        LLMResponse(content=r, model="test-model", usage={}, metadata={}, success=True)
        for r in responses
    ])
    return provider


@pytest.mark.asyncio
async def test_workflow_stock_only_run():
    """A plain ticker query should route through Supervisor -> StockAnalysis -> FinalAnalyst."""
    responses = [
        # StockAnalysis's _analyze_company call
        '{"summary": "Apple is financially healthy with strong revenue growth."}',
        # FinalAnalyst's structured synthesis call
        (
            '{"executive_summary": "Apple looks healthy.", "fundamental_analysis": "Strong revenue.", '
            '"news_sentiment": "Insufficient recent news data.", "sec_insights": "No SEC filing evidence available.", '
            '"technical_analysis": "No technical data available.", "risk_analysis": "No risk data available.", '
            '"strengths": ["Strong revenue growth"], "risks": ["Valuation risk"], '
            '"key_uncertainties": ["Macro conditions"], "overall_outlook": "Positive", "confidence": 0.8}'
        ),
    ]
    llm = _mock_llm_provider(responses)

    company_service = AsyncMock()
    company_service.get_company_info = AsyncMock(return_value={
        "name": "Apple Inc.", "sector": "Technology", "market_cap": 3_000_000_000_000, "pe_ratio": 30,
    })
    company_service.get_market_data = AsyncMock(return_value={"technical": {}, "returns": {}, "risk": {}})

    with patch("app.graph.workflow._load_news_agent", return_value=None), \
         patch("app.graph.workflow._load_risk_agent", return_value=None), \
         patch("app.graph.workflow._load_sec_agent", return_value=None):
        workflow = FinAgentWorkflow(llm, company_service)
        result = await workflow.run("Analyze AAPL")

    assert result["tickers"] == ["AAPL"]
    assert "StockAnalysis" in result["completed_agents"]
    assert "FinalAnalyst" in result["completed_agents"]
    assert "NewsAnalysis" not in result["completed_agents"]
    assert result["overall_assessment"]["overall_outlook"] == "Positive"
    assert "Apple looks healthy" in result["final_report"]
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_workflow_no_ticker_query_skips_specialized_agents():
    """A query with no resolvable ticker should still complete via FinalAnalyst,
    with an empty-evidence result rather than crashing."""
    llm = _mock_llm_provider(["NONE"])  # supervisor's LLM ticker-extraction fallback

    with patch("app.graph.workflow._load_news_agent", return_value=None), \
         patch("app.graph.workflow._load_risk_agent", return_value=None), \
         patch("app.graph.workflow._load_sec_agent", return_value=None):
        workflow = FinAgentWorkflow(llm)
        result = await workflow.run("What is a stock market?")

    assert result["tickers"] == []
    assert result["completed_agents"] == ["Supervisor", "FinalAnalyst"]
    assert result["overall_assessment"]["overall_outlook"] == "Insufficient Evidence"


@pytest.mark.asyncio
async def test_workflow_debate_mode_stream_completes_without_crashing():
    """Debate mode fans out through EvidenceJoin -> [BullCase, BearCase] -> Judge ->
    FinalAnalyst. This regression-tests the streaming path specifically: LangGraph
    reports a structural no-op node's (EvidenceJoin's) update as None rather than
    an empty dict, which previously crashed the stream's manual state accumulation."""
    responses = [
        '{"summary": "Apple is financially healthy."}',  # StockAnalysis
        "Bull thesis: strong fundamentals.",  # BullCase or BearCase - order between them is not deterministic
        "Bear thesis: valuation risk.",  # (parallel branch), but both are plain text so order doesn't matter
        (
            '{"stronger_case": "bull", "reasoning": "Bull case cited more concrete figures.", '
            '"key_disagreements": [], "unresolved_uncertainty": [], "confidence": 0.6}'
        ),  # Judge - always runs after both Bull and Bear, so its slot is deterministic
        (
            '{"executive_summary": "Apple looks healthy.", "fundamental_analysis": "Strong revenue.", '
            '"news_sentiment": "Insufficient recent news data.", "sec_insights": "No SEC filing evidence available.", '
            '"technical_analysis": "No technical data available.", "risk_analysis": "No risk data available.", '
            '"debate_summary": "The evidence favors the bull case.", '
            '"strengths": ["Strong revenue growth"], "risks": ["Valuation risk"], '
            '"key_uncertainties": ["Macro conditions"], "overall_outlook": "Positive", "confidence": 0.7}'
        ),  # FinalAnalyst
    ]
    llm = _mock_llm_provider(responses)

    company_service = AsyncMock()
    company_service.get_company_info = AsyncMock(return_value={
        "name": "Apple Inc.", "sector": "Technology", "market_cap": 3_000_000_000_000, "pe_ratio": 30,
    })
    company_service.get_market_data = AsyncMock(return_value={"technical": {}, "returns": {}, "risk": {}})

    with patch("app.graph.workflow._load_news_agent", return_value=None), \
         patch("app.graph.workflow._load_risk_agent", return_value=None), \
         patch("app.graph.workflow._load_sec_agent", return_value=None):
        workflow = FinAgentWorkflow(llm, company_service)

        events = [event async for event in workflow.stream("bull and bear case for AAPL", debate=True)]

    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) == 1
    final_state = done_events[0]["state"]

    assert final_state["errors"] == []
    for agent in ("Supervisor", "StockAnalysis", "BullCase", "BearCase", "Judge", "FinalAnalyst"):
        assert agent in final_state["completed_agents"]

    debate_results = final_state["debate_results"]
    assert debate_results["bull_case"] and debate_results["bear_case"]
    assert debate_results["verdict"]["stronger_case"] == "bull"
    assert "Bull vs. Bear Debate" in final_state["final_report"]
