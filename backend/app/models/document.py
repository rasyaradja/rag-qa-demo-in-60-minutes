"""
SQLAlchemy model for source documents and their embeddings.

- Represents curated source documents ingested into the RAG system.
- Stores title, content, embedding vector, and optional source URL.
- Embedding is stored as a NumPy array (PostgreSQL: BYTEA or ARRAY[float]).
- Used for retrieval, citation, and provenance tracking.

Dependencies:
- SQLAlchemy 2.0 (async)
- PostgreSQL (ARRAY or BYTEA for embeddings)
"""

import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

Base = declarative_base()

class Document(Base):
    """
    Source document model for RAG Q&A Demo.

    Fields:
        id: UUID primary key.
        title: Short title or label for the document.
        content: Full text content of the document.
        embedding: Vector embedding (list of floats).
        source_url: Optional URL or citation for provenance.
        created_at: Timestamp of ingestion.
    """
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    title: Mapped[str] = mapped_column(sa.String(length=256), nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        ARRAY(sa.Float), nullable=True
    )
    source_url: Mapped[Optional[str]] = mapped_column(sa.String(length=512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title!r})>"
