import type { SearchResult } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';

interface SearchResultsProps {
  result: SearchResult | null;
  loading: boolean;
  error: string | null;
}

export function SearchResults({ result, loading, error }: SearchResultsProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-card border border-cream-200">
        <div className="flex flex-col items-center justify-center py-10">
          <div className="w-10 h-10 border-3 border-coral-200 border-t-coral-500 rounded-full animate-spin mb-4" />
          <p className="text-slate-600 font-medium">Searching the web...</p>
          <p className="text-slate-400 text-sm mt-1">This may take a moment</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-card border border-coral-200">
        <div className="flex items-start gap-3">
          <div className="text-xl">⚠️</div>
          <div>
            <h3 className="text-coral-600 font-semibold">Search Failed</h3>
            <p className="text-slate-600 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const allCitations = result.basis.flatMap((b) => b.citations);
  const uniqueCitations = allCitations.filter(
    (citation, index, self) =>
      index === self.findIndex((c) => c.url === citation.url)
  );

  return (
    <div className="bg-white rounded-2xl p-5 shadow-card border border-cream-200 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-800">Analysis Results</h2>
        <span
          className={`px-2.5 py-1 rounded-lg text-xs font-medium ${result.status === 'completed'
              ? 'bg-sage-100 text-sage-600'
              : 'bg-clay-100 text-clay-600'
            }`}
        >
          {result.status}
        </span>
      </div>

      {/* Main Content */}
      <div className="bg-cream-50 rounded-xl p-4 border border-cream-200">
        <MarkdownRenderer
          content={result.content}
          className="text-slate-700 leading-relaxed"
        />
      </div>

      {/* Reasoning */}
      {result.basis.map((basis, index) => (
        <div key={index}>
          {basis.reasoning && (
            <div className="bg-sky-50 rounded-xl p-4 border border-sky-100">
              <h4 className="text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-sky-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
                Reasoning
              </h4>
              <MarkdownRenderer
                content={basis.reasoning}
                className="text-slate-600 text-sm leading-relaxed"
              />
            </div>
          )}
        </div>
      ))}

      {/* Citations */}
      {uniqueCitations.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-slate-700 mb-3 flex items-center gap-2">
            <svg
              className="w-4 h-4 text-clay-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              />
            </svg>
            Sources ({uniqueCitations.length})
          </h4>
          <div className="space-y-2">
            {uniqueCitations.map((citation, index) => (
              <a
                key={index}
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 bg-cream-50 rounded-xl border border-cream-200 hover:border-coral-300 hover:bg-coral-50/30 transition-all group"
              >
                <div className="flex items-center gap-2">
                  <svg
                    className="w-4 h-4 text-slate-400 group-hover:text-coral-500 transition-colors flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                  <span className="text-coral-600 text-sm truncate group-hover:text-coral-700 font-medium">
                    {citation.title || new URL(citation.url).hostname}
                  </span>
                </div>
                <p className="text-slate-400 text-xs mt-1 truncate">
                  {citation.url}
                </p>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
