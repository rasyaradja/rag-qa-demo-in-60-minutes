/**
 * AnswerDisplay component for showing the assistant's answer and status.
 * - Handles normal answers, refusals, and safety flags.
 * - Supports basic Markdown rendering for answer text.
 */

import React from "react";

interface AnswerDisplayProps {
  answer: string | null;
  status: "answered" | "refused" | "error";
  safetyFlag?: boolean;
}

/**
 * Very basic Markdown-to-HTML rendering for answer text.
 * For production, consider using a library like react-markdown.
 */
function renderMarkdown(text: string): React.ReactNode {
  // Simple replacements: code, bold, italics, links, line breaks
  let html = text
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^\*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^\*]+)\*/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\n/g, "<br />");
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

export const AnswerDisplay: React.FC<AnswerDisplayProps> = ({
  answer,
  status,
  safetyFlag = false,
}) => {
  if (!answer) return null;

  let statusLabel = null;
  let statusColor = "";
  if (status === "answered") {
    statusLabel = (
      <span className="inline-flex items-center gap-1 text-green-700 font-semibold text-xs bg-green-100 px-2 py-0.5 rounded">
        <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        Answered
      </span>
    );
    statusColor = "text-gray-900";
  } else if (status === "refused") {
    statusLabel = (
      <span className="inline-flex items-center gap-1 text-yellow-800 font-semibold text-xs bg-yellow-100 px-2 py-0.5 rounded">
        <svg className="h-4 w-4 text-yellow-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" />
        </svg>
        Refused
      </span>
    );
    statusColor = "text-yellow-900";
  } else if (status === "error") {
    statusLabel = (
      <span className="inline-flex items-center gap-1 text-red-800 font-semibold text-xs bg-red-100 px-2 py-0.5 rounded">
        <svg className="h-4 w-4 text-red-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" />
        </svg>
        Error
      </span>
    );
    statusColor = "text-red-900";
  }

  return (
    <div className="w-full">
      <div className="flex items-center gap-2 mb-2">
        {statusLabel}
        {safetyFlag && (
          <span className="inline-flex items-center gap-1 text-orange-700 font-semibold text-xs bg-orange-100 px-2 py-0.5 rounded" title="Safety flag">
            <svg className="h-4 w-4 text-orange-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M5.07 19h13.86c.66 0 1.07-.7.74-1.29l-6.93-12c-.33-.59-1.15-.59-1.48 0l-6.93 12A.857.857 0 005.07 19z" />
            </svg>
            Safety flag
          </span>
        )}
      </div>
      <div
        className={`prose prose-sm max-w-none ${statusColor} bg-gray-50 border border-gray-200 rounded p-4`}
        data-testid="answer-text"
      >
        {renderMarkdown(answer)}
      </div>
      {status === "refused" && (
        <div className="mt-2 text-yellow-700 text-xs">
          This question was refused due to safety or policy reasons.
        </div>
      )}
      {status === "error" && (
        <div className="mt-2 text-red-700 text-xs">
          An error occurred while generating the answer.
        </div>
      )}
      {safetyFlag && (
        <div className="mt-2 text-orange-700 text-xs">
          <strong>Note:</strong> This answer was flagged for safety review.
        </div>
      )}
    </div>
  );
};
