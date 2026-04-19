"""
API endpoint for RAG question answering.

- POST /api/v1/rag/answer: Submit a user question; receive answer and citations.
- GET  /api/v1/rag/prompt_versions: List available prompt template versions.
- GET  /api/v1/rag/llm_models: List supported LLM model names.

Uses backend.app.services.rag_service for core RAG pipeline.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from ....schemas.rag import (
    RAGAnswerRequest,
    RAGAnswerOut,
    RAGRefusalOut,
    ErrorResponse,
)
from ....services.rag_service import (
    answer_question_rag,
    list_prompt_versions,
    list_llm_models,
)
from ....db.session import get_db

router = APIRouter()
logger = logging.getLogger("rag_api")

@router.post(
    "/rag/answer",
    summary="Submit a user question and receive answer with citations",
    tags=["rag"],
    response_model=RAGAnswerOut,
    responses={
        200: {"model": RAGAnswerOut},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def rag_answer(
    req: RAGAnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    RAG Q&A endpoint.
    Receives a user question, runs retrieval-augmented generation pipeline,
    and returns answer with citations and metadata.
    """
    question = req.question.strip() if req.question else ""
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )
    try:
        rag_out = await answer_question_rag(
            db=db,
            question=question,
            prompt_version=req.prompt_version,
            llm_model=req.llm_model,
            eval_mode=False,
        )
        # Convert datetimes to isoformat for JSONResponse
        out_dict = rag_out.dict()
        if "created_at" in out_dict and out_dict["created_at"]:
            out_dict["created_at"] = out_dict["created_at"].isoformat()
        return JSONResponse(content=out_dict, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("RAG answer failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {e}",
        )

@router.get(
    "/rag/prompt_versions",
    summary="List available prompt template versions",
    tags=["rag"],
    response_model=List[str],
    responses={
        200: {"model": List[str]},
        500: {"model": ErrorResponse},
    },
)
async def get_prompt_versions():
    """
    Returns a list of available prompt template versions.
    """
    try:
        versions = list_prompt_versions()
        return JSONResponse(content=versions, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Failed to list prompt versions.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompt versions: {e}",
        )

@router.get(
    "/rag/llm_models",
    summary="List supported LLM model names",
    tags=["rag"],
    response_model=List[str],
    responses={
        200: {"model": List[str]},
        500: {"model": ErrorResponse},
    },
)
async def get_llm_models():
    """
    Returns a list of supported LLM model names.
    """
    try:
        models = list_llm_models()
        return JSONResponse(content=models, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Failed to list LLM models.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list LLM models: {e}",
        )
