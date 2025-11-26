// Data source types
export type DataSource = 'yahoo' | 'haver';

// Time series data
export interface TimeSeriesData {
  ticker: string;
  timestamps: string[];
  values: number[];
  data_type?: string;
}

// Haver types
export interface HaverDatabase {
  code: string;
  name: string;
}

export interface HaverSeries {
  name: string;
  description: string;
  start_date?: string;
  end_date?: string;
  frequency?: string;
}

export interface HaverTimeSeriesData {
  database: string;
  series: string;
  description?: string;
  currency?: string;
  timestamps: string[];
  values: number[];
}

// Chart data point
export interface ChartDataPoint {
  date: string;
  timestamp: string;
  value: number;
  formattedDate: string;
}

// Search types
export interface Citation {
  title?: string;
  url: string;
  excerpts: string[];
}

export interface SearchBasis {
  field: string;
  citations: Citation[];
  reasoning: string;
  confidence: string;
}

export interface SearchResult {
  run_id: string;
  status: string;
  content: string;
  basis: SearchBasis[];
}

export interface SearchRequest {
  ticker: string;
  query: string;
  start_date: string;
  end_date: string;
  change_description?: string;
}

// Selection range
export interface DateRange {
  startDate: string;
  endDate: string;
  startIndex: number;
  endIndex: number;
}

// Backtest types
export interface BacktestWindow {
  history_start: string;
  history_end: string;
  target_start: string;
  target_end: string;
  actual_values: number[];
  forecast_values: number[];
  timestamps: string[];
}

export interface BacktestResult {
  ticker: string;
  cutoff_date: string;
  forecast_window: string;
  stride: string;
  frequency: string;
  windows: BacktestWindow[];
  mape: number;
  mae: number;
  total_points: number;
}

export interface BacktestRequest {
  ticker: string;
  timestamps: string[];
  values: number[];
  start_date: string;
  end_date: string;
}

