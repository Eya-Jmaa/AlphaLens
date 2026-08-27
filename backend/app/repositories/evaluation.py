"""Repository for evaluation-run persistence (optional - see app/database/session.py)"""
import logging
from typing import Any, Dict, Optional

from app.database.session import get_session_factory
from app.models.orm import EvaluationRun

logger = logging.getLogger(__name__)


async def record_evaluation_run(
    dataset_name: str,
    case_name: str,
    query: str,
    passed: bool,
    latency_seconds: float,
    details: Optional[Dict[str, Any]] = None,
) -> bool:
    """Persist one evaluation case's outcome. Returns False (and logs) rather
    than raising if the database isn't available - the eval run itself still
    completes and prints its summary either way."""
    factory = get_session_factory()
    if factory is None:
        return False

    try:
        async with factory() as session:
            session.add(
                EvaluationRun(
                    dataset_name=dataset_name,
                    case_name=case_name,
                    query=query,
                    passed=passed,
                    latency_seconds=latency_seconds,
                    details=details or {},
                )
            )
            await session.commit()
            return True
    except Exception as e:
        logger.warning(f"Failed to persist evaluation run '{case_name}': {e}")
        return False
