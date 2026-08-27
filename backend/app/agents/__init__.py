"""Agent System Module"""
from app.agents.base import BaseAgent
from app.agents.final import FinalAnalystAgent
from app.agents.stock import StockAnalysisAgent
from app.agents.supervisor import SupervisorAgent

__all__ = [
    "BaseAgent",
    "SupervisorAgent",
    "StockAnalysisAgent",
    "FinalAnalystAgent",
    "NewsAgent",
    "SECAgent",
    "RiskAgent",
]

# Lazy imports for optional agents
def __getattr__(name):
    if name == "NewsAgent":
        try:
            from app.agents.news import NewsAgent
            return NewsAgent
        except ImportError as e:
            raise AttributeError(f"NewsAgent not available: {e}")
    elif name == "SECAgent":
        try:
            from app.agents.sec import SECAgent
            return SECAgent
        except ImportError as e:
            raise AttributeError(f"SECAgent not available: {e}")
    elif name == "RiskAgent":
        try:
            from app.agents.risk import RiskAgent
            return RiskAgent
        except ImportError as e:
            raise AttributeError(f"RiskAgent not available: {e}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")