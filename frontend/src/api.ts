import axios from 'axios';
import type {
  TimeSeriesData,
  HaverDatabase,
  HaverSeries,
  HaverTimeSeriesData,
  SearchResult,
  SearchRequest,
  BacktestResult,
  BacktestRequest,
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

