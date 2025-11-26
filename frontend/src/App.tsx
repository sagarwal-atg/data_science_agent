import { useState, useCallback, useRef, useEffect } from 'react';
import {
  DataSourceSelector,
  TimeSeriesChart,
  SearchPanel,
  SearchResults,
  BacktestResults,
} from './components';
import { useTimeSeriesData } from './hooks/useTimeSeriesData';
import { searchTimeSeriesEvent, runBacktest } from './api';
import type { SearchResult, DateRange, BacktestResult } from './types';

function App() {
  const {
    data,
    loading: dataLoading,
    error: dataError,
    ticker,
    currency,
    selectedRange,
    loadYahooData,
    loadHaverData,
    setSelectedRange,
  } = useTimeSeriesData();

  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestError, setBacktestError] = useState<string | null>(null);
  const [leftPaneWidth, setLeftPaneWidth] = useState(320); // Default 320px (w-80)
  const [isResizing, setIsResizing] = useState(false);
  const resizeRef = useRef<HTMLDivElement>(null);

  const handleSearch = useCallback(
    async (query: string) => {
      if (!selectedRange || !ticker) return;

      setSearchLoading(true);
      setSearchError(null);
      setSearchResult(null);

      try {
        // Calculate change description
        const startValue = data[selectedRange.startIndex]?.value;
        const endValue = data[selectedRange.endIndex]?.value;
        let changeDescription: string | undefined;

        if (startValue !== undefined && endValue !== undefined) {
          const change = endValue - startValue;
          const changePercent = ((change / startValue) * 100).toFixed(2);
          changeDescription = `${change >= 0 ? 'increased' : 'decreased'} by ${Math.abs(
            change
          ).toFixed(2)} (${change >= 0 ? '+' : ''}${changePercent}%)`;
        }

        const result = await searchTimeSeriesEvent({
          ticker,
          query,
          start_date: selectedRange.startDate,
          end_date: selectedRange.endDate,
          change_description: changeDescription,
        });

        setSearchResult(result);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Search failed';
        setSearchError(message);
      } finally {
        setSearchLoading(false);
      }
    },
    [selectedRange, ticker, data]
  );

  const handleBacktest = useCallback(async () => {
    if (!selectedRange || !ticker || data.length === 0) return;

    setBacktestLoading(true);
    setBacktestError(null);
    setBacktestResult(null);

    try {
      // Get all timestamps and values from the data
      const timestamps = data.map((d) => d.timestamp);
      const values = data.map((d) => d.value);

      const result = await runBacktest({
        ticker,
        timestamps,
        values,
        start_date: selectedRange.startDate,
        end_date: selectedRange.endDate,
      });

      setBacktestResult(result);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Backtest failed';
      setBacktestError(message);
    } finally {
      setBacktestLoading(false);
    }
  }, [selectedRange, ticker, data]);

  const handleRangeChange = useCallback(
    (range: DateRange | null) => {
      setSelectedRange(range);
      // Clear previous results when range changes
      setSearchResult(null);
      setSearchError(null);
      setBacktestResult(null);
      setBacktestError(null);
    },
    [setSelectedRange]
  );

  // Handle mouse move for resizing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const newWidth = e.clientX;
      // Constrain between 200px and 600px
      const constrainedWidth = Math.min(Math.max(newWidth, 200), 600);
      setLeftPaneWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  const handleMouseDown = () => {
    setIsResizing(true);
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Left Sidebar - Resizable Width */}
      <aside
        className="flex-shrink-0 border-r border-slate-200 bg-white overflow-y-auto"
        style={{ width: `${leftPaneWidth}px` }}
      >
        <div className="p-6 space-y-6">
          <div>
            <h1 className="text-xl font-bold text-slate-800 mb-1">
              Time Series AI
            </h1>
            <p className="text-xs text-slate-400">
              Financial Intelligence Dashboard
            </p>
          </div>

          <DataSourceSelector
            onLoadYahoo={loadYahooData}
            onLoadHaver={loadHaverData}
            loading={dataLoading}
          />

          <SearchPanel
            ticker={ticker}
            selectedRange={selectedRange}
            onSearch={handleSearch}
            onBacktest={handleBacktest}
            loading={searchLoading}
            backtestLoading={backtestLoading}
          />
        </div>
      </aside>

      {/* Resizer Handle */}
      <div
        ref={resizeRef}
        onMouseDown={handleMouseDown}
        className={`w-1 bg-slate-200 hover:bg-slate-400 cursor-col-resize flex-shrink-0 transition-colors relative group ${isResizing ? 'bg-slate-500' : ''
          }`}
        style={{ minWidth: '4px' }}
        title="Drag to resize"
      >
        {/* Visual indicator dots */}
        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 flex flex-col items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          <div className="w-0.5 h-0.5 rounded-full bg-slate-500"></div>
          <div className="w-0.5 h-0.5 rounded-full bg-slate-500"></div>
          <div className="w-0.5 h-0.5 rounded-full bg-slate-500"></div>
        </div>
      </div>

      {/* Main Content - Scrollable */}
      <main className="flex-1 flex flex-col min-w-0 bg-slate-50/50 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Error Display */}
          {dataError && (
            <div className="bg-coral-500/10 border border-coral-400/30 rounded-2xl p-4">
              <div className="flex items-center gap-2 text-coral-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium">Error loading data</span>
              </div>
              <p className="text-coral-600/80 text-sm mt-1">{dataError}</p>
            </div>
          )}

          {/* Chart Section - Fixed Min Height */}
          <div className="min-h-[500px]">
            <TimeSeriesChart
              data={data}
              ticker={ticker}
              currency={currency}
              selectedRange={selectedRange}
              onRangeChange={handleRangeChange}
            />
          </div>

          {/* Search Results - Below Chart */}
          {(searchResult || searchLoading || searchError) && (
            <div className="animate-fadeIn">
              <SearchResults
                result={searchResult}
                loading={searchLoading}
                error={searchError}
              />
            </div>
          )}

          {/* Backtest Results - Below Chart */}
          {(backtestResult || backtestLoading || backtestError) && (
            <div className="animate-fadeIn">
              <BacktestResults
                result={backtestResult}
                loading={backtestLoading}
                error={backtestError}
                fullTimeSeries={data}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
