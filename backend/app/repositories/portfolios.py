"""Repository for saved-portfolio persistence (optional - see app/database/session.py)"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.session import get_session_factory
from app.models.orm import Portfolio, PortfolioPosition

logger = logging.getLogger(__name__)


async def save_portfolio(name: str, positions: List[Dict[str, Any]], cash: float = 0.0) -> Optional[str]:
    factory = get_session_factory()
    if factory is None:
        return None

    try:
        async with factory() as session:
            portfolio = Portfolio(name=name or "My Portfolio", cash=cash)
            session.add(portfolio)
            await session.flush()

            for p in positions:
                session.add(
                    PortfolioPosition(portfolio_id=portfolio.id, ticker=p["ticker"], weight=p["weight"])
                )

            await session.commit()
            return str(portfolio.id)
    except Exception as e:
        logger.warning(f"Failed to save portfolio: {e}")
        return None


async def list_portfolios() -> Optional[List[Dict[str, Any]]]:
    factory = get_session_factory()
    if factory is None:
        return None

    try:
        async with factory() as session:
            result = await session.execute(
                select(Portfolio).options(selectinload(Portfolio.positions)).order_by(Portfolio.created_at.desc())
            )
            portfolios = result.scalars().all()
            return [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "cash": p.cash,
                    "positions": [{"ticker": pos.ticker, "weight": pos.weight} for pos in p.positions],
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in portfolios
            ]
    except Exception as e:
        logger.warning(f"Failed to list portfolios: {e}")
        return None
