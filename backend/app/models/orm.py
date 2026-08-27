"""SQLAlchemy ORM models (Postgres persistence layer).

Single-tenant, no auth: rows aren't scoped to a user. Scope is deliberately
narrow - only what has nowhere else to live. Live market/news data stays in
Redis (short-lived cache, not a historical record) and SEC filing chunks stay
in Qdrant (vector data belongs in a vector store) - persisting either again
here would just be duplicated, unused state.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[uuid.UUID] = _uuid_pk()
    query: Mapped[str] = mapped_column(Text)
    tickers: Mapped[list] = mapped_column(JSONB, default=list)
    report_text: Mapped[str] = mapped_column(Text)
    assessment: Mapped[dict] = mapped_column(JSONB, default=dict)
    errors: Mapped[list] = mapped_column(JSONB, default=list)
    warnings: Mapped[list] = mapped_column(JSONB, default=list)
    debate: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = _now()

    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_analysis_reports_created_at", "created_at"),)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_reports.id", ondelete="CASCADE"))
    agent_name: Mapped[str] = mapped_column(String(64))
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    had_error: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = _now()

    report: Mapped["AnalysisReport"] = relationship(back_populates="agent_runs")

    __table_args__ = (Index("ix_agent_runs_report_id", "report_id"),)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(120), default="My Portfolio")
    cash: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = _now()

    positions: Mapped[list["PortfolioPosition"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    portfolio_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"))
    ticker: Mapped[str] = mapped_column(String(12))
    weight: Mapped[float] = mapped_column(Float)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")

    __table_args__ = (Index("ix_portfolio_positions_portfolio_id", "portfolio_id"),)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    dataset_name: Mapped[str] = mapped_column(String(120))
    case_name: Mapped[str] = mapped_column(String(200))
    query: Mapped[str] = mapped_column(Text)
    passed: Mapped[bool] = mapped_column(default=False)
    latency_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = _now()

    __table_args__ = (Index("ix_evaluation_runs_created_at", "created_at"),)
