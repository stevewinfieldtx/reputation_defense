import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Audit(Base):
    """One reputation audit run. Collected data, analysis and revenue math are
    stored as JSON so the report can be re-rendered at any time without re-spending
    on APIs."""

    __tablename__ = "audits"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|collecting|analyzing|complete|error
    demo: Mapped[bool] = mapped_column(Boolean, default=False)

    business_name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(200))
    vertical: Mapped[str] = mapped_column(String(50), default="default")
    avg_transaction: Mapped[float | None] = mapped_column(Float, nullable=True)
    monthly_customers: Mapped[float | None] = mapped_column(Float, nullable=True)
    competitors: Mapped[list] = mapped_column(JSON, default=list)  # names typed at intake

    business_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # profile + reviews
    competitor_data: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{profile, reviews}, ...]
    analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)         # LLM output (validated)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)          # python-computed stats
    revenue: Mapped[dict | None] = mapped_column(JSON, nullable=True)          # calculator output

    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
