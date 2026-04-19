"""
Pydantic schemas for evaluation API input/output.

- Defines schemas for EvalSet, EvalResult, evaluation run requests, and evaluation report responses.
- Used for API endpoints: /api/v1/eval/run, /api/v1/eval/report, etc.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Any

from pydantic import Field

from .base import APIModel, IDModel, TimestampModel

# --- EvalSet Schemas ---

class EvalQuestion(APIModel):
    """
    A single evaluation question and its gold answer.
    """
    question: str = Field(..., description="Evaluation question")
    gold_answer: Optional[str] = Field(None, description="Reference/gold answer (optional)")
    meta: Optional[Any] = Field(None, description="Optional metadata for this question (e.g., tags, difficulty)")

class EvalSetCreate(APIModel):
    """
    Request schema for creating a new evaluation set.
    """
    name: str = Field(..., description="Name of the evaluation set")
    questions: List[EvalQuestion] = Field(..., description="List of evaluation questions")

class EvalSetOut(IDModel, TimestampModel):
    """
    Response schema for an evaluation set.
    """
    name: str = Field(..., description="Name of the evaluation set")
    questions: List[EvalQuestion] = Field(..., description="List of evaluation questions")

# --- EvalResult Schemas ---

class EvalResultOut(IDModel, TimestampModel):
    """
    Response schema for a single evaluation result.
    """
    eval_set_id: uuid.UUID = Field(..., description="EvalSet UUID")
    query_id: uuid.UUID = Field(..., description="UserQuery UUID")
    faithfulness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Faithfulness score (0-1)")
    relevance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score (0-1)")
    safety_flag: Optional[bool] = Field(None, description="True if answer is unsafe or refused")
    latency_ms: Optional[int] = Field(None, ge=0, description="Latency in milliseconds")
    cost_usd: Optional[float] = Field(None, ge=0.0, description="Estimated API cost in USD")

# --- Evaluation Run/Report Schemas ---

class EvalRunRequest(APIModel):
    """
    Request schema to trigger an evaluation run.
    """
    eval_set_id: Optional[uuid.UUID] = Field(
        None, description="EvalSet UUID to run (if omitted, use default from config)"
    )
    prompt_version: Optional[str] = Field(
        None, description="Prompt template version to use (optional override)"
    )
    llm_model: Optional[str] = Field(
        None, description="LLM model to use for evaluation (optional override)"
    )

class EvalRunResponse(APIModel):
    """
    Response schema after triggering an evaluation run.
    """
    eval_set_id: uuid.UUID = Field(..., description="EvalSet UUID used")
    num_questions: int = Field(..., description="Number of questions evaluated")
    started_at: datetime = Field(..., description="Evaluation start time (UTC)")
    finished_at: datetime = Field(..., description="Evaluation end time (UTC)")
    report_path: str = Field(..., description="Path to generated evaluation report file")
    results: List[EvalResultOut] = Field(..., description="List of evaluation results")

class EvalReportMetrics(APIModel):
    """
    Aggregated metrics for an evaluation report.
    """
    avg_faithfulness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Average faithfulness score")
    avg_relevance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Average relevance score")
    num_safe: int = Field(..., description="Number of safe answers")
    num_unsafe: int = Field(..., description="Number of unsafe/refused answers")
    avg_latency_ms: Optional[float] = Field(None, ge=0.0, description="Average latency (ms)")
    total_cost_usd: Optional[float] = Field(None, ge=0.0, description="Total API cost (USD)")

class EvalReportOut(APIModel):
    """
    Response schema for fetching an evaluation report.
    """
    eval_set: EvalSetOut = Field(..., description="Evaluation set details")
    metrics: EvalReportMetrics = Field(..., description="Aggregated evaluation metrics")
    results: List[EvalResultOut] = Field(..., description="List of evaluation results")
    report_path: str = Field(..., description="Path to the markdown evaluation report")
    generated_at: datetime = Field(..., description="Report generation timestamp (UTC)")
    prompt_version: Optional[str] = Field(None, description="Prompt template version used")
    llm_model: Optional[str] = Field(None, description="LLM model used for evaluation")
