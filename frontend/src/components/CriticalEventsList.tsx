import { format, parseISO } from 'date-fns';
import type { CriticalEventsResult } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';

interface CriticalEventsListProps {
  result: CriticalEventsResult | null;
  loading: boolean;
  error: string | null;
  showMarkers: boolean;
  onToggleMarkers: (show: boolean) => void;
}

export function CriticalEventsList({
  result,
  loading,
  error,
  showMarkers,
  onToggleMarkers,
}: CriticalEventsListProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-card border border-cream-200 animate-fadeIn">
        <div className="flex items-center justify-center py-10">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-3 border-sage-300 border-t-sage-500 rounded-full animate-spin" />
            <p className="text-slate-500 font-medium">Searching for critical events...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-card border border-cream-200 animate-fadeIn">
        <div className="bg-coral-50 border border-coral-200 rounded-xl p-4">
          <div className="flex items-center gap-2 text-coral-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">Error loading critical events</span>
          </div>
          <p className="text-coral-600/80 text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!result || result.events.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl p-5 shadow-card border border-cream-200 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-5 pb-4 border-b border-cream-200">
        <div>
          <h2 className="text-lg font-bold text-slate-800 mb-0.5">
            Critical Events
          </h2>
          <p className="text-xs text-slate-500">
            {result.events.length} events found for {result.ticker}
          </p>
        </div>
        <label className="flex items-center gap-2 cursor-pointer bg-cream-50 px-3 py-1.5 rounded-lg border border-cream-200">
          <input
            type="checkbox"
            checked={showMarkers}
            onChange={(e) => onToggleMarkers(e.target.checked)}
            className="w-3.5 h-3.5 text-sage-500 border-slate-300 rounded focus:ring-sage-500 focus:ring-2"
          />
          <span className="text-xs font-medium text-slate-600">Show on chart</span>
        </label>
      </div>

      {/* Events Grid */}
      <div className="grid gap-3">
        {result.events.map((event, index) => {
          let formattedDate: string;
          let monthStr: string;
          let dayStr: string;
          try {
            const date = parseISO(event.date);
            formattedDate = format(date, 'MMM d, yyyy');
            monthStr = format(date, 'MMM');
            dayStr = format(date, 'd');
          } catch {
            formattedDate = event.date;
            monthStr = '---';
            dayStr = '--';
          }

          return (
            <div
              key={`${event.date}-${index}`}
              className="flex gap-3 p-3 bg-cream-50 rounded-xl border border-cream-200 hover:border-sage-300 hover:bg-sage-50/30 transition-all"
            >
              {/* Date Badge */}
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-br from-sage-400 to-sage-500 rounded-xl flex flex-col items-center justify-center text-white shadow-sm">
                  <span className="text-[9px] font-bold uppercase tracking-wider">
                    {monthStr}
                  </span>
                  <span className="text-lg font-bold leading-none">
                    {dayStr}
                  </span>
                </div>
              </div>

              {/* Event Content */}
              <div className="flex-1 min-w-0">
                {event.title && (
                  <h3 className="text-sm font-semibold text-slate-800 mb-0.5 leading-snug">
                    {event.title}
                  </h3>
                )}
                <MarkdownRenderer
                  content={event.summary}
                  className="text-xs text-slate-600 leading-relaxed"
                />

                {/* Citations */}
                {event.citations && event.citations.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {event.citations.slice(0, 2).map((citation, citIndex) => (
                      <a
                        key={citIndex}
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-sage-600 hover:text-sage-700 underline"
                      >
                        {citation.title || 'Source'}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
