import { useMemo, useState } from 'react';
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
  ReferenceLine,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import type { ChartDataPoint, DateRange, CriticalEvent } from '../types';

interface TimeSeriesChartProps {
  data: ChartDataPoint[];
  ticker: string;
  currency?: string | null;
  selectedRange: DateRange | null;
  onRangeChange: (range: DateRange | null) => void;
  onBrushChange?: (range: DateRange | null) => void;
  criticalEvents?: CriticalEvent[];
  showEventMarkers?: boolean;
}

// Custom tooltip component
const CustomTooltip = ({ active, payload, currency }: any) => {
  if (active && payload && payload.length) {
    const point = payload[0].payload as ChartDataPoint;
    return (
      <div className="bg-cream-50/95 backdrop-blur-sm border border-cream-300 rounded-xl p-3 shadow-lg">
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

// Event Markers Overlay Component
function EventMarkersOverlay({ events, data }: { events: any[], data: ChartDataPoint[] }) {
  const [hoveredEvent, setHoveredEvent] = useState<number | null>(null);

  if (!events || events.length === 0) return null;

  const markerPositions = events.map((marker) => {
    const eventDate = marker.event.date || marker.timestamp.split('T')[0];

    let closestIndex = -1;
    let minDiff = Infinity;

    for (let i = 0; i < data.length; i++) {
      const dataDate = data[i].timestamp.split('T')[0];
      const diff = Math.abs(new Date(dataDate).getTime() - new Date(eventDate).getTime());
      if (diff < minDiff) {
        minDiff = diff;
        closestIndex = i;
      }
    }

    const index = closestIndex >= 0 ? closestIndex : 0;

    return {
      ...marker,
      index,
      percentage: data.length > 1 ? index / (data.length - 1) : 0,
    };
  });

  return (
    <div className="absolute bottom-[30px] left-0 right-0 h-8 pointer-events-none z-20">
      {markerPositions.map((marker, idx) => {
        const leftPercent = marker.percentage * 100;
        return (
          <div
            key={`overlay-${marker.event.date}-${idx}`}
            className="absolute pointer-events-auto"
            style={{ left: `${leftPercent}%`, transform: 'translateX(-50%)' }}
            onMouseEnter={() => setHoveredEvent(idx)}
            onMouseLeave={() => setHoveredEvent(null)}
          >
            <div className="relative">
              <div className="w-3 h-3 bg-coral-500 rounded-full border-2 border-white shadow-lg cursor-pointer hover:bg-coral-600 transition-colors" />
              {hoveredEvent === idx && (
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 bg-cream-50 border border-cream-300 rounded-xl p-3 shadow-xl z-50 pointer-events-none">
                  <p className="text-xs font-semibold text-slate-800 mb-1">
                    {marker.event.title || (() => {
                      try {
                        return format(parseISO(marker.event.date), 'MMM d, yyyy');
                      } catch {
                        return marker.event.date;
                      }
                    })()}
                  </p>
                  <p className="text-xs text-slate-600 line-clamp-3">
                    {marker.event.summary}
                  </p>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function TimeSeriesChart({
  data,
  ticker,
  currency,
  selectedRange,
  onRangeChange,
  onBrushChange,
  criticalEvents = [],
  showEventMarkers = false,
}: TimeSeriesChartProps) {
  const [refAreaLeft, setRefAreaLeft] = useState<string | null>(null);
  const [refAreaRight, setRefAreaRight] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const yDomain = useMemo(() => {
    if (data.length === 0) return [0, 100];
    const values = data.map((d) => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.1;
    return [min - padding, max + padding];
  }, [data]);

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

  const eventMarkers = useMemo(() => {
    if (!showEventMarkers || !criticalEvents || criticalEvents.length === 0) return [];

    return criticalEvents.map((event) => {
      const eventDate = event.timestamp.split('T')[0];
      let closestPoint = data[0];
      let minDiff = Infinity;

      for (const point of data) {
        const pointDate = point.timestamp.split('T')[0];
        const diff = Math.abs(new Date(pointDate).getTime() - new Date(eventDate).getTime());
        if (diff < minDiff) {
          minDiff = diff;
          closestPoint = point;
        }
      }

      return {
        ...closestPoint,
        event,
      };
    });
  }, [criticalEvents, showEventMarkers, data]);

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
      let leftIndex = data.findIndex(d => d.timestamp === refAreaLeft);
      let rightIndex = data.findIndex(d => d.timestamp === refAreaRight);

      if (leftIndex > rightIndex) {
        [leftIndex, rightIndex] = [rightIndex, leftIndex];
      }

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
        onRangeChange(null);
      }
    }

    setRefAreaLeft(null);
    setRefAreaRight(null);
    setIsDragging(false);
  };

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-10 flex items-center justify-center h-[480px] shadow-card border border-cream-200">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-cream-100 rounded-2xl flex items-center justify-center">
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
    <div className="bg-white rounded-2xl p-5 shadow-card border border-cream-200 h-[480px] flex flex-col select-none">
      {/* Header */}
      <div className="flex items-end justify-between mb-3 flex-shrink-0 border-b border-cream-200 pb-3">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight leading-none">
              {ticker}
            </h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cream-100 text-slate-500 uppercase tracking-wider">
                {data.length} pts
              </span>
              <span className="text-[11px] text-slate-400">
                {data[0]?.formattedDate} — {data[data.length - 1]?.formattedDate}
              </span>
            </div>
          </div>

          {selectedRange && rangeStats && (
            <div className="hidden lg:flex items-center gap-3 pl-4 border-l border-cream-200 ml-4">
              <div className="flex flex-col">
                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Selected</span>
                <span className="text-xs font-mono font-medium text-slate-600">
                  {selectedRange.startDate} → {selectedRange.endDate}
                </span>
              </div>
              <div className={`flex flex-col items-end ${rangeStats.change >= 0 ? 'text-sage-600' : 'text-coral-600'}`}>
                <span className="text-[9px] font-bold uppercase tracking-wider opacity-80">Change</span>
                <span className="text-xs font-mono font-bold">
                  {rangeStats.change >= 0 ? '+' : ''}{rangeStats.changePercent.toFixed(2)}%
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="text-right">
          <p className="text-2xl font-mono font-bold text-slate-800 leading-none">
            {currency ? '' : '$'}{data[data.length - 1]?.value.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
          {currency && (
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mt-0.5">
              {currency}
            </p>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0 w-full relative group">
        <p className="absolute top-1 right-3 z-10 text-[10px] text-slate-400 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity bg-white/80 backdrop-blur px-2 py-1 rounded border border-cream-200">
          Click & drag to select range
        </p>

        {showEventMarkers && eventMarkers.length > 0 && (
          <EventMarkersOverlay
            events={eventMarkers}
            data={data}
          />
        )}

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
                <stop offset="0%" stopColor="#E5684A" />
                <stop offset="100%" stopColor="#D4512F" />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="0" stroke="#F5EDE3" vertical={false} />

            <XAxis
              dataKey="timestamp"
              tickFormatter={formatXAxis}
              stroke="#E3E3DF"
              tick={{ fill: '#A8A89E', fontSize: 10, fontWeight: 500 }}
              tickLine={false}
              axisLine={{ stroke: '#E3E3DF' }}
              minTickGap={30}
              dy={10}
            />

            <YAxis
              domain={yDomain}
              stroke="#E3E3DF"
              tick={{ fill: '#A8A89E', fontSize: 10, fontWeight: 500 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${currency ? '' : '$'}${value.toFixed(0)}`}
              width={55}
            />

            <Tooltip content={<CustomTooltip currency={currency} />} cursor={{ stroke: '#D1D1CB', strokeWidth: 1 }} />

            {selectedRange && (
              <ReferenceArea
                x1={data[selectedRange.startIndex]?.timestamp}
                x2={data[selectedRange.endIndex]?.timestamp}
                strokeOpacity={0}
                fill="#E5684A"
                fillOpacity={0.08}
              />
            )}

            {refAreaLeft && refAreaRight && (
              <ReferenceArea
                x1={refAreaLeft}
                x2={refAreaRight}
                strokeOpacity={0}
                fill="#E5684A"
                fillOpacity={0.15}
              />
            )}

            <Line
              type="monotone"
              dataKey="value"
              stroke="url(#lineGradient)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, fill: '#E5684A', stroke: '#fff', strokeWidth: 2 }}
              isAnimationActive={false}
            />

            {showEventMarkers && eventMarkers.map((marker, index) => (
              <ReferenceLine
                key={`event-${marker.event.date}-${index}`}
                x={marker.timestamp}
                stroke="#E5684A"
                strokeWidth={1}
                strokeDasharray="3 3"
                strokeOpacity={0.4}
              />
            ))}

            <Brush
              dataKey="timestamp"
              height={28}
              stroke="#D1D1CB"
              fill="#FAF8F5"
              tickFormatter={() => ''}
              travellerWidth={10}
              onChange={(brushData: any) => {
                if (onBrushChange && brushData && brushData.startIndex !== undefined && brushData.endIndex !== undefined) {
                  const startPoint = data[brushData.startIndex];
                  const endPoint = data[brushData.endIndex];

                  if (startPoint && endPoint) {
                    onBrushChange({
                      startDate: startPoint.timestamp.split('T')[0],
                      endDate: endPoint.timestamp.split('T')[0],
                      startIndex: brushData.startIndex,
                      endIndex: brushData.endIndex,
                    });
                  }
                } else if (onBrushChange && (!brushData || brushData.startIndex === undefined)) {
                  if (data.length > 0) {
                    onBrushChange({
                      startDate: data[0].timestamp.split('T')[0],
                      endDate: data[data.length - 1].timestamp.split('T')[0],
                      startIndex: 0,
                      endIndex: data.length - 1,
                    });
                  } else {
                    onBrushChange(null);
                  }
                }
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
