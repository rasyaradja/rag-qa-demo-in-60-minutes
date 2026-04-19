/**
 * CitationList component for displaying supporting document citations for an answer.
 * - Shows document title, optional source URL, and snippet preview.
 * - Renders as a numbered list.
 */

import React from "react";

export interface Citation {
  id: string;
  title: string;
  source_url?: string | null;
  snippet?: string | null;
}

interface CitationListProps {
  citations: Citation[];
}

export const CitationList: React.FC<CitationListProps> = ({ citations }) => {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="w-full">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">
        Source Citations
      </h3>
      <ol className="list-decimal pl-5 space-y-3">
        {citations.map((c, idx) => (
          <li key={c.id} className="bg-gray-100 rounded p-3 border border-gray-200">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-gray-900">
                {c.title || `Document ${idx + 1}`}
              </span>
              {c.source_url && (
                <a
                  href={c.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 text-blue-600 underline text-xs hover:text-blue-800"
                  title="View source"
                >
                  [source]
                </a>
              )}
            </div>
            {c.snippet && (
              <div className="text-gray-700 text-xs mt-1">
                <span className="italic">“…{c.snippet.trim()}…”</span>
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
};
