/**
 * Main page component for the RAG Q&A Demo frontend.
 * - Renders the question submission form, answer display, and citation list.
 * - Handles API calls to backend /api/v1/rag/answer.
 * - Shows prompt version/model selectors and error/safety messages.
 */

"use client";

import React, { useState, useRef } from "react";
import { QueryForm } from "../components/QueryForm";
import { AnswerDisplay } from "../components/AnswerDisplay";
import { CitationList } from "../components/CitationList";
import { getRagAnswer, getPromptVersions, getLlmModels } from "../lib/api";
import type { RAGAnswerOut, RAGRefusalOut, Citation } from "../lib/api";

export default function HomePage() {
  // State for user input, answer, citations, loading, error, prompt version/model
  const [question, setQuestion] = useState<string>("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "answered" | "refused" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [promptVersions, setPromptVersions] = useState<string[]>([]);
  const [selectedPromptVersion, setSelectedPromptVersion] = useState<string>("");
  const [llmModels, setLlmModels] = useState<string[]>([]);
  const [selectedLlmModel, setSelectedLlmModel] = useState<string>("");
  const [safetyFlag, setSafetyFlag] = useState<boolean>(false);

  const answerRef = useRef<HTMLDivElement>(null);

  // Fetch prompt versions and LLM models on mount
  React.useEffect(() => {
    getPromptVersions()
      .then((versions) => {
        setPromptVersions(versions);
        if (versions.length > 0) setSelectedPromptVersion(versions[0]);
      })
      .catch(() => setPromptVersions([]));
    getLlmModels()
      .then((models) => {
        setLlmModels(models);
        if (models.length > 0) setSelectedLlmModel(models[0]);
      })
      .catch(() => setLlmModels([]));
  }, []);

  // Scroll to answer after submission
  React.useEffect(() => {
    if (status === "answered" || status === "refused") {
      setTimeout(() => {
        answerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    }
  }, [status]);

  // Handle question submission
  const handleSubmit = async (q: string) => {
    setQuestion(q);
    setAnswer(null);
    setCitations([]);
    setError(null);
    setStatus("loading");
    setSafetyFlag(false);

    try {
      const resp: RAGAnswerOut | RAGRefusalOut = await getRagAnswer({
        question: q,
        prompt_version: selectedPromptVersion,
        llm_model: selectedLlmModel,
      });
      if (resp.status === "answered") {
        setAnswer(resp.answer || "");
        setCitations(resp.citations || []);
        setStatus("answered");
        setSafetyFlag(!!resp.safety_flag);
      } else if (resp.status === "refused") {
        setAnswer(resp.answer || "Sorry, I cannot answer that question.");
        setCitations([]);
        setStatus("refused");
        setSafetyFlag(true);
      } else {
        setError("An error occurred. Please try again.");
        setStatus("error");
      }
    } catch (err: any) {
      setError(
        err?.response?.data?.error ||
          err?.message ||
          "An unexpected error occurred. Please try again."
      );
      setStatus("error");
    }
  };

  // Handle prompt version/model change
  const handlePromptVersionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedPromptVersion(e.target.value);
  };
  const handleLlmModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLlmModel(e.target.value);
  };

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-2xl bg-white rounded-xl shadow-lg p-6">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-1">RAG Q&amp;A Demo</h1>
          <p className="text-gray-600 text-sm">
            Retrieval-Augmented Generation assistant. Ask a question about the provided documents and get an answer with source citations.
          </p>
        </header>

        <section className="mb-4 flex flex-col md:flex-row gap-3">
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-700 mb-1" htmlFor="prompt-version">
              Prompt Version
            </label>
            <select
              id="prompt-version"
              className="w-full border rounded px-2 py-1 text-sm"
              value={selectedPromptVersion}
              onChange={handlePromptVersionChange}
              disabled={promptVersions.length === 0}
            >
              {promptVersions.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-700 mb-1" htmlFor="llm-model">
              LLM Model
            </label>
            <select
              id="llm-model"
              className="w-full border rounded px-2 py-1 text-sm"
              value={selectedLlmModel}
              onChange={handleLlmModelChange}
              disabled={llmModels.length === 0}
            >
              {llmModels.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        </section>

        <QueryForm
          onSubmit={handleSubmit}
          loading={status === "loading"}
          disabled={status === "loading"}
        />

        <div ref={answerRef} className="mt-8">
          {status === "loading" && (
            <div className="flex items-center gap-2 text-blue-600 text-sm">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
              Generating answer...
            </div>
          )}

          {(status === "answered" || status === "refused") && (
            <div className="mt-2">
              <AnswerDisplay
                answer={answer}
                status={status}
                safetyFlag={safetyFlag}
              />
              {citations.length > 0 && (
                <div className="mt-4">
                  <CitationList citations={citations} />
                </div>
              )}
            </div>
          )}

          {status === "error" && error && (
            <div className="mt-2 text-red-600 text-sm font-medium">
              {error}
            </div>
          )}
        </div>
      </div>

      <footer className="mt-8 text-xs text-gray-400 text-center">
        <p>
          &copy; {new Date().getFullYear()} RAG Q&amp;A Demo &mdash; Powered by Next.js, FastAPI, OpenAI, and FAISS.
        </p>
        <p>
          <a
            href="https://github.com/your-org/rag-qa-demo"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-blue-600"
          >
            View Source on GitHub
          </a>
        </p>
      </footer>
    </main>
  );
}
