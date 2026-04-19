/**
 * QueryForm component for submitting user questions to the RAG Q&A assistant.
 * - Handles input, validation, and submit button state.
 * - Calls onSubmit prop with the user's question.
 */

import React, { useState, useRef, FormEvent } from "react";

interface QueryFormProps {
  onSubmit: (question: string) => void | Promise<void>;
  loading?: boolean;
  disabled?: boolean;
}

export const QueryForm: React.FC<QueryFormProps> = ({
  onSubmit,
  loading = false,
  disabled = false,
}) => {
  const [input, setInput] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Validate and submit the question
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const question = input.trim();
    if (!question) {
      setError("Please enter a question.");
      inputRef.current?.focus();
      return;
    }
    if (question.length > 512) {
      setError("Question is too long (max 512 characters).");
      inputRef.current?.focus();
      return;
    }
    setError(null);
    await onSubmit(question);
    setInput("");
  };

  // Clear error on input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
    if (error) setError(null);
  };

  // Allow Enter to submit, but Shift+Enter for multiline (if textarea used in future)
  // For now, input is single-line.

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <label htmlFor="question-input" className="sr-only">
        Ask a question
      </label>
      <div className="flex gap-2">
        <input
          id="question-input"
          ref={inputRef}
          type="text"
          className="flex-1 border border-gray-300 rounded px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Ask a question about the documents..."
          value={input}
          onChange={handleInputChange}
          disabled={loading || disabled}
          maxLength={512}
          autoComplete="off"
          autoFocus
          aria-label="Ask a question"
        />
        <button
          type="submit"
          className={`inline-flex items-center px-4 py-2 rounded font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition ${
            loading || disabled
              ? "opacity-60 cursor-not-allowed"
              : ""
          }`}
          disabled={loading || disabled || !input.trim()}
          aria-disabled={loading || disabled || !input.trim()}
        >
          {loading ? (
            <svg
              className="animate-spin h-5 w-5 mr-2 text-white"
              viewBox="0 0 24 24"
            >
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
          ) : (
            <svg
              className="h-5 w-5 mr-2 text-white"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 12h14M12 5l7 7-7 7"
              />
            </svg>
          )}
          Ask
        </button>
      </div>
      {error && (
        <div className="text-red-600 text-sm font-medium">{error}</div>
      )}
    </form>
  );
};
