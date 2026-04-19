"""
Core RAG pipeline: retrieval, prompt construction, LLM call, citation extraction, safety checks.

- Embeds user question.
- Retrieves relevant documents from vector DB (FAISS/Pinecone).
- Constructs prompt using selected template and retrieved context.
- Calls LLM API (OpenAI, Anthropic, HF Llama).
- Extracts citations from answer.
- Applies safety/refusal policy.
- Returns structured answer with citations and metadata.

Used by /api/v1/rag/answer and evaluation pipeline.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.config import settings
from ..core.embeddings import get_embedding_model
from ..core.vectorstore import get_vectorstore
from ..core.prompts import get_prompt_template, get_prompt_version
from ..core.llm import get_llm_client
from ..models.document import Document
from ..models.query import UserQuery
from ..schemas.rag import (
    RAGAnswerOut,
    RAGRefusalOut,
    RAGAnswerRequest,
    Citation,
)
from ..schemas.base import ErrorResponse

logger = logging.getLogger("rag_service")

# --- Safety/Refusal Policy ---

UNSAFE_KEYWORDS = [
    "suicide", "self-harm", "violence", "kill", "murder", "attack",
    "illegal", "crime", "hack", "explosive", "terror", "abuse", "porn",
    "sexual", "drugs", "weapon", "bomb", "racist", "hate", "harass",
    "nazi", "extremist", "child abuse", "molest", "assault", "shoot",
    "overthrow", "fraud", "scam", "phishing", "malware", "virus",
    "execute", "shell", "root", "admin password", "bypass", "exploit",
    "cheat", "cheating", "cheatsheet", "cheat code",
]
OUT_OF_SCOPE_KEYWORDS = [
    "weather", "sports", "celebrity", "joke", "stock price", "bitcoin",
    "horoscope", "astrology", "lottery", "gambling", "betting",
    "personal advice", "medical advice", "diagnosis", "prescription",
    "therapy", "fortune", "future", "prediction", "relationship",
    "dating", "love life", "marriage", "divorce", "tax advice",
    "investment advice", "legal advice", "lawyer", "attorney",
    "court case", "lawsuit", "patent", "copyright", "trademark",
    "politics", "election", "vote", "president", "prime minister",
    "government", "conspiracy", "classified", "secret",
]

REFUSAL_MESSAGE = (
    "I'm sorry, but I cannot answer that question. "
    "Please ask about topics covered in the provided documents."
)

def is_unsafe_question(question: str) -> bool:
    q = question.lower()
    for kw in UNSAFE_KEYWORDS:
        if kw in q:
            return True
    return False

def is_out_of_scope(question: str) -> bool:
    q = question.lower()
    for kw in OUT_OF_SCOPE_KEYWORDS:
        if kw in q:
            return True
    return False

def should_refuse(question: str) -> Optional[str]:
    if is_unsafe_question(question):
        return (
            "Your question contains unsafe or prohibited content. "
            "For safety reasons, I cannot answer."
        )
    if is_out_of_scope(question):
        return (
            "Your question appears to be out of scope for this assistant. "
            "Please ask about topics covered in the provided documents."
        )
    if not question.strip():
        return "Please enter a non-empty question."
    if len(question.strip()) < 3:
        return "Your question is too short to answer meaningfully."
    return None

# --- Retrieval ---

async def retrieve_relevant_chunks(
    db: AsyncSession,
    question: str,
    top_k: int = 4,
    embedding_model=None,
    vectorstore=None,
) -> List[Dict[str, Any]]:
    """
    Embeds the question and retrieves top_k relevant document chunks from the vector store.
    Returns a list of dicts: {document_id, title, content, source_url, score}
    """
    if embedding_model is None:
        embedding_model = get_embedding_model()
    if vectorstore is None:
        vectorstore = get_vectorstore()
    query_embedding = await embedding_model.embed_text(question)
    results = await vectorstore.similarity_search(query_embedding, top_k=top_k)
    # Each result: {doc_id, score, metadata}
    doc_ids = [uuid.UUID(r["doc_id"]) for r in results]
    # Fetch from DB for full content
    stmt = select(Document).where(Document.id.in_(doc_ids))
    db_result = await db.execute(stmt)
    docs = {d.id: d for d in db_result.scalars().all()}
    out = []
    for r in results:
        doc_id = uuid.UUID(r["doc_id"])
        doc = docs.get(doc_id)
        if not doc:
            continue
        out.append({
            "document_id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "source_url": doc.source_url,
            "score": r.get("score"),
        })
    return out

# --- Prompt Construction ---

def build_rag_prompt(
    question: str,
    context_chunks: List[Dict[str, Any]],
    prompt_version: Optional[str] = None,
) -> str:
    """
    Constructs the RAG prompt using the selected template and retrieved context.
    """
    prompt_template = get_prompt_template(prompt_version)
    # Format context as concatenated chunks with titles
    context_strs = []
    for idx, chunk in enumerate(context_chunks):
        title = chunk.get("title") or f"Document {idx+1}"
        content = chunk.get("content") or ""
        context_strs.append(f"[{title}]\n{content}")
    context_block = "\n\n".join(context_strs)
    prompt = prompt_template.format(context=context_block, question=question)
    return prompt

# --- Citation Extraction ---

def extract_citations_from_answer(
    answer: str,
    context_chunks: List[Dict[str, Any]],
) -> List[Citation]:
    """
    Naive citation extraction: if answer contains a chunk's title or unique phrase, cite it.
    """
    citations = []
    answer_lc = (answer or "").lower()
    for chunk in context_chunks:
        title = (chunk.get("title") or "").lower()
        content = (chunk.get("content") or "").lower()
        # If title or a unique phrase from content appears in answer, cite
        if title and title in answer_lc:
            citations.append(Citation(
                document_id=chunk["document_id"],
                title=chunk.get("title"),
                source_url=chunk.get("source_url"),
            ))
        elif content and any(phrase in answer_lc for phrase in content.split()[:5]):
            citations.append(Citation(
                document_id=chunk["document_id"],
                title=chunk.get("title"),
                source_url=chunk.get("source_url"),
            ))
    # Deduplicate by document_id
    seen = set()
    deduped = []
    for c in citations:
        if c.document_id not in seen:
            deduped.append(c)
            seen.add(c.document_id)
    return deduped

# --- Main RAG Pipeline ---

async def answer_question_rag(
    db: AsyncSession,
    question: str,
    prompt_version: Optional[str] = None,
    llm_model: Optional[str] = None,
    eval_mode: bool = False,
) -> RAGAnswerOut:
    """
    Core RAG pipeline: handles retrieval, prompt construction, LLM call, citation extraction, safety checks.
    Returns RAGAnswerOut (or RAGRefusalOut if refused).
    """
    now = datetime.now(timezone.utc)
    question_id = uuid.uuid4()
    prompt_version = prompt_version or get_prompt_version()
    llm_model = llm_model or settings.LLM_MODEL

    # Safety/refusal check
    refusal_reason = should_refuse(question)
    if refusal_reason:
        logger.info(f"Refused question: {question!r} ({refusal_reason})")
        return RAGRefusalOut(
            id=question_id,
            created_at=now,
            question=question,
            answer=refusal_reason,
            citations=[],
            status="refused",
            llm_model=llm_model,
            prompt_version=prompt_version,
            safety_flag=True,
        )

    # Retrieval
    try:
        context_chunks = await retrieve_relevant_chunks(db, question, top_k=4)
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return RAGAnswerOut(
            id=question_id,
            created_at=now,
            question=question,
            answer=None,
            citations=[],
            status="error",
            llm_model=llm_model,
            prompt_version=prompt_version,
            safety_flag=True,
        )

    # Prompt construction
    prompt = build_rag_prompt(question, context_chunks, prompt_version)

    # LLM call
    llm_client = get_llm_client(llm_model)
    try:
        llm_resp = await llm_client.generate(
            prompt=prompt,
            model=llm_model,
            temperature=0.0 if eval_mode else 0.2,
            max_tokens=512,
        )
        answer = llm_resp.get("text") or llm_resp.get("answer") or ""
        cost_usd = llm_resp.get("cost_usd", None)
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        return RAGAnswerOut(
            id=question_id,
            created_at=now,
            question=question,
            answer=None,
            citations=[],
            status="error",
            llm_model=llm_model,
            prompt_version=prompt_version,
            safety_flag=True,
        )

    # Citation extraction
    citations = extract_citations_from_answer(answer, context_chunks)

    # Safety check on answer
    safety_flag = False
    status = "answered"
    if not answer or "cannot answer" in answer.lower() or "not allowed" in answer.lower():
        status = "refused"
        safety_flag = True
    elif is_unsafe_question(answer):
        status = "refused"
        safety_flag = True

    # Persist UserQuery (unless eval_mode)
    if not eval_mode:
        user_query = UserQuery(
            id=question_id,
            question=question,
            answer=answer,
            citations=[c.document_id for c in citations],
            created_at=now,
            status=status,
            llm_model=llm_model,
            prompt_version=prompt_version,
        )
        db.add(user_query)
        await db.commit()

    return RAGAnswerOut(
        id=question_id,
        created_at=now,
        question=question,
        answer=answer,
        citations=citations,
        status=status,
        llm_model=llm_model,
        prompt_version=prompt_version,
        safety_flag=safety_flag,
    )

# --- Utility: List available prompt versions ---

def list_prompt_versions() -> List[str]:
    """
    Returns a list of available prompt template versions.
    """
    from ..core.prompts import list_prompt_versions as _list
    return _list()

# --- Utility: List available LLM models ---

def list_llm_models() -> List[str]:
    """
    Returns a list of supported LLM model names (from config).
    """
    return settings.LLM_MODELS or [settings.LLM_MODEL]
