import { useState } from 'react';
import type { DateRange } from '../types';

interface SearchPanelProps {
  ticker: string;
  selectedRange: DateRange | null;
  onSearch: (query: string) => void;
  onBacktest: () => void;
  loading: boolean;
  backtestLoading: boolean;
}

export function SearchPanel({
  ticker,
  selectedRange,
  onSearch,
  onBacktest,
  loading,
  backtestLoading,
}: SearchPanelProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && selectedRange) {
      onSearch(query.trim());
    }
  };

  const suggestedQueries = [
    'Why did the price change during this period?',
    'What news events affected this?',
    'What market factors caused this movement?',
    'Were there any earnings announcements?',
  ];

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-card border border-slate-100">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">
        Analyze Movement
      </h2>

      {!selectedRange ? (
        <div className="text-center py-8">
          <div className="text-4xl mb-3 opacity-50">🔍</div>
          <p className="text-slate-500">
            Select a time range on the chart to analyze
          </p>
          <p className="text-slate-400 text-sm mt-1">
            Use the brush selector below the chart
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Selected Range Display */}
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-slate-500">Analyzing:</span>
              <span className="text-brand-600 font-mono font-medium">
                {ticker}
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm mt-1">
              <span className="text-slate-500">Period:</span>
              <span className="text-amber-600 font-mono">
                {selectedRange.startDate} → {selectedRange.endDate}
              </span>
            </div>
          </div>

          {/* Query Input */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-slate-600 mb-2">
                Your Question
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Why did the stock increase this week?"
                rows={3}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 text-white font-semibold rounded-xl hover:from-amber-600 hover:to-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-amber-500/25"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Searching...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                  Search for Explanation
                </span>
              )}
            </button>
          </form>

          {/* Backtest Button */}
          <div className="pt-2 border-t border-slate-200">
            <p className="text-xs text-slate-400 mb-2">Or run a forecast backtest:</p>
            <button
              type="button"
              onClick={onBacktest}
              disabled={backtestLoading}
              className="w-full py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-indigo-500/25"
            >
              {backtestLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Running Backtest...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                  Run Backtest
                </span>
              )}
            </button>
            <p className="text-[10px] text-slate-400 mt-2 text-center">
              Uses Synthefy to forecast the selected region
            </p>
          </div>

          {/* Suggested Queries */}
          <div>
            <p className="text-xs text-slate-400 mb-2">Quick suggestions:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQueries.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="px-3 py-1.5 text-xs bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 hover:text-slate-800 transition-colors border border-slate-200"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

