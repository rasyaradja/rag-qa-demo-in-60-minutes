"""
SQLAlchemy models for evaluation sets and evaluation results.

- EvalSet: Stores a named set of evaluation questions and gold answers.
- EvalResult: Stores the result of running a query from an EvalSet through the RAG pipeline, including faithfulness, relevance, safety, latency, and cost metrics.

Dependencies:
- SQLAlchemy 2.0 (async)
- PostgreSQL (UUID, JSON, ARRAY)
- models.document and models.query for FK references

"""

import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

Base = declarative_base()

class EvalSet(Base):
    """
    Evaluation set containing a list of questions and gold answers.

    Fields:
        id: UUID primary key.
        name: Human-readable name for the eval set.
        questions: JSON list of dicts (each with 'question', 'gold_answer', etc).
        created_at: Timestamp of creation.
    """
    __tablename__ = "eval_sets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(length=128), nullable=False, unique=True)
    questions: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    results: Mapped[list["EvalResult"]] = relationship(
        "EvalResult",
        back_populates="eval_set",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<EvalSet(id={self.id}, name={self.name!r})>"

class EvalResult(Base):
    """
    Stores the result of evaluating a single query from an EvalSet.

    Fields:
        id: UUID primary key.
        eval_set_id: FK to EvalSet.
        query_id: FK to UserQuery (the query run for this eval).
        faithfulness: Float (0-1), how well answer aligns with sources.
        relevance: Float (0-1), how well answer addresses the question.
        safety_flag: Boolean, True if answer is unsafe or refused.
        latency_ms: Integer, time taken to answer (ms).
        cost_usd: Float, estimated API cost in USD.
        created_at: Timestamp of result creation.
    """
    __tablename__ = "eval_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    eval_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("eval_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("user_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    faithfulness: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    relevance: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    safety_flag: Mapped[Optional[bool]] = mapped_column(sa.Boolean, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    eval_set: Mapped["EvalSet"] = relationship(
        "EvalSet",
        back_populates="results",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return (
            f"<EvalResult(id={self.id}, eval_set_id={self.eval_set_id}, "
            f"query_id={self.query_id}, faithfulness={self.faithfulness}, "
            f"relevance={self.relevance}, safety_flag={self.safety_flag})>"
        )
