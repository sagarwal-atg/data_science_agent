import { useState, useEffect } from 'react';
import type { DataSource, HaverDatabase, HaverSeries } from '../types';
import { fetchHaverDatabases, fetchHaverSeries } from '../api';

interface DataSourceSelectorProps {
  onLoadYahoo: (ticker: string) => void;
  onLoadHaver: (database: string, series: string) => void;
  loading: boolean;
}

export function DataSourceSelector({
  onLoadYahoo,
  onLoadHaver,
  loading,
}: DataSourceSelectorProps) {
  const [dataSource, setDataSource] = useState<DataSource>('yahoo');
  const [yahooTicker, setYahooTicker] = useState('NVDA');

  // Haver state
  const [databases, setDatabases] = useState<HaverDatabase[]>([]);
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [series, setSeries] = useState<HaverSeries[]>([]);
  const [selectedSeries, setSelectedSeries] = useState<string>('');
  const [loadingDatabases, setLoadingDatabases] = useState(false);
  const [loadingSeries, setLoadingSeries] = useState(false);
  const [seriesSearch, setSeriesSearch] = useState('');

  // Load databases when Haver is selected
  useEffect(() => {
    if (dataSource === 'haver' && databases.length === 0) {
      loadDatabases();
    }
  }, [dataSource]);

  // Load series when database is selected
  useEffect(() => {
    if (selectedDatabase) {
      loadSeriesForDatabase(selectedDatabase);
    }
  }, [selectedDatabase]);

  const loadDatabases = async () => {
    setLoadingDatabases(true);
    try {
      const dbs = await fetchHaverDatabases();
      setDatabases(dbs);
    } catch (err) {
      console.error('Failed to load databases:', err);
    } finally {
      setLoadingDatabases(false);
    }
  };

  const loadSeriesForDatabase = async (db: string) => {
    setLoadingSeries(true);
    setSeries([]);
    setSelectedSeries('');
    try {
      const seriesList = await fetchHaverSeries(db);
      setSeries(seriesList);
    } catch (err) {
      console.error('Failed to load series:', err);
    } finally {
      setLoadingSeries(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (dataSource === 'yahoo') {
      if (yahooTicker.trim()) {
        onLoadYahoo(yahooTicker.trim().toUpperCase());
      }
    } else {
      if (selectedDatabase && selectedSeries) {
        onLoadHaver(selectedDatabase, selectedSeries);
      }
    }
  };

  const filteredSeries = series.filter(
    (s) =>
      s.name.toLowerCase().includes(seriesSearch.toLowerCase()) ||
      s.description.toLowerCase().includes(seriesSearch.toLowerCase())
  );

  return (
    <div className="bg-white rounded-2xl p-6 shadow-card border border-slate-100">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Data Source</h2>

      {/* Source Toggle */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setDataSource('yahoo')}
          className={`flex-1 py-2.5 px-4 rounded-xl font-medium transition-all duration-200 ${dataSource === 'yahoo'
              ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/25'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
        >
          Yahoo Finance
        </button>
        <button
          onClick={() => setDataSource('haver')}
          className={`flex-1 py-2.5 px-4 rounded-xl font-medium transition-all duration-200 ${dataSource === 'haver'
              ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/25'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
        >
          Haver Analytics
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {dataSource === 'yahoo' ? (
          /* Yahoo Finance Input */
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-2">
              Stock Ticker
            </label>
            <input
              type="text"
              value={yahooTicker}
              onChange={(e) => setYahooTicker(e.target.value)}
              placeholder="e.g., NVDA, AAPL, MSFT"
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all"
            />
          </div>
        ) : (
          /* Haver Analytics Hierarchical Selection */
          <>
            {/* Database Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-600 mb-2">
                Database
              </label>
              {loadingDatabases ? (
                <div className="flex items-center gap-2 text-slate-500 py-3">
                  <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                  Loading databases...
                </div>
              ) : (
                <select
                  value={selectedDatabase}
                  onChange={(e) => setSelectedDatabase(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all cursor-pointer"
                >
                  <option value="">Select a database...</option>
                  {databases.map((db) => (
                    <option key={db.code} value={db.code}>
                      {db.code} - {db.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Series Selection */}
            {selectedDatabase && (
              <div>
                <label className="block text-sm font-medium text-slate-600 mb-2">
                  Series
                </label>
                {loadingSeries ? (
                  <div className="flex items-center gap-2 text-slate-500 py-3">
                    <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                    Loading series...
                  </div>
                ) : (
                  <>
                    <input
                      type="text"
                      value={seriesSearch}
                      onChange={(e) => setSeriesSearch(e.target.value)}
                      placeholder="Search series..."
                      className="w-full px-4 py-2 mb-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:border-brand-500 text-sm"
                    />
                    <div className="max-h-48 overflow-y-auto bg-slate-50 rounded-xl border border-slate-200">
                      {filteredSeries.slice(0, 100).map((s) => (
                        <button
                          key={s.name}
                          type="button"
                          onClick={() => setSelectedSeries(s.name)}
                          className={`w-full text-left px-4 py-2.5 border-b border-slate-100 last:border-b-0 transition-colors ${selectedSeries === s.name
                              ? 'bg-brand-50 text-brand-600'
                              : 'hover:bg-slate-100 text-slate-700'
                            }`}
                        >
                          <div className="font-mono text-sm">{s.name}</div>
                          <div className="text-xs text-slate-500 truncate">
                            {s.description}
                          </div>
                        </button>
                      ))}
                      {filteredSeries.length === 0 && (
                        <div className="px-4 py-3 text-slate-400 text-sm">
                          No series found
                        </div>
                      )}
                      {filteredSeries.length > 100 && (
                        <div className="px-4 py-2 text-slate-400 text-xs text-center">
                          Showing first 100 results. Use search to filter.
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}
          </>
        )}

        {/* Load Button */}
        <button
          type="submit"
          disabled={
            loading ||
            (dataSource === 'yahoo' && !yahooTicker.trim()) ||
            (dataSource === 'haver' && (!selectedDatabase || !selectedSeries))
          }
          className="w-full py-3 bg-gradient-to-r from-brand-500 to-brand-600 text-white font-semibold rounded-xl hover:from-brand-600 hover:to-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-brand-500/25"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Loading...
            </span>
          ) : (
            'Load Data'
          )}
        </button>
      </form>
    </div>
  );
}

