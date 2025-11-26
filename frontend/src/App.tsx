import { useState, useCallback, useRef, useEffect } from 'react';
import {
  DataSourceSelector,
  TimeSeriesChart,
  SearchResults,
  BacktestResults,
  CriticalEventsList,
} from './components';
import { useTimeSeriesData } from './hooks/useTimeSeriesData';
import { searchTimeSeriesEvent, runBacktest, searchCriticalEvents } from './api';
import type { SearchResult, DateRange, BacktestResult, CriticalEventsResult } from './types';

type AnalysisTab = 'explain' | 'events' | 'backtest';

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
    loadCryptoData,
    loadForexData,
    setSelectedRange,
  } = useTimeSeriesData();

  const [activeTab, setActiveTab] = useState<AnalysisTab>('explain');
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestError, setBacktestError] = useState<string | null>(null);
  const [criticalEventsResult, setCriticalEventsResult] = useState<CriticalEventsResult | null>(null);
  const [criticalEventsLoading, setCriticalEventsLoading] = useState(false);
  const [criticalEventsError, setCriticalEventsError] = useState<string | null>(null);
  const [showEventMarkers, setShowEventMarkers] = useState(false);
  const [brushRange, setBrushRange] = useState<DateRange | null>(null);
  const [leftPaneWidth, setLeftPaneWidth] = useState(300);
  const [isResizing, setIsResizing] = useState(false);
  const [query, setQuery] = useState('');
  const resizeRef = useRef<HTMLDivElement>(null);

  const handleSearch = useCallback(
    async (searchQuery: string) => {
      if (!selectedRange || !ticker) return;

      setSearchLoading(true);
      setSearchError(null);
      setSearchResult(null);

      try {
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
          query: searchQuery,
          start_date: selectedRange.startDate,
          end_date: selectedRange.endDate,
          change_description: changeDescription,
        });

        setSearchResult(result);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Search failed';
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
      const message = err instanceof Error ? err.message : 'Backtest failed';
      setBacktestError(message);
    } finally {
      setBacktestLoading(false);
    }
  }, [selectedRange, ticker, data]);

  const handleCriticalEvents = useCallback(async () => {
    if (!brushRange || !ticker) return;

    setCriticalEventsLoading(true);
    setCriticalEventsError(null);
    setCriticalEventsResult(null);
    setShowEventMarkers(false);

    try {
      const result = await searchCriticalEvents({
        ticker,
        start_date: brushRange.startDate,
        end_date: brushRange.endDate,
        num_events: 10,
      });

      setCriticalEventsResult(result);
      setShowEventMarkers(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Critical events search failed';
      setCriticalEventsError(message);
    } finally {
      setCriticalEventsLoading(false);
    }
  }, [brushRange, ticker]);

  const handleBrushChange = useCallback((range: DateRange | null) => {
    setBrushRange(range);
    setCriticalEventsResult(null);
    setCriticalEventsError(null);
    setShowEventMarkers(false);
  }, []);

  useEffect(() => {
    if (data.length > 0) {
      const newBrushRange = {
        startDate: data[0].timestamp.split('T')[0],
        endDate: data[data.length - 1].timestamp.split('T')[0],
        startIndex: 0,
        endIndex: data.length - 1,
      };

      setBrushRange((currentRange) => {
        if (!currentRange ||
          currentRange.startDate !== newBrushRange.startDate ||
          currentRange.endDate !== newBrushRange.endDate) {
          return newBrushRange;
        }
        return currentRange;
      });

      setCriticalEventsResult(null);
      setCriticalEventsError(null);
      setShowEventMarkers(false);
    } else {
      setBrushRange(null);
    }
  }, [data]);

  const handleRangeChange = useCallback(
    (range: DateRange | null) => {
      setSelectedRange(range);
      setSearchResult(null);
      setSearchError(null);
      setBacktestResult(null);
      setBacktestError(null);
    },
    [setSelectedRange]
  );

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = e.clientX;
      const constrainedWidth = Math.min(Math.max(newWidth, 240), 450);
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && selectedRange) {
      handleSearch(query.trim());
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'explain':
        return (
          <div className="space-y-3">
            {selectedRange ? (
              <>
                <div className="bg-cream-100 rounded-xl p-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Period</span>
                    <span className="font-mono font-medium text-coral-600">
                      {selectedRange.startDate} → {selectedRange.endDate}
                    </span>
                  </div>
                </div>
                <form onSubmit={handleSubmit} className="space-y-3">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Why did the price change?"
                    rows={2}
                    className="w-full px-3 py-2.5 bg-white border border-cream-300 rounded-xl text-slate-800 placeholder-slate-400 text-sm focus:outline-none focus:border-coral-400 resize-none"
                  />
                  <button
                    type="submit"
                    disabled={searchLoading || !query.trim()}
                    className="w-full py-2.5 bg-coral-500 text-white font-semibold rounded-xl hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
                  >
                    {searchLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Searching...
                      </span>
                    ) : (
                      'Search'
                    )}
                  </button>
                </form>
                <div className="flex flex-wrap gap-1.5">
                  {['Why did price change?', 'Any news events?'].map((s) => (
                    <button
                      key={s}
                      onClick={() => setQuery(s)}
                      className="px-2.5 py-1 text-[11px] bg-cream-100 text-slate-600 rounded-lg hover:bg-cream-200 transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-6">
                <div className="text-2xl mb-2 opacity-40">📈</div>
                <p className="text-slate-500 text-sm">Select a range on the chart</p>
              </div>
            )}
          </div>
        );

      case 'events':
        return (
          <div className="space-y-3">
            {brushRange && (
              <div className="bg-cream-100 rounded-xl p-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Range</span>
                  <span className="font-mono font-medium text-sage-600">
                    {brushRange.startDate} → {brushRange.endDate}
                  </span>
                </div>
              </div>
            )}
            <button
              onClick={handleCriticalEvents}
              disabled={criticalEventsLoading || !brushRange}
              className="w-full py-2.5 bg-sage-500 text-white font-semibold rounded-xl hover:bg-sage-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
            >
              {criticalEventsLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Searching...
                </span>
              ) : (
                'Find Critical Events'
              )}
            </button>
            <p className="text-[10px] text-slate-400 text-center">
              Searches for important events in the visible range
            </p>
          </div>
        );

      case 'backtest':
        return (
          <div className="space-y-3">
            {selectedRange ? (
              <>
                <div className="bg-cream-100 rounded-xl p-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Forecast Target</span>
                    <span className="font-mono font-medium text-lavender-600">
                      {selectedRange.startDate} → {selectedRange.endDate}
                    </span>
                  </div>
                </div>
                <button
                  onClick={handleBacktest}
                  disabled={backtestLoading}
                  className="w-full py-2.5 bg-lavender-500 text-white font-semibold rounded-xl hover:bg-lavender-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
                >
                  {backtestLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Running...
                    </span>
                  ) : (
                    'Run Backtest'
                  )}
                </button>
                <p className="text-[10px] text-slate-400 text-center">
                  Uses Synthefy to forecast the selected region
                </p>
              </>
            ) : (
              <div className="text-center py-6">
                <div className="text-2xl mb-2 opacity-40">📊</div>
                <p className="text-slate-500 text-sm">Select a range to backtest</p>
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen bg-cream-100 overflow-hidden">
      {/* Left Sidebar */}
      <aside
        className="flex-shrink-0 border-r border-cream-300 bg-cream-50 overflow-y-auto"
        style={{ width: `${leftPaneWidth}px` }}
      >
        <div className="p-4 space-y-4">
          {/* Header */}
          <div className="pb-3 border-b border-cream-200">
            <h1 className="text-lg font-bold text-slate-800 tracking-tight">
              Time Series AI
            </h1>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider mt-0.5">
              Financial Intelligence
            </p>
          </div>

          {/* Data Source */}
          <DataSourceSelector
            onLoadYahoo={loadYahooData}
            onLoadHaver={loadHaverData}
            onLoadCrypto={loadCryptoData}
            onLoadForex={loadForexData}
            loading={dataLoading}
          />

          {/* Analysis Section */}
          {ticker && (
            <div className="space-y-3">
              {/* Ticker Display */}
              <div className="flex items-center gap-2 px-3 py-2 bg-white rounded-xl border border-cream-200">
                <div className="w-2 h-2 rounded-full bg-sage-400"></div>
                <span className="text-sm font-semibold text-slate-700">{ticker}</span>
              </div>

              {/* Tabs */}
              <div className="bg-cream-200 p-1 rounded-xl">
                <div className="grid grid-cols-3 gap-1">
                  {[
                    { id: 'explain', label: 'Explain', icon: '💡' },
                    { id: 'events', label: 'Events', icon: '📅' },
                    { id: 'backtest', label: 'Forecast', icon: '📈' },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as AnalysisTab)}
                      className={`px-2 py-2 rounded-lg text-xs font-medium transition-all ${activeTab === tab.id
                          ? 'bg-white text-slate-800 shadow-sm'
                          : 'text-slate-500 hover:text-slate-700 hover:bg-white/50'
                        }`}
                    >
                      <span className="mr-1">{tab.icon}</span>
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tab Content */}
              <div className="bg-white rounded-xl p-3 border border-cream-200">
                {renderTabContent()}
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Resizer */}
      <div
        ref={resizeRef}
        onMouseDown={handleMouseDown}
        className={`w-1 bg-cream-200 hover:bg-coral-300 cursor-col-resize flex-shrink-0 transition-colors ${isResizing ? 'bg-coral-400' : ''
          }`}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 bg-cream-100 overflow-y-auto">
        <div className="p-5 space-y-5">
          {/* Error Display */}
          {dataError && (
            <div className="bg-coral-50 border border-coral-200 rounded-2xl p-4">
              <div className="flex items-center gap-2 text-coral-700">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium">Error loading data</span>
              </div>
              <p className="text-coral-600 text-sm mt-1">{dataError}</p>
            </div>
          )}

          {/* Chart */}
          <div className="min-h-[480px]">
            <TimeSeriesChart
              data={data}
              ticker={ticker}
              currency={currency}
              selectedRange={selectedRange}
              onRangeChange={handleRangeChange}
              onBrushChange={handleBrushChange}
              criticalEvents={criticalEventsResult?.events}
              showEventMarkers={showEventMarkers}
            />
          </div>

          {/* Results based on active tab */}
          {activeTab === 'explain' && (searchResult || searchLoading || searchError) && (
            <div className="animate-fadeIn">
              <SearchResults
                result={searchResult}
                loading={searchLoading}
                error={searchError}
              />
            </div>
          )}

          {activeTab === 'backtest' && (backtestResult || backtestLoading || backtestError) && (
            <div className="animate-fadeIn">
              <BacktestResults
                result={backtestResult}
                loading={backtestLoading}
                error={backtestError}
                fullTimeSeries={data}
              />
            </div>
          )}

          {activeTab === 'events' && (criticalEventsResult || criticalEventsLoading || criticalEventsError) && (
            <div className="animate-fadeIn">
              <CriticalEventsList
                result={criticalEventsResult}
                loading={criticalEventsLoading}
                error={criticalEventsError}
                showMarkers={showEventMarkers}
                onToggleMarkers={setShowEventMarkers}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
