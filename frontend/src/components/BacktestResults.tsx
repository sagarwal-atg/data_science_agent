import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceArea,
  ReferenceLine,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import type { BacktestResult, ChartDataPoint } from '../types';

interface BacktestResultsProps {
  result: BacktestResult | null;
  loading: boolean;
  error: string | null;
  fullTimeSeries?: ChartDataPoint[];  // Full time series data
}

// Custom tooltip for the chart
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl p-3 shadow-lg ring-1 ring-black/5">
        <p className="text-slate-500 text-xs font-medium mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          entry.value !== null && entry.value !== undefined && (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-xs text-slate-600">{entry.name}:</span>
              <span className="text-sm font-mono font-bold text-slate-800">
                {entry.value?.toFixed(2)}
              </span>
            </div>
          )
        ))}
      </div>
    );
  }
  return null;
};

// Format date for display
const formatDate = (dateStr: string) => {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy');
  } catch {
    return dateStr;
  }
};

// Format axis tick
const formatXAxis = (timestamp: string) => {
  try {
    return format(parseISO(timestamp), 'MMM d');
  } catch {
    return timestamp;
  }
};

export function BacktestResults({ result, loading, error, fullTimeSeries }: BacktestResultsProps) {
  // Create a map of forecast values by date for quick lookup
  const forecastMap = useMemo(() => {
    if (!result || result.windows.length === 0) return new Map<string, number>();

    const map = new Map<string, number>();
    result.windows.forEach((window) => {
      window.timestamps.forEach((ts, i) => {
        // Normalize the date to just the date part
        const dateKey = ts.split('T')[0];
        map.set(dateKey, window.forecast_values[i]);
      });
    });

    return map;
  }, [result]);

  // Prepare chart data combining full time series with forecasts
  const chartData = useMemo(() => {
    if (!result) return [];

    // If we have full time series, use it as the base
    if (fullTimeSeries && fullTimeSeries.length > 0) {
      return fullTimeSeries.map((point) => {
        const dateKey = point.timestamp.split('T')[0];
        const forecastValue = forecastMap.get(dateKey);

        return {
          date: point.timestamp,
          actual: point.value,
          forecast: forecastValue ?? null,  // null if no forecast for this date
        };
      });
    }

    // Fallback to just the backtest data
    const data: { date: string; actual: number; forecast: number | null }[] = [];
    result.windows.forEach((window) => {
      window.timestamps.forEach((ts, i) => {
        data.push({
          date: ts,
          actual: window.actual_values[i],
          forecast: window.forecast_values[i],
        });
      });
    });

    return data;
  }, [result, fullTimeSeries, forecastMap]);

  // Calculate Y domain for chart
  const yDomain = useMemo(() => {
    if (chartData.length === 0) return [0, 100];
    const allValues = chartData.flatMap((d) => [d.actual, d.forecast]).filter((v): v is number => v !== null);
    if (allValues.length === 0) return [0, 100];
    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    const padding = (max - min) * 0.1;
    return [min - padding, max + padding];
  }, [chartData]);

  // Get backtest region bounds for highlighting
  const backtestRegion = useMemo(() => {
    if (!result || result.windows.length === 0) return null;

    const firstWindow = result.windows[0];
    const lastWindow = result.windows[result.windows.length - 1];

    return {
      start: firstWindow.target_start,
      end: lastWindow.target_end,
    };
  }, [result]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-card border border-slate-100">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-12 h-12 border-3 border-indigo-200 border-t-indigo-500 rounded-full animate-spin mb-4" />
          <p className="text-slate-700 text-lg">Running backtest...</p>
          <p className="text-slate-400 text-sm mt-1">
            Generating forecasts with Synthefy
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-card border border-rose-200">
        <div className="flex items-start gap-3">
          <div className="text-2xl">⚠️</div>
          <div>
            <h3 className="text-rose-600 font-semibold">Backtest Failed</h3>
            <p className="text-slate-600 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  // Determine MAPE quality indicator
  const getMapeQuality = (mape: number) => {
    if (mape < 10) return { label: 'Excellent', color: 'text-emerald-600', bg: 'bg-emerald-500/15' };
    if (mape < 20) return { label: 'Good', color: 'text-green-600', bg: 'bg-green-500/15' };
    if (mape < 30) return { label: 'Fair', color: 'text-amber-600', bg: 'bg-amber-500/15' };
    return { label: 'Poor', color: 'text-rose-600', bg: 'bg-rose-500/15' };
  };

  const mapeQuality = getMapeQuality(result.mape);

  return (
    <div className="bg-white rounded-2xl p-6 shadow-card border border-slate-100 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">
            Backtest Results
          </h2>
          <p className="text-slate-500 text-sm mt-0.5">
            Rolling forecast validation using Synthefy
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-500/15 text-indigo-600">
          {result.windows.length} windows
        </span>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* MAPE Card - Main Metric */}
        <div className={`col-span-2 ${mapeQuality.bg} rounded-xl p-4 border border-slate-100`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                MAPE (Mean Absolute Percentage Error)
              </p>
              <div className="flex items-baseline gap-2">
                <span className={`text-4xl font-mono font-bold ${mapeQuality.color}`}>
                  {result.mape.toFixed(2)}%
                </span>
                <span className={`text-sm font-semibold ${mapeQuality.color}`}>
                  {mapeQuality.label}
                </span>
              </div>
            </div>
            <div className="text-5xl opacity-30">📊</div>
          </div>
        </div>

        {/* MAE */}
        <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
            MAE
          </p>
          <span className="text-2xl font-mono font-bold text-slate-800">
            {result.mae.toFixed(2)}
          </span>
        </div>

        {/* Total Points */}
        <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
            Data Points
          </p>
          <span className="text-2xl font-mono font-bold text-slate-800">
            {result.total_points}
          </span>
        </div>
      </div>

      {/* Configuration Info */}
      <div className="flex flex-wrap gap-3 text-sm">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg">
          <span className="text-slate-500">Cutoff:</span>
          <span className="font-mono font-medium text-slate-700">
            {formatDate(result.cutoff_date)}
          </span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg">
          <span className="text-slate-500">Forecast Window:</span>
          <span className="font-mono font-medium text-slate-700">
            {result.forecast_window}
          </span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg">
          <span className="text-slate-500">Stride:</span>
          <span className="font-mono font-medium text-slate-700">
            {result.stride}
          </span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg">
          <span className="text-slate-500">Frequency:</span>
          <span className="font-mono font-medium text-slate-700 capitalize">
            {result.frequency}
          </span>
        </div>
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-xl p-4 border border-slate-200">
          <h4 className="text-sm font-medium text-slate-700 mb-4 flex items-center gap-2">
            <svg
              className="w-4 h-4 text-indigo-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
              />
            </svg>
            {fullTimeSeries ? 'Full Time Series with Backtest' : 'Actual vs Forecast'}
          </h4>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />

                {/* Highlight the backtest region */}
                {backtestRegion && (
                  <ReferenceArea
                    x1={backtestRegion.start}
                    x2={backtestRegion.end}
                    fill="#4f46e5"
                    fillOpacity={0.1}
                    stroke="#4f46e5"
                    strokeOpacity={0.3}
                    strokeDasharray="3 3"
                  />
                )}

                {/* Cutoff line */}
                {backtestRegion && (
                  <ReferenceLine
                    x={backtestRegion.start}
                    stroke="#6366f1"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                    label={{
                      value: 'Cutoff',
                      position: 'top',
                      fill: '#6366f1',
                      fontSize: 10,
                      fontWeight: 'bold',
                    }}
                  />
                )}

                <XAxis
                  dataKey="date"
                  tickFormatter={formatXAxis}
                  stroke="#e2e8f0"
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                  minTickGap={50}
                />
                <YAxis
                  domain={yDomain}
                  stroke="#e2e8f0"
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  width={60}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="top"
                  height={36}
                  iconType="line"
                  wrapperStyle={{ fontSize: '12px' }}
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  name="Ground Truth"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: '#f59e0b' }}
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  name="Forecast"
                  stroke="#4f46e5"
                  strokeWidth={2.5}
                  dot={false}
                  activeDot={{ r: 4, fill: '#4f46e5' }}
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          {fullTimeSeries && (
            <p className="text-xs text-slate-400 mt-2 text-center">
              Shaded region shows the backtest period • Dashed line marks the cutoff date
            </p>
          )}
        </div>
      )}

      {/* Window Details */}
      {result.windows.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-slate-700 mb-3 flex items-center gap-2">
            <svg
              className="w-4 h-4 text-purple-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 10h16M4 14h16M4 18h16"
              />
            </svg>
            Forecast Windows ({result.windows.length})
          </h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {result.windows.map((window, index) => {
              // Calculate window-specific MAPE
              const windowErrors = window.actual_values.map((a, i) =>
                a !== 0 ? Math.abs((a - window.forecast_values[i]) / a) * 100 : 0
              );
              const windowMape = windowErrors.reduce((sum, e) => sum + e, 0) / windowErrors.length;

              return (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 flex items-center justify-center bg-indigo-100 text-indigo-600 text-xs font-bold rounded">
                      {index + 1}
                    </span>
                    <div>
                      <p className="text-sm font-mono text-slate-700">
                        {formatDate(window.target_start)} → {formatDate(window.target_end)}
                      </p>
                      <p className="text-xs text-slate-400">
                        History: {formatDate(window.history_start)} to {formatDate(window.history_end)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`text-sm font-mono font-bold ${getMapeQuality(windowMape).color}`}>
                      {windowMape.toFixed(1)}%
                    </span>
                    <p className="text-xs text-slate-400">MAPE</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
