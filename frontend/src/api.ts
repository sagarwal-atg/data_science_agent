import axios from 'axios';
import type {
  TimeSeriesData,
  HaverDatabase,
  HaverSeries,
  HaverTimeSeriesData,
  CryptoSymbol,
  CryptoTimeSeriesData,
  ForexPair,
  ForexTimeSeriesData,
  SearchResult,
  SearchRequest,
  BacktestResult,
  BacktestRequest,
  CriticalEventsResult,
  CriticalEventsRequest,
} from './types';

const API_BASE = '/api';

// Yahoo Finance API
export async function fetchYahooData(
  ticker: string,
  startDate?: string,
  endDate?: string
): Promise<TimeSeriesData> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const url = `${API_BASE}/yahoo/${ticker}${params.toString() ? `?${params}` : ''}`;
  const response = await axios.get<TimeSeriesData>(url);
  return response.data;
}

// Haver Analytics API
export async function fetchHaverDatabases(): Promise<HaverDatabase[]> {
  const response = await axios.get<{ databases: HaverDatabase[] }>(
    `${API_BASE}/haver/databases`
  );
  return response.data.databases;
}

export async function fetchHaverSeries(database: string): Promise<HaverSeries[]> {
  const response = await axios.get<{ database: string; series: HaverSeries[] }>(
    `${API_BASE}/haver/series/${database}`
  );
  return response.data.series;
}

export async function fetchHaverData(
  database: string,
  series: string
): Promise<HaverTimeSeriesData> {
  const response = await axios.get<HaverTimeSeriesData>(
    `${API_BASE}/haver/${database}/${series}`
  );
  return response.data;
}

// Crypto API
export async function fetchPopularCryptos(): Promise<CryptoSymbol[]> {
  const response = await axios.get<{ cryptos: CryptoSymbol[] }>(
    `${API_BASE}/crypto/popular`
  );
  return response.data.cryptos;
}

export async function fetchCryptoData(
  ticker: string,
  startDate?: string,
  endDate?: string
): Promise<CryptoTimeSeriesData> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const url = `${API_BASE}/crypto/${ticker}${params.toString() ? `?${params}` : ''}`;
  const response = await axios.get<CryptoTimeSeriesData>(url);
  return response.data;
}

// Forex API
export async function fetchPopularForexPairs(): Promise<ForexPair[]> {
  const response = await axios.get<{ pairs: ForexPair[] }>(
    `${API_BASE}/forex/popular`
  );
  return response.data.pairs;
}

export async function fetchForexData(
  pair: string,
  startDate?: string,
  endDate?: string
): Promise<ForexTimeSeriesData> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const url = `${API_BASE}/forex/${pair}${params.toString() ? `?${params}` : ''}`;
  const response = await axios.get<ForexTimeSeriesData>(url);
  return response.data;
}

// Search API
export async function searchTimeSeriesEvent(
  request: SearchRequest
): Promise<SearchResult> {
  const response = await axios.post<SearchResult>(`${API_BASE}/search`, request);
  return response.data;
}

// Backtest API
export async function runBacktest(
  request: BacktestRequest
): Promise<BacktestResult> {
  const response = await axios.post<BacktestResult>(`${API_BASE}/backtest`, request);
  return response.data;
}

// Critical Events API
export async function searchCriticalEvents(
  request: CriticalEventsRequest
): Promise<CriticalEventsResult> {
  const response = await axios.post<CriticalEventsResult>(`${API_BASE}/critical-events`, request);
  return response.data;
}

