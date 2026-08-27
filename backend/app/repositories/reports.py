"""Repository for analysis report persistence (optional - see app/database/session.py)"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select

from app.database.session import get_session_factory
from app.models.orm import AgentRun, AnalysisReport

logger = logging.getLogger(__name__)


async def create_report(state: Dict[str, Any]) -> Optional[uuid.UUID]:
    """Persist a completed analysis (report + per-agent timings). Best-effort:
    returns None (and logs) rather than raising if the database isn't available."""
    factory = get_session_factory()
    if factory is None:
        return None

    try:
        async with factory() as session:
            report = AnalysisReport(
                query=state.get("user_query", ""),
                tickers=state.get("tickers", []),
                report_text=state.get("final_report", ""),
                assessment=state.get("overall_assessment", {}),
                errors=state.get("errors", []),
                warnings=state.get("warnings", []),
                debate=state.get("debate_results") or None,
            )
            session.add(report)
            await session.flush()  # populate report.id before building agent_runs

            timings = state.get("agent_timings", {})
            for agent_name in state.get("completed_agents", []):
                session.add(
                    AgentRun(
                        report_id=report.id,
                        agent_name=agent_name,
                        duration_seconds=timings.get(agent_name, 0.0),
                        had_error=any(agent_name in e for e in state.get("errors", [])),
                    )
                )

            await session.commit()
            return report.id
    except Exception as e:
        logger.warning(f"Failed to persist analysis report: {e}")
        return None


async def list_reports(limit: int = 25) -> Optional[List[Dict[str, Any]]]:
    """Return recent reports (summary shape), or None if the database isn't available."""
    factory = get_session_factory()
    if factory is None:
        return None

    try:
        async with factory() as session:
            result = await session.execute(
                select(AnalysisReport).order_by(AnalysisReport.created_at.desc()).limit(limit)
            )
            reports = result.scalars().all()
            return [
                {
                    "id": str(r.id),
                    "query": r.query,
                    "tickers": r.tickers,
                    "overall_outlook": (r.assessment or {}).get("overall_outlook", "Neutral"),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in reports
            ]
    except Exception as e:
        logger.warning(f"Failed to list analysis reports: {e}")
        return None


async def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """Return one report's full detail (with its agent runs), or None if not
    found / the database isn't available."""
    factory = get_session_factory()
    if factory is None:
        return None

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        return None

    try:
        async with factory() as session:
            result = await session.execute(
                select(AnalysisReport).where(AnalysisReport.id == report_uuid)
            )
            report = result.scalar_one_or_none()
            if report is None:
                return None

            runs_result = await session.execute(
                select(AgentRun).where(AgentRun.report_id == report_uuid)
            )
            runs = runs_result.scalars().all()

            return {
                "id": str(report.id),
                "query": report.query,
                "tickers": report.tickers,
                "report": report.report_text,
                "assessment": report.assessment,
                "errors": report.errors,
                "warnings": report.warnings,
                "debate": report.debate,
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "execution": {
                    "completed_agents": [r.agent_name for r in runs],
                    "agent_timings": {r.agent_name: r.duration_seconds for r in runs},
                },
            }
    except Exception as e:
        logger.warning(f"Failed to fetch analysis report {report_id}: {e}")
        return None


async def delete_report(report_id: str) -> bool:
    factory = get_session_factory()
    if factory is None:
        return False

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        return False

    try:
        async with factory() as session:
            result = await session.execute(delete(AnalysisReport).where(AnalysisReport.id == report_uuid))
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.warning(f"Failed to delete analysis report {report_id}: {e}")
        return False
