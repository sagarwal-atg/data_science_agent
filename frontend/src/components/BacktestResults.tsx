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
  fullTimeSeries?: ChartDataPoint[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-cream-50/95 backdrop-blur-sm border border-cream-300 rounded-xl p-3 shadow-lg">
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

const formatDate = (dateStr: string) => {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy');
  } catch {
    return dateStr;
  }
};

const formatXAxis = (timestamp: string) => {
  try {
    return format(parseISO(timestamp), 'MMM d');
  } catch {
    return timestamp;
  }
};

export function BacktestResults({ result, loading, error, fullTimeSeries }: BacktestResultsProps) {
  const forecastMap = useMemo(() => {
    if (!result || result.windows.length === 0) return new Map<string, number>();

    const map = new Map<string, number>();
    result.windows.forEach((window) => {
      window.timestamps.forEach((ts, i) => {
        const dateKey = ts.split('T')[0];
        map.set(dateKey, window.forecast_values[i]);
      });
    });

    return map;
  }, [result]);

  const chartData = useMemo(() => {
    if (!result) return [];

    if (fullTimeSeries && fullTimeSeries.length > 0) {
      return fullTimeSeries.map((point) => {
        const dateKey = point.timestamp.split('T')[0];
        const forecastValue = forecastMap.get(dateKey);

        return {
          date: point.timestamp,
          actual: point.value,
          forecast: forecastValue ?? null,
        };
      });
    }

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

  const yDomain = useMemo(() => {
    if (chartData.length === 0) return [0, 100];
    const allValues = chartData.flatMap((d) => [d.actual, d.forecast]).filter((v): v is number => v !== null);
    if (allValues.length === 0) return [0, 100];
    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    const padding = (max - min) * 0.1;
    return [min - padding, max + padding];
  }, [chartData]);

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
      <div className="bg-white rounded-2xl p-6 shadow-card border border-cream-200">
        <div className="flex flex-col items-center justify-center py-10">
          <div className="w-10 h-10 border-3 border-lavender-300 border-t-lavender-500 rounded-full animate-spin mb-4" />
          <p className="text-slate-600 font-medium">Running backtest...</p>
          <p className="text-slate-400 text-sm mt-1">Generating forecasts with Synthefy</p>
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
            <h3 className="text-coral-600 font-semibold">Backtest Failed</h3>
            <p className="text-slate-600 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const getMapeQuality = (mape: number) => {
    if (mape < 10) return { label: 'Excellent', color: 'text-sage-600', bg: 'bg-sage-50' };
    if (mape < 20) return { label: 'Good', color: 'text-sage-500', bg: 'bg-sage-50' };
    if (mape < 30) return { label: 'Fair', color: 'text-clay-600', bg: 'bg-clay-50' };
    return { label: 'Poor', color: 'text-coral-600', bg: 'bg-coral-50' };
  };

  const mapeQuality = getMapeQuality(result.mape);

  return (
    <div className="bg-white rounded-2xl p-5 shadow-card border border-cream-200 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Backtest Results</h2>
          <p className="text-slate-500 text-sm mt-0.5">Rolling forecast validation</p>
        </div>
        <span className="px-2.5 py-1 rounded-lg text-xs font-medium bg-lavender-100 text-lavender-600">
          {result.windows.length} windows
        </span>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* MAPE Card */}
        <div className={`col-span-2 ${mapeQuality.bg} rounded-xl p-4 border border-cream-200`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                MAPE (Mean Abs % Error)
              </p>
              <div className="flex items-baseline gap-2">
                <span className={`text-3xl font-mono font-bold ${mapeQuality.color}`}>
                  {result.mape.toFixed(2)}%
                </span>
                <span className={`text-sm font-semibold ${mapeQuality.color}`}>
                  {mapeQuality.label}
                </span>
              </div>
            </div>
            <div className="text-4xl opacity-30">📊</div>
          </div>
        </div>

        {/* MAE */}
        <div className="bg-cream-50 rounded-xl p-3 border border-cream-200">
          <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400 mb-1">MAE</p>
          <span className="text-xl font-mono font-bold text-slate-700">{result.mae.toFixed(2)}</span>
        </div>

        {/* Total Points */}
        <div className="bg-cream-50 rounded-xl p-3 border border-cream-200">
          <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400 mb-1">Points</p>
          <span className="text-xl font-mono font-bold text-slate-700">{result.total_points}</span>
        </div>
      </div>

      {/* Config */}
      <div className="flex flex-wrap gap-2 text-xs">
        {[
          { label: 'Cutoff', value: formatDate(result.cutoff_date) },
          { label: 'Window', value: result.forecast_window },
          { label: 'Stride', value: result.stride },
          { label: 'Freq', value: result.frequency },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-1.5 px-2.5 py-1 bg-cream-100 rounded-lg">
            <span className="text-slate-500">{item.label}:</span>
            <span className="font-mono font-medium text-slate-700">{item.value}</span>
          </div>
        ))}
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="bg-cream-50 rounded-xl p-4 border border-cream-200">
          <h4 className="text-sm font-medium text-slate-700 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-lavender-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
            Actual vs Forecast
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E3E3DF" vertical={false} />

                {backtestRegion && (
                  <ReferenceArea
                    x1={backtestRegion.start}
                    x2={backtestRegion.end}
                    fill="#9A7BB4"
                    fillOpacity={0.08}
                    stroke="#9A7BB4"
                    strokeOpacity={0.2}
                    strokeDasharray="3 3"
                  />
                )}

                {backtestRegion && (
                  <ReferenceLine
                    x={backtestRegion.start}
                    stroke="#9A7BB4"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                    label={{
                      value: 'Cutoff',
                      position: 'top',
                      fill: '#9A7BB4',
                      fontSize: 10,
                      fontWeight: 'bold',
                    }}
                  />
                )}

                <XAxis
                  dataKey="date"
                  tickFormatter={formatXAxis}
                  stroke="#E3E3DF"
                  tick={{ fill: '#A8A89E', fontSize: 10 }}
                  tickLine={false}
                  axisLine={{ stroke: '#E3E3DF' }}
                  minTickGap={50}
                />
                <YAxis
                  domain={yDomain}
                  stroke="#E3E3DF"
                  tick={{ fill: '#A8A89E', fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  width={55}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="top"
                  height={32}
                  iconType="line"
                  wrapperStyle={{ fontSize: '11px' }}
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  name="Actual"
                  stroke="#E5684A"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: '#E5684A' }}
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  name="Forecast"
                  stroke="#9A7BB4"
                  strokeWidth={2.5}
                  dot={false}
                  activeDot={{ r: 4, fill: '#9A7BB4' }}
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Windows */}
      {result.windows.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
            <svg className="w-4 h-4 text-lavender-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
            Windows ({result.windows.length})
          </h4>
          <div className="space-y-1.5 max-h-40 overflow-y-auto">
            {result.windows.map((window, index) => {
              const windowErrors = window.actual_values.map((a, i) =>
                a !== 0 ? Math.abs((a - window.forecast_values[i]) / a) * 100 : 0
              );
              const windowMape = windowErrors.reduce((sum, e) => sum + e, 0) / windowErrors.length;

              return (
                <div
                  key={index}
                  className="flex items-center justify-between p-2.5 bg-cream-50 rounded-lg border border-cream-200"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 flex items-center justify-center bg-lavender-100 text-lavender-600 text-[10px] font-bold rounded">
                      {index + 1}
                    </span>
                    <div>
                      <p className="text-xs font-mono text-slate-700">
                        {formatDate(window.target_start)} → {formatDate(window.target_end)}
                      </p>
                    </div>
                  </div>
                  <span className={`text-xs font-mono font-bold ${getMapeQuality(windowMape).color}`}>
                    {windowMape.toFixed(1)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
