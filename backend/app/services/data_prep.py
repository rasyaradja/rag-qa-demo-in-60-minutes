"""
Service for preparing and ingesting source documents and embeddings.

- Loads curated source documents from markdown or JSON.
- Splits documents into chunks, generates embeddings, and stores in DB and vector store.
- Ensures idempotent ingestion (no duplicate documents).
- Used for initial setup and re-indexing.
"""

import os
import uuid
import logging
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError

from ..core.config import settings
from ..core.embeddings import get_embedding_model, EmbeddingModel
from ..core.vectorstore import get_vectorstore, VectorStore
from ..models.document import Document
from ..core.prompts import load_prompt_template

import aiofiles

logger = logging.getLogger("data_prep")
CHUNK_SIZE = 512  # tokens or chars, depending on model
CHUNK_OVERLAP = 64

def _split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Naive text splitter: splits text into overlapping chunks.
    """
    if not text:
        return []
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == length:
            break
        start = end - overlap
    return chunks

async def _load_markdown_sources(md_path: str) -> List[dict]:
    """
    Loads and parses a markdown file with source documents.
    Each document is separated by '---' and may have a title and optional source_url.
    Example format:
    ---
    title: Document Title
    source_url: https://example.com
    Content of the document...
    ---
    """
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Source markdown file not found: {md_path}")

    async with aiofiles.open(md_path, "r", encoding="utf-8") as f:
        content = await f.read()

    docs = []
    raw_docs = [d.strip() for d in content.split('---') if d.strip()]
    for raw in raw_docs:
        lines = raw.splitlines()
        title = None
        source_url = None
        body_lines = []
        for line in lines:
            if line.lower().startswith("title:"):
                title = line[len("title:"):].strip()
            elif line.lower().startswith("source_url:"):
                source_url = line[len("source_url:"):].strip()
            else:
                body_lines.append(line)
        body = "\n".join(body_lines).strip()
        if not body:
            continue
        docs.append({
            "title": title or "Untitled",
            "content": body,
            "source_url": source_url,
        })
    return docs

async def ingest_documents(
    db: AsyncSession,
    vectorstore: Optional[VectorStore] = None,
    embedding_model: Optional[EmbeddingModel] = None,
    sources_path: Optional[str] = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> Tuple[int, int]:
    """
    Ingests documents from the curated sources file, splits into chunks, embeds, and stores.

    Returns:
        (num_documents, num_chunks)
    """
    sources_path = sources_path or settings.SOURCES_PATH
    if not sources_path:
        raise ValueError("No sources_path provided or configured.")

    logger.info(f"Loading source documents from: {sources_path}")
    docs = await _load_markdown_sources(sources_path)
    logger.info(f"Loaded {len(docs)} source documents.")

    if embedding_model is None:
        embedding_model = get_embedding_model()
    if vectorstore is None:
        vectorstore = get_vectorstore()

    num_docs_ingested = 0
    num_chunks_ingested = 0

    for doc in docs:
        # Check if document already exists (by title and content hash)
        stmt = select(Document).where(
            Document.title == doc["title"],
            Document.content == doc["content"]
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            logger.info(f"Document already ingested: {doc['title']}")
            continue

        # Split into chunks
        chunks = _split_text(doc["content"], chunk_size, chunk_overlap)
        chunk_ids = []
        for idx, chunk in enumerate(chunks):
            chunk_id = uuid.uuid4()
            embedding = await embedding_model.embed_text(chunk)
            # Insert into DB
            db_doc = Document(
                id=chunk_id,
                title=doc["title"],
                content=chunk,
                embedding=embedding,
                source_url=doc.get("source_url"),
            )
            db.add(db_doc)
            try:
                await db.flush()
            except IntegrityError:
                logger.warning(f"Duplicate chunk skipped: {doc['title']} [{idx}]")
                continue
            # Add to vectorstore
            await vectorstore.add_embedding(
                doc_id=str(chunk_id),
                embedding=embedding,
                metadata={
                    "title": doc["title"],
                    "source_url": doc.get("source_url"),
                    "chunk_index": idx,
                }
            )
            chunk_ids.append(chunk_id)
            num_chunks_ingested += 1

        await db.commit()
        logger.info(f"Ingested document '{doc['title']}' with {len(chunk_ids)} chunks.")
        num_docs_ingested += 1

    logger.info(f"Ingestion complete: {num_docs_ingested} documents, {num_chunks_ingested} chunks.")
    return num_docs_ingested, num_chunks_ingested

async def reindex_vectorstore(
    db: AsyncSession,
    vectorstore: Optional[VectorStore] = None,
    embedding_model: Optional[EmbeddingModel] = None,
) -> int:
    """
    Rebuilds the vectorstore from all documents in the DB.
    Useful if switching vector DB backends or after schema changes.

    Returns:
        Number of chunks re-indexed.
    """
    if vectorstore is None:
        vectorstore = get_vectorstore()
    if embedding_model is None:
        embedding_model = get_embedding_model()

    stmt = select(Document)
    result = await db.execute(stmt)
    docs = result.scalars().all()
    logger.info(f"Re-indexing {len(docs)} document chunks into vectorstore.")

    await vectorstore.clear()  # Remove all existing vectors

    count = 0
    for doc in docs:
        # Re-embed if missing
        embedding = doc.embedding
        if embedding is None:
            embedding = await embedding_model.embed_text(doc.content)
        await vectorstore.add_embedding(
            doc_id=str(doc.id),
            embedding=embedding,
            metadata={
                "title": doc.title,
                "source_url": doc.source_url,
            }
        )
        count += 1
    logger.info(f"Re-indexed {count} chunks into vectorstore.")
    return count

async def list_ingested_documents(db: AsyncSession) -> List[dict]:
    """
    Returns a list of all ingested documents (titles, ids, chunk counts).
    """
    stmt = select(Document.title, Document.source_url)
    result = await db.execute(stmt)
    rows = result.all()
    docs = {}
    for title, source_url in rows:
        key = (title, source_url)
        docs.setdefault(key, 0)
        docs[key] += 1
    return [
        {"title": title, "source_url": source_url, "num_chunks": count}
        for (title, source_url), count in docs.items()
    ]
