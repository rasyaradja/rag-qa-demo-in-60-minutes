"""
SQLAlchemy model for user queries and answers in the RAG Q&A Demo.

- Represents a user-submitted question, the generated answer, citations, and metadata.
- Tracks status (answered, refused, error), LLM model, prompt version, and timestamps.
- Citations are stored as a list of Document UUIDs (ARRAY[UUID]).
- Used for logging, provenance, and evaluation linkage.

Dependencies:
- SQLAlchemy 2.0 (async)
- PostgreSQL (UUID, ARRAY)
- models.document for citation references
"""

import uuid
from datetime import datetime
from typing import Optional, List

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

Base = declarative_base()

class UserQuery(Base):
    """
    User-submitted query and answer record.

    Fields:
        id: UUID primary key.
        question: The user question (input).
        answer: The generated answer (output).
        citations: List of Document UUIDs referenced in the answer.
        created_at: Timestamp of query submission.
        status: Enum('answered', 'refused', 'error').
        llm_model: LLM model used for answer generation.
        prompt_version: Prompt template version used.
    """
    __tablename__ = "user_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    question: Mapped[str] = mapped_column(sa.Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    citations: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    status: Mapped[str] = mapped_column(
        sa.Enum("answered", "refused", "error", name="query_status"),
        nullable=False,
        default="answered",
        server_default="answered",
    )
    llm_model: Mapped[Optional[str]] = mapped_column(sa.String(length=64), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(sa.String(length=32), nullable=True)

    # Relationships (optional, for ORM navigation)
    # Documents referenced in citations (not a true FK, but can be joined manually)
    # Evaluation results (one-to-many, via EvalResult.query_id)
    eval_results: Mapped[List["EvalResult"]] = relationship(
        "EvalResult",
        back_populates="user_query",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"<UserQuery(id={self.id}, status={self.status}, "
            f"llm_model={self.llm_model}, prompt_version={self.prompt_version})>"
        )
