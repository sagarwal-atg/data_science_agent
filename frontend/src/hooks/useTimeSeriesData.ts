import { useState, useCallback } from 'react';
import { format, parseISO } from 'date-fns';
import type { DataSource, ChartDataPoint, DateRange } from '../types';
import { fetchYahooData, fetchHaverData, fetchCryptoData, fetchForexData } from '../api';

interface UseTimeSeriesDataReturn {
  data: ChartDataPoint[];
  loading: boolean;
  error: string | null;
  ticker: string;
  currency: string | null;
  selectedRange: DateRange | null;
  loadYahooData: (ticker: string) => Promise<void>;
  loadHaverData: (database: string, series: string) => Promise<void>;
  loadCryptoData: (ticker: string) => Promise<void>;
  loadForexData: (pair: string) => Promise<void>;
  setSelectedRange: (range: DateRange | null) => void;
}

export function useTimeSeriesData(): UseTimeSeriesDataReturn {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ticker, setTicker] = useState<string>('');
  const [currency, setCurrency] = useState<string | null>(null);
  const [selectedRange, setSelectedRange] = useState<DateRange | null>(null);

  const transformData = useCallback(
    (timestamps: string[], values: number[]): ChartDataPoint[] => {
      return timestamps.map((timestamp, index) => {
        let date: Date;
        let formattedDate: string;
        
        try {
          date = parseISO(timestamp);
          if (isNaN(date.getTime())) {
            // Try parsing as regular date constructor if ISO fails
            date = new Date(timestamp);
          }
          
          if (isNaN(date.getTime())) {
             // Fallback for display if date is still invalid
             formattedDate = timestamp;
             // Keep date object invalid but don't crash format()
          } else {
             formattedDate = format(date, 'MMM d, yyyy');
          }
        } catch (e) {
          formattedDate = timestamp;
          date = new Date(); // Fallback to now or keep invalid? 
        }

        return {
          date: timestamp,
          timestamp,
          value: values[index],
          formattedDate: formattedDate || timestamp,
        };
      });
    },
    []
  );

  const loadYahooData = useCallback(
    async (tickerSymbol: string) => {
      setLoading(true);
      setError(null);
      setSelectedRange(null);

      try {
        const result = await fetchYahooData(tickerSymbol);
        const chartData = transformData(result.timestamps, result.values);
        setData(chartData);
        setTicker(tickerSymbol);
        // Yahoo data might include currency but our current API doesn't return it explicitely in top level
        // We'll assume USD or handle it if we update Yahoo API
        setCurrency(null); 
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch data';
        setError(message);
        setData([]);
        setCurrency(null);
      } finally {
        setLoading(false);
      }
    },
    [transformData]
  );

  const loadHaverData = useCallback(
    async (database: string, series: string) => {
      setLoading(true);
      setError(null);
      setSelectedRange(null);

      try {
        const result = await fetchHaverData(database, series);
        const chartData = transformData(result.timestamps, result.values);
        setData(chartData);
        setTicker(`${series}@${database}`);
        setCurrency(result.currency || null);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch data';
        setError(message);
        setData([]);
        setCurrency(null);
      } finally {
        setLoading(false);
      }
    },
    [transformData]
  );

  const loadCryptoData = useCallback(
    async (tickerSymbol: string) => {
      setLoading(true);
      setError(null);
      setSelectedRange(null);

      try {
        const result = await fetchCryptoData(tickerSymbol);
        const chartData = transformData(result.timestamps, result.values);
        setData(chartData);
        setTicker(result.ticker);
        setCurrency(result.currency);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch data';
        setError(message);
        setData([]);
        setCurrency(null);
      } finally {
        setLoading(false);
      }
    },
    [transformData]
  );

  const loadForexData = useCallback(
    async (pair: string) => {
      setLoading(true);
      setError(null);
      setSelectedRange(null);

      try {
        const result = await fetchForexData(pair);
        const chartData = transformData(result.timestamps, result.values);
        setData(chartData);
        setTicker(`${result.base_currency}/${result.quote_currency}`);
        setCurrency(result.quote_currency);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch data';
        setError(message);
        setData([]);
        setCurrency(null);
      } finally {
        setLoading(false);
      }
    },
    [transformData]
  );

  return {
    data,
    loading,
    error,
    ticker,
    currency,
    selectedRange,
    loadYahooData,
    loadHaverData,
    loadCryptoData,
    loadForexData,
    setSelectedRange,
  };
}

