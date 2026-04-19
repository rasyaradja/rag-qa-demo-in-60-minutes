/**
 * API client utilities for communicating with the FastAPI backend.
 *
 * - Handles RAG Q&A, evaluation, and health endpoints.
 * - Provides typed request/response helpers for frontend components.
 * - Reads backend URL from NEXT_PUBLIC_API_BASE_URL or defaults to '/api'.
 */

import type { UUID } from 'crypto'; // Node 18+; fallback to string if needed
import type { AxiosRequestConfig } from 'axios';

export type ApiError = {
  error: string;
  code: string;
};

export type Citation = {
  document_id: string; // UUID
  title?: string;
  source_url?: string;
};

export type RAGAnswerRequest = {
  question: string;
  prompt_version?: string;
  llm_model?: string;
};

export type RAGAnswerOut = {
  id: string;
  created_at: string;
  question: string;
  answer?: string;
  citations: Citation[];
  status: 'answered' | 'refused' | 'error';
  llm_model?: string;
  prompt_version?: string;
  safety_flag?: boolean;
};

export type RAGRefusalOut = RAGAnswerOut & {
  status: 'refused';
  answer?: string;
  safety_flag: true;
};

export type EvalQuestion = {
  question: string;
  gold_answer?: string;
  meta?: any;
};

export type EvalSetOut = {
  id: string;
  created_at: string;
  name: string;
  questions: EvalQuestion[];
};

export type EvalResultOut = {
  id: string;
  created_at: string;
  eval_set_id: string;
  query_id: string;
  faithfulness?: number;
  relevance?: number;
  safety_flag?: boolean;
  latency_ms?: number;
  cost_usd?: number;
};

export type EvalReportMetrics = {
  avg_faithfulness?: number;
  avg_relevance?: number;
  num_safe: number;
  num_unsafe: number;
  avg_latency_ms?: number;
  total_cost_usd?: number;
};

export type EvalReportOut = {
  eval_set: EvalSetOut;
  metrics: EvalReportMetrics;
  results: EvalResultOut[];
  report_path: string;
  generated_at: string;
  prompt_version?: string;
  llm_model?: string;
};

export type EvalRunRequest = {
  eval_set_id?: string;
  prompt_version?: string;
  llm_model?: string;
};

export type EvalRunResponse = {
  eval_set_id: string;
  num_questions: number;
  started_at: string;
  finished_at: string;
  report_path: string;
  results: EvalResultOut[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, '') || '/api/v1';

/**
 * Helper for HTTP requests with error handling.
 */
async function apiFetch<T>(
  path: string,
  options?: RequestInit & { skipJsonError?: boolean }
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const resp = await fetch(url, {
    credentials: 'same-origin',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });

  const isJson = resp.headers
    .get('content-type')
    ?.includes('application/json');

  if (!resp.ok) {
    let err: ApiError = {
      error: resp.statusText,
      code: `http_${resp.status}`,
    };
    if (isJson && !options?.skipJsonError) {
      try {
        const data = await resp.json();
        if (data && typeof data.error === 'string') {
          err = data;
        }
      } catch {
        // ignore
      }
    }
    throw err;
  }

  if (isJson) {
    return resp.json();
  }
  // @ts-expect-error
  return resp.text();
}

/**
 * Submit a user question to the RAG assistant.
 */
export async function submitRAGQuestion(
  req: RAGAnswerRequest
): Promise<RAGAnswerOut> {
  return apiFetch<RAGAnswerOut>('/rag/answer', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

/**
 * Health check endpoint.
 */
export async function getApiHealth(): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/rag/health', { method: 'GET' });
}

/**
 * Trigger an evaluation run (admin-only in production).
 */
export async function runEvaluation(
  req: EvalRunRequest = {}
): Promise<EvalRunResponse> {
  return apiFetch<EvalRunResponse>('/eval/run', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

/**
 * Fetch the latest evaluation report.
 */
export async function fetchEvalReport(): Promise<EvalReportOut> {
  return apiFetch<EvalReportOut>('/eval/report', { method: 'GET' });
}

/**
 * Utility: Check if error is an ApiError.
 */
export function isApiError(e: unknown): e is ApiError {
  return (
    typeof e === 'object' &&
    e !== null &&
    'error' in e &&
    typeof (e as any).error === 'string'
  );
}
