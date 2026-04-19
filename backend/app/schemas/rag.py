"""
Pydantic schemas for RAG (Retrieval-Augmented Generation) Q&A API.

- Defines request/response schemas for /api/v1/rag/answer and related endpoints.
- Used for user question submission, answer/citation output, and refusal/error responses.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import Field

from .base import APIModel, IDModel, TimestampModel, ErrorResponse

# --- RAG Answer API Schemas ---

class RAGAnswerRequest(APIModel):
    """
    Request schema for submitting a user question to the RAG assistant.
    """
    question: str = Field(..., min_length=1, max_length=1024, description="User question to be answered")
    prompt_version: Optional[str] = Field(
        None, description="Prompt template version to use (optional override)"
    )
    llm_model: Optional[str] = Field(
        None, description="LLM model to use for answer generation (optional override)"
    )

class Citation(APIModel):
    """
    Schema for a single document citation in the answer.
    """
    document_id: uuid.UUID = Field(..., description="UUID of the cited document")
    title: Optional[str] = Field(None, description="Title of the cited document")
    source_url: Optional[str] = Field(None, description="Source URL of the cited document (if available)")

class RAGAnswerOut(IDModel, TimestampModel):
    """
    Response schema for a RAG answer, including citations and metadata.
    """
    question: str = Field(..., description="User question")
    answer: Optional[str] = Field(None, description="Generated answer (may be None if refused or error)")
    citations: List[Citation] = Field(default_factory=list, description="List of cited documents")
    status: str = Field(..., description="Status: 'answered', 'refused', or 'error'")
    llm_model: Optional[str] = Field(None, description="LLM model used for answer generation")
    prompt_version: Optional[str] = Field(None, description="Prompt template version used")
    safety_flag: Optional[bool] = Field(
        None, description="True if the answer was refused or flagged as unsafe"
    )

class RAGRefusalOut(IDModel, TimestampModel):
    """
    Response schema for a refused or unsafe query.
    """
    question: str = Field(..., description="User question")
    answer: Optional[str] = Field(
        None, description="Refusal message explaining why the question was not answered"
    )
    citations: List[Citation] = Field(default_factory=list, description="Empty list (no citations)")
    status: str = Field("refused", const=True, description="Status: always 'refused'")
    llm_model: Optional[str] = Field(None, description="LLM model used (if any)")
    prompt_version: Optional[str] = Field(None, description="Prompt template version used (if any)")
    safety_flag: bool = Field(True, description="Always True for refusals")

# --- Example Error Response (inherits from ErrorResponse) ---

# ErrorResponse is already defined in base.py and reused for all error cases.

# --- Example Usage in FastAPI endpoint ---
# @app.post("/api/v1/rag/answer", response_model=RAGAnswerOut, responses={400: {"model": ErrorResponse}})
# async def answer_question(...):
#     ...

