import { useCallback, useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Brush,
  ReferenceArea,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import type { ChartDataPoint, DateRange } from '../types';

interface TimeSeriesChartProps {
  data: ChartDataPoint[];
  ticker: string;
  currency?: string | null;
  selectedRange: DateRange | null;
  onRangeChange: (range: DateRange | null) => void;
}

// Custom tooltip component
const CustomTooltip = ({ active, payload, currency }: any) => {
  if (active && payload && payload.length) {
    const point = payload[0].payload as ChartDataPoint;
    return (
      <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl p-3 shadow-lg ring-1 ring-black/5">
        <p className="text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-0.5">{point.formattedDate}</p>
        <p className="text-xl font-mono font-bold text-slate-800">
          {currency ? '' : '$'}{point.value.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })} {currency || ''}
        </p>
      </div>
    );
  }
  return null;
};


// Format X axis tick
const formatXAxis = (timestamp: string) => {
  try {
    return format(parseISO(timestamp), 'MMM yyyy');
  } catch {
    return timestamp;
  }
};

export function TimeSeriesChart({
  data,
  ticker,
  currency,
  selectedRange,
  onRangeChange,
}: TimeSeriesChartProps) {
  // State for drag selection
  const [refAreaLeft, setRefAreaLeft] = useState<string | null>(null);
  const [refAreaRight, setRefAreaRight] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Calculate min/max for Y axis
  const yDomain = useMemo(() => {
    if (data.length === 0) return [0, 100];
    const values = data.map((d) => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.1;
    return [min - padding, max + padding];
  }, [data]);

  // Calculate change for selected range
  const rangeStats = useMemo(() => {
    if (!selectedRange || data.length === 0) return null;

    const startValue = data[selectedRange.startIndex]?.value;
    const endValue = data[selectedRange.endIndex]?.value;

    if (startValue === undefined || endValue === undefined) return null;

    const change = endValue - startValue;
    const changePercent = (change / startValue) * 100;

    return {
      startValue,
      endValue,
      change,
      changePercent,
    };
  }, [selectedRange, data]);

  // Mouse Event Handlers for Selection
  const onMouseDown = (e: any) => {
    if (e && e.activeLabel) {
      setRefAreaLeft(e.activeLabel);
      setIsDragging(true);
      setRefAreaRight(e.activeLabel);
    }
  };

  const onMouseMove = (e: any) => {
    if (isDragging && refAreaLeft && e && e.activeLabel) {
      setRefAreaRight(e.activeLabel);
    }
  };

  const onMouseUp = () => {
    if (isDragging && refAreaLeft && refAreaRight) {
      // Find indices
      let leftIndex = data.findIndex(d => d.timestamp === refAreaLeft);
      let rightIndex = data.findIndex(d => d.timestamp === refAreaRight);

      // Swap if dragged backwards
      if (leftIndex > rightIndex) {
        [leftIndex, rightIndex] = [rightIndex, leftIndex];
      }

      // Ensure minimal selection
      if (rightIndex - leftIndex > 0) {
        const startPoint = data[leftIndex];
        const endPoint = data[rightIndex];

        onRangeChange({
          startDate: startPoint.timestamp.split('T')[0],
          endDate: endPoint.timestamp.split('T')[0],
          startIndex: leftIndex,
          endIndex: rightIndex,
        });
      } else {
        // Single click clears selection
        onRangeChange(null);
      }
    }

    setRefAreaLeft(null);
    setRefAreaRight(null);
    setIsDragging(false);
  };

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-3xl p-10 flex items-center justify-center h-[500px] shadow-sm border border-slate-100">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-slate-50 rounded-2xl flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
          </div>
          <p className="text-slate-600 font-medium">No data loaded</p>
          <p className="text-slate-400 text-sm mt-1">Select a source to begin</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 h-[580px] flex flex-col select-none">
      {/* Compact Header */}
      <div className="flex items-end justify-between mb-4 flex-shrink-0 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 font-mono tracking-tight leading-none">
              {ticker}
            </h2>
            <div className="flex items-center gap-2 mt-1.5">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500 uppercase tracking-wider">
                {data.length} Points
              </span>
              <span className="text-xs text-slate-400">
                {data[0]?.formattedDate} — {data[data.length - 1]?.formattedDate}
              </span>
            </div>
          </div>

          {/* Range Stats (Compact) */}
          {selectedRange && rangeStats && (
            <div className="hidden lg:flex items-center gap-3 pl-4 border-l border-slate-200 ml-4">
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Selected Range</span>
                <span className="text-sm font-mono font-medium text-slate-700">
                  {selectedRange.startDate} → {selectedRange.endDate}
                </span>
              </div>
              <div className={`flex flex-col items-end ${rangeStats.change >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                <span className="text-[10px] font-bold uppercase tracking-wider opacity-80">Change</span>
                <span className="text-sm font-mono font-bold">
                  {rangeStats.change >= 0 ? '+' : ''}{rangeStats.changePercent.toFixed(2)}%
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="text-right">
          <p className="text-3xl font-mono font-bold text-slate-900 leading-none">
            {currency ? '' : '$'}{data[data.length - 1]?.value.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
          {currency && (
            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mt-1">
              {currency}
            </p>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0 w-full relative group">
        <p className="absolute top-2 right-4 z-10 text-xs text-slate-400 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity bg-white/80 backdrop-blur px-2 py-1 rounded border border-slate-100">
          Click & drag to select range
        </p>

        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 5, right: 5, left: 0, bottom: 5 }}
            onMouseDown={onMouseDown}
            onMouseMove={onMouseMove}
            onMouseUp={onMouseUp}
          >
            <defs>
              <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#3b82f6" />
                <stop offset="100%" stopColor="#6366f1" />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="0" stroke="#f1f5f9" vertical={false} />

            <XAxis
              dataKey="timestamp"
              tickFormatter={formatXAxis}
              stroke="#e2e8f0"
              tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 500 }}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              minTickGap={30}
              dy={10}
            />

            <YAxis
              domain={yDomain}
              stroke="#e2e8f0"
              tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 500 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${currency ? '' : '$'}${value.toFixed(0)}`}
              width={60}
            />

            <Tooltip content={<CustomTooltip currency={currency} />} cursor={{ stroke: '#cbd5e1', strokeWidth: 1 }} />

            {/* Selected Range Highlight */}
            {selectedRange && (
              <ReferenceArea
                x1={data[selectedRange.startIndex]?.timestamp}
                x2={data[selectedRange.endIndex]?.timestamp}
                strokeOpacity={0}
                fill="#f59e0b"
                fillOpacity={0.1}
              />
            )}

            {/* Dragging Selection Highlight */}
            {refAreaLeft && refAreaRight && (
              <ReferenceArea
                x1={refAreaLeft}
                x2={refAreaRight}
                strokeOpacity={0}
                fill="#3b82f6"
                fillOpacity={0.2}
              />
            )}

            <Line
              type="monotone"
              dataKey="value"
              stroke="url(#lineGradient)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, fill: '#3b82f6', stroke: '#fff', strokeWidth: 2 }}
              isAnimationActive={false}
            />

            <Brush
              dataKey="timestamp"
              height={30}
              stroke="#cbd5e1"
              fill="#f8fafc"
              tickFormatter={() => ''}
              travellerWidth={10}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
