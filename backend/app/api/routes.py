"""API Route Definitions"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import (
    get_company_service,
    get_llm_provider,
    get_portfolio_optimizer,
    get_risk_service,
    get_workflow,
)
from app.config.settings import settings
from app.core.json_utils import sanitize_for_json
from app.llm.provider import LLMProvider
from app.models.portfolio import Portfolio, Position
from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    CompanyInfo,
    HealthResponse,
    PortfolioAnalyzeRequest,
    PortfolioOptimizeRequest,
    SavePortfolioRequest,
    Source,
)
from app.repositories import portfolios as portfolios_repo
from app.repositories import reports as reports_repo
from app.services.company_service import CompanyService
from app.services.risk_service import RiskService
from app.tools.portfolio import PortfolioOptimizer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="operational",
        service="FinAgent API",
        version=settings.VERSION,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    llm_provider: LLMProvider = Depends(get_llm_provider),
):
    """Quick, single-shot LLM analysis with no tool use. For real multi-agent
    analysis grounded in market/news/SEC/risk data, use /analyze/stream or /analyze/agent."""
    try:
        logger.info(f"Quick analysis request: {request.query}")

        system_prompt = """You are FinAgent, a financial analysis platform.
        Be concise and informative. This is a quick, ungrounded response - make clear
        you have not looked at live data, and suggest the user run a full analysis for that.
        """

        response = await llm_provider.generate(
            prompt=request.query,
            system_prompt=system_prompt,
        )

        if not response.success:
            raise HTTPException(status_code=502, detail=f"LLM error: {response.error}")

        return AnalyzeResponse(
            query=request.query,
            analysis=response.content,
            confidence=0.5,
            sources=[Source(name="Groq LLM (no tools)", type="api", url="https://groq.com")],
            warnings=["This is a quick response with no live data lookup."],
            disclaimer="This is an informational analysis, not financial advice.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/agent")
async def analyze_with_agents(request: AnalyzeRequest, workflow=Depends(get_workflow)):
    """Run the full multi-agent workflow and return the complete result (non-streaming)."""
    try:
        logger.info(f"Agent analysis request: {request.query}")
        result = await workflow.run(request.query, debate=request.debate)
        report_id = await reports_repo.create_report(result)
        return _format_agent_result(request.query, result, report_id)
    except Exception as e:
        logger.error(f"Agent analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/stream")
async def analyze_stream(request: AnalyzeRequest, workflow=Depends(get_workflow)):
    """Run the full multi-agent workflow, streaming per-agent progress as Server-Sent Events.

    Event types:
      - agent_started / agent_completed: {"agent": "...", "errors": [...], "warnings": [...]}
      - done: {"result": <same shape as /analyze/agent>}
      - error: {"message": "..."}
    """
    query = request.query
    debate = request.debate

    async def event_stream():
        yield _sse("agent_started", {"agent": "Supervisor"})
        try:
            async for event in workflow.stream(query, debate=debate):
                if event["type"] == "agent_completed":
                    yield _sse("agent_completed", {
                        "agent": event["agent"],
                        "errors": event.get("errors", []),
                        "warnings": event.get("warnings", []),
                    })
                elif event["type"] == "done":
                    report_id = await reports_repo.create_report(event["state"])
                    result = _format_agent_result(query, event["state"], report_id)
                    yield _sse("done", {"result": result})
        except Exception as e:
            logger.error(f"Stream failed: {e}")
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(sanitize_for_json(data), default=str)}\n\n"


def _format_agent_result(query: str, state: dict, report_id=None) -> dict:
    """Shape the LangGraph final state into the API response payload."""
    return sanitize_for_json({
        "id": str(report_id) if report_id else None,
        "query": query,
        "report": state.get("final_report", "No report generated"),
        "assessment": state.get("overall_assessment", {}),
        "tickers": state.get("tickers", []),
        "stock_analysis": state.get("stock_analysis_results", []),
        "technical_analysis": state.get("technical_analysis_results", {}),
        "news_analysis": state.get("news_analysis_results", []),
        "risk_analysis": state.get("risk_analysis_results", {}),
        "sec_analysis": state.get("sec_analysis_results", []),
        "debate": state.get("debate_results") or None,
        "execution": {
            "completed_agents": state.get("completed_agents", []),
            "agent_timings": state.get("agent_timings", {}),
        },
        "errors": state.get("errors", []),
        "warnings": state.get("warnings", []),
        "disclaimer": "This is an informational analysis, not financial advice.",
    })


@router.get("/companies/{ticker}", response_model=CompanyInfo)
async def get_company_info(
    ticker: str,
    company_service: CompanyService = Depends(get_company_service),
):
    """Get real company information (yfinance, with Alpha Vantage fallback if configured)."""
    info = await company_service.get_company_info(ticker)

    if info.get("error"):
        raise HTTPException(status_code=404, detail=f"No data found for ticker '{ticker.upper()}'")

    return CompanyInfo(
        ticker=info.get("ticker", ticker.upper()),
        name=info.get("name"),
        exchange=info.get("exchange"),
        sector=info.get("sector"),
        industry=info.get("industry"),
        country=info.get("country"),
        market_cap=info.get("market_cap"),
        pe_ratio=info.get("pe_ratio"),
        description=f"Data source: {info.get('source', 'unknown')}, updated {info.get('updated_at', 'unknown')}",
    )


@router.get("/market/{ticker}/chart")
async def get_chart_series(
    ticker: str,
    period: str = "6mo",
    company_service: CompanyService = Depends(get_company_service),
):
    """Compact historical series (close, SMA20/50, RSI, MACD histogram) for charting."""
    from app.tools.technical import TechnicalAnalyzer

    history = await company_service.get_historical_data(ticker, period=period)
    if history.empty:
        raise HTTPException(status_code=404, detail=f"No historical data available for '{ticker.upper()}'")

    series = TechnicalAnalyzer.chart_series(history)
    return sanitize_for_json({"ticker": ticker.upper(), "period": period, "series": series})


@router.post("/portfolio/analyze")
async def analyze_portfolio(
    request: PortfolioAnalyzeRequest,
    risk_service: RiskService = Depends(get_risk_service),
):
    """Calculate risk metrics (volatility, VaR/CVaR, Sharpe, drawdown, correlation) for a portfolio."""
    weights = {p.ticker: p.weight for p in request.positions}

    try:
        returns_data = await risk_service.get_historical_returns(list(weights.keys()))
        if returns_data.empty:
            raise HTTPException(status_code=422, detail="No historical price data available for these tickers")

        metrics = await risk_service.calculate_risk_metrics(weights=weights, returns_data=returns_data)

        portfolio = Portfolio(
            positions=[Position(ticker=t, weight=w) for t, w in weights.items()],
            cash=request.cash,
        )
        simulation = await risk_service.monte_carlo_simulation(portfolio=portfolio, num_simulations=500)

        return sanitize_for_json({
            "weights": weights,
            "metrics": metrics.model_dump(),
            "simulation": simulation,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/optimize")
async def optimize_portfolio(
    request: PortfolioOptimizeRequest,
    risk_service: RiskService = Depends(get_risk_service),
    optimizer: PortfolioOptimizer = Depends(get_portfolio_optimizer),
):
    """Recommend portfolio weights for maximum Sharpe ratio or minimum volatility."""
    tickers = [p.ticker for p in request.positions]
    current_weights = {p.ticker: p.weight for p in request.positions}

    try:
        returns_data = await risk_service.get_historical_returns(tickers)
        if returns_data.empty or len(returns_data.columns) < 2:
            raise HTTPException(
                status_code=422,
                detail="Not enough overlapping historical data to optimize this portfolio",
            )

        constraints = {"max_weight": request.max_weight} if request.max_weight else None

        if request.method == "min_volatility":
            result = optimizer.optimize_min_volatility(returns_data, constraints=constraints)
        else:
            result = optimizer.optimize_max_sharpe(returns_data, constraints=constraints)

        comparison = optimizer.compare_portfolios(current_weights, result.recommended_weights, returns_data)

        return sanitize_for_json({"optimization": result.model_dump(), "comparison": comparison})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports")
async def list_reports(limit: int = 25):
    """List recent persisted analysis reports (requires DATABASE_URL to be configured)."""
    reports = await reports_repo.list_reports(limit=limit)
    if reports is None:
        raise HTTPException(status_code=503, detail="Report history is unavailable: no database configured")
    return {"reports": reports}


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Fetch one persisted analysis report in full (same shape as /analyze/agent)."""
    report = await reports_repo.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    report["disclaimer"] = "This is an informational analysis, not financial advice."
    return sanitize_for_json(report)


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    """Delete one persisted analysis report."""
    deleted = await reports_repo.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return {"deleted": True}


@router.post("/portfolios")
async def create_saved_portfolio(request: SavePortfolioRequest):
    """Save a portfolio definition for later reuse (requires DATABASE_URL to be configured)."""
    positions = [{"ticker": p.ticker, "weight": p.weight} for p in request.positions]
    portfolio_id = await portfolios_repo.save_portfolio(request.name, positions, request.cash)
    if portfolio_id is None:
        raise HTTPException(status_code=503, detail="Saving portfolios is unavailable: no database configured")
    return {"id": portfolio_id}


@router.get("/portfolios")
async def get_saved_portfolios():
    """List saved portfolios (requires DATABASE_URL to be configured)."""
    portfolios = await portfolios_repo.list_portfolios()
    if portfolios is None:
        raise HTTPException(status_code=503, detail="Saved portfolios are unavailable: no database configured")
    return {"portfolios": portfolios}
