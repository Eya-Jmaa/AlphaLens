"""API Dependencies"""
from functools import lru_cache

from app.config.settings import settings
from app.llm import GroqProvider, LLMConfig
from app.services.company_service import CompanyService
from app.services.risk_service import RiskService
from app.tools.portfolio import PortfolioOptimizer


@lru_cache()
def get_llm_provider():
    """Get or create LLM provider instance"""
    if not settings.GROQ_API_KEY:
        from app.core.exceptions import LLMException
        raise LLMException("GROQ_API_KEY not configured")

    config = LLMConfig(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=settings.GROQ_TEMPERATURE,
        max_tokens=settings.GROQ_MAX_TOKENS,
        timeout=settings.GROQ_TIMEOUT,
    )

    return GroqProvider(config)


@lru_cache()
def get_company_service() -> CompanyService:
    return CompanyService()


@lru_cache()
def get_risk_service() -> RiskService:
    return RiskService()


@lru_cache()
def get_portfolio_optimizer() -> PortfolioOptimizer:
    return PortfolioOptimizer()


@lru_cache()
def get_workflow():
    """Get or create the (expensive-to-build) LangGraph workflow, once per process.

    Building it constructs every specialized agent, including the SEC agent's
    embedding model + vector store connection, so this must not happen per-request.
    """
    from app.graph.workflow import AlphaLensWorkflow
    return AlphaLensWorkflow(get_llm_provider(), get_company_service())
