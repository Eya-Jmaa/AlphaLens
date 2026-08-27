"""Services Module"""
from app.services.cache_service import CacheService
from app.services.company_service import CompanyService
from app.services.market_service import MarketService
from app.services.news_service import NewsService
from app.services.risk_service import RiskService

# SEC service pulls in requests/bs4 which are core deps, but keep it optional
# defensively since SEC analysis is allowed to degrade gracefully.
try:
    from app.services.sec_service import SECService
except ImportError:
    SECService = None

__all__ = [
    "CompanyService",
    "MarketService",
    "CacheService",
    "NewsService",
    "RiskService",
    "SECService",
]