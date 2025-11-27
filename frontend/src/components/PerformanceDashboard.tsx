import { useEffect, useState } from 'react';
import {
  fetchStoredBacktests,
  fetchStoredBacktestDetail,
} from '../api';
import type {
  AssetClass,
  StoredBacktestSummary,
  StoredBacktestDetail,
} from '../types';

const ASSET_CLASS_OPTIONS: { id: AssetClass; label: string }[] = [
  { id: 'sp500', label: 'S&P 500' },
  { id: 'crypto', label: 'Crypto' },
  { id: 'forex', label: 'Forex' },
  { id: 'macro', label: 'Macro' },
];

export function PerformanceDashboard() {
  const [assetClass, setAssetClass] = useState<AssetClass>('sp500');
  const [summaries, setSummaries] = useState<StoredBacktestSummary[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [detail, setDetail] = useState<StoredBacktestDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  const loadSummaries = async () => {
    setLoading(true);
    setError(null);
    setSummaries([]);
    setDetail(null);
    setSelectedSymbol(null);
    try {
      const results = await fetchStoredBacktests(assetClass, 100);
      setSummaries(results);
      if (results.length > 0) {
        setSelectedSymbol(results[0].symbol);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load backtests';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (symbol: string) => {
    setDetailLoading(true);
    setDetailError(null);
    try {
      const response = await fetchStoredBacktestDetail(assetClass, symbol, 750);
      setDetail(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load details';
      setDetailError(message);
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    loadSummaries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assetClass]);

  useEffect(() => {
    if (selectedSymbol) {
      loadDetail(selectedSymbol);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSymbol]);

  const handleSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
  };

  return (
    <div className="bg-white border border-cream-200 rounded-2xl p-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            Forecast Performance
          </p>
          <h2 className="text-lg font-bold text-slate-800">Historical Backtest Database</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={assetClass}
            onChange={(e) => setAssetClass(e.target.value as AssetClass)}
            className="px-3 py-2 rounded-xl border border-cream-300 text-sm bg-cream-50"
          >
            {ASSET_CLASS_OPTIONS.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            onClick={loadSummaries}
            className="px-3 py-2 rounded-xl border border-cream-300 text-sm bg-white hover:bg-cream-100 transition-colors"
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error ? (
        <div className="bg-coral-50 border border-coral-200 rounded-xl p-4 text-sm text-coral-700">
          {error}
        </div>
      ) : (
        <div className="grid md:grid-cols-5 gap-4">
          <div className="md:col-span-2 space-y-2">
            {loading ? (
              <div className="flex items-center justify-center py-12 text-slate-400">
                <div className="w-6 h-6 border-2 border-slate-200 border-t-coral-400 rounded-full animate-spin" />
              </div>
            ) : summaries.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-sm">
                No stored backtests yet. Run the pipeline first.
              </div>
            ) : (
              <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
                {summaries.map((summary) => (
                  <button
                    key={summary.run_key}
                    onClick={() => handleSelect(summary.symbol)}
                    className={`w-full text-left px-3 py-2 rounded-xl border transition-all ${selectedSymbol === summary.symbol
                        ? 'border-coral-400 bg-coral-50'
                        : 'border-cream-200 bg-cream-50 hover:border-coral-200'
                      }`}
                  >
                    <div className="flex items-center justify-between text-sm font-semibold text-slate-800">
                      <span>{summary.symbol}</span>
                      <span className="text-xs font-normal text-slate-500">
                        {summary.run_week ?? 'N/A'}
                      </span>
                    </div>
                    {summary.name && (
                      <p className="text-xs text-slate-500 truncate">{summary.name}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-xs">
                      <span className="px-2 py-0.5 rounded-full bg-white text-coral-600 font-semibold">
                        MAPE {summary.mape?.toFixed(2) ?? '—'}%
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-white text-slate-500 font-semibold">
                        MAE {summary.mae?.toFixed(3) ?? '—'}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="md:col-span-3">
            {detailLoading ? (
              <div className="flex items-center justify-center py-16 text-slate-400">
                <div className="w-8 h-8 border-2 border-slate-200 border-t-lavender-500 rounded-full animate-spin" />
              </div>
            ) : detailError ? (
              <div className="bg-coral-50 border border-coral-200 rounded-xl p-4 text-sm text-coral-700">
                {detailError}
              </div>
            ) : detail ? (
              <div className="space-y-4">
                <div className="p-4 bg-cream-50 border border-cream-200 rounded-xl">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wide">Latest Run</p>
                      <h3 className="text-lg font-semibold text-slate-800">
                        {detail.summary.symbol}{' '}
                        <span className="text-sm text-slate-500 font-normal">
                          {detail.summary.name}
                        </span>
                      </h3>
                    </div>
                    <div className="text-right text-xs text-slate-500">
                      <p>{detail.summary.run_week ?? 'N/A'}</p>
                      <p>{detail.summary.run_timestamp?.replace('T', ' ').slice(0, 16) ?? ''}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3 mt-4 text-center">
                    <div className="bg-white rounded-lg p-3 border border-cream-200">
                      <p className="text-[11px] text-slate-500">MAPE</p>
                      <p className="text-lg font-semibold text-coral-600">
                        {detail.summary.mape?.toFixed(2) ?? '—'}%
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-cream-200">
                      <p className="text-[11px] text-slate-500">MAE</p>
                      <p className="text-lg font-semibold text-slate-700">
                        {detail.summary.mae?.toFixed(4) ?? '—'}
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-cream-200">
                      <p className="text-[11px] text-slate-500">Samples</p>
                      <p className="text-lg font-semibold text-slate-700">
                        {detail.summary.total_points}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 text-[11px] text-slate-500">
                    Horizon {detail.summary.forecast_window} • stride {detail.summary.stride} •{' '}
                    {detail.summary.frequency}
                  </div>
                </div>

                <div className="border border-cream-200 rounded-xl overflow-hidden">
                  <div className="bg-cream-100 px-3 py-2 flex items-center justify-between text-xs font-semibold text-slate-600">
                    <span>Forecast Windows ({detail.windows.length})</span>
                    <span>Actual vs Forecast</span>
                  </div>
                  {detail.windows.length === 0 ? (
                    <div className="text-center py-8 text-slate-500 text-sm">
                      No window-level data available
                    </div>
                  ) : (
                    <div className="max-h-[320px] overflow-y-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-white text-slate-500">
                          <tr>
                            <th className="text-left px-3 py-2 font-medium">Target</th>
                            <th className="text-right px-3 py-2 font-medium">Actual</th>
                            <th className="text-right px-3 py-2 font-medium">Forecast</th>
                            <th className="text-right px-3 py-2 font-medium">Error</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detail.windows.slice(0, 150).map((window) => {
                            const actual = window.actual_value;
                            const forecast = window.forecast_value;
                            const err = actual !== 0 ? ((forecast - actual) / actual) * 100 : 0;
                            return (
                              <tr
                                key={`${window.target_start}-${window.history_start}`}
                                className="odd:bg-white even:bg-cream-50"
                              >
                                <td className="px-3 py-2 font-mono text-[11px] text-slate-600">
                                  {window.target_start.slice(0, 10)}
                                </td>
                                <td className="px-3 py-2 text-right text-slate-800">
                                  {actual.toFixed(2)}
                                </td>
                                <td className="px-3 py-2 text-right text-slate-800">
                                  {forecast.toFixed(2)}
                                </td>
                                <td className={`px-3 py-2 text-right ${err >= 0 ? 'text-coral-600' : 'text-sage-600'}`}>
                                  {err.toFixed(2)}%
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-sm">
                Select an asset to view detailed performance.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
