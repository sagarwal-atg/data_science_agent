"""Backtest service using Synthefy API.

Note: Requires Python 3.10+ due to synthefy SDK type hints.
"""

import os
from typing import List, Tuple

import pandas as pd
from pydantic import BaseModel
from synthefy.data_models import ForecastV2Request
from synthefy.api_client import SynthefyAsyncAPIClient
from pandas.tseries.frequencies import to_offset

class BacktestWindow(BaseModel):
    """A single backtest window result."""
    
    history_start: str
    history_end: str
    target_start: str
    target_end: str
    actual_values: List[float]
    forecast_values: List[float]
    timestamps: List[str]


class BacktestResult(BaseModel):
    """Backtest result with metrics."""
    
    ticker: str
    cutoff_date: str
    forecast_window: str
    stride: str
    frequency: str
    windows: List[BacktestWindow]
    mape: float
    mae: float
    total_points: int


def get_synthefy_api_key() -> str:
    """Get Synthefy API key from environment variable."""
    api_key = os.getenv("SYNTHEFY_API_KEY")
    if not api_key:
        raise ValueError(
            "SYNTHEFY_API_KEY environment variable not set. "
            "Please set it with: export SYNTHEFY_API_KEY='your-api-key-here'"
        )
    return api_key


def detect_frequency(timestamps: List[str]) -> Tuple[str, str]:
    """
    Detect the frequency of a time series.
    
    Returns:
        Tuple of (frequency_code, human_readable_name)
        e.g., ('D', 'day'), ('Q', 'quarter'), ('M', 'month')
    """
    print(f"DEBUG [detect_frequency]: Analyzing {len(timestamps)} timestamps")
    
    if len(timestamps) < 2:
        print("DEBUG [detect_frequency]: Less than 2 timestamps, defaulting to daily")
        return 'D', 'day'
    
    # Parse timestamps
    try:
        dates = pd.to_datetime(timestamps)
        print(f"DEBUG [detect_frequency]: First date: {dates[0]}, Last date: {dates[-1]}")
    except Exception as e:
        print(f"DEBUG [detect_frequency]: Failed to parse timestamps: {e}, defaulting to daily")
        return 'D', 'day'
    
    # Calculate median difference between consecutive timestamps
    diffs = dates.diff()[1:]
    median_diff = diffs.median()
    
    days = median_diff.days
    print(f"DEBUG [detect_frequency]: Median difference between timestamps: {days} days")
    
    # Classify based on median difference
    if days <= 1:
        freq = ('D', 'day')
    elif days <= 7:
        freq = ('W', 'week')
    elif days <= 45:
        freq = ('M', 'month')
    elif days <= 100:
        freq = ('Q', 'quarter')
    else:
        freq = ('A', 'year')
    
    print(f"DEBUG [detect_frequency]: Detected frequency: {freq[0]} ({freq[1]})")
    return freq


def get_forecast_window_string(frequency: str) -> str:
    """Get the forecast window string for Synthefy API based on frequency."""
    mapping = {
        'D': '1D',
        'W': '1W',
        'M': '1M',
        'Q': '1Q',
        'A': '1Y',
    }
    result = mapping.get(frequency, '1D')
    print(f"DEBUG [get_forecast_window_string]: Frequency {frequency} -> Window {result}")
    return result


def calculate_mape(actual: List[float], forecast: List[float]) -> float:
    """Calculate Mean Absolute Percentage Error."""
    if len(actual) != len(forecast):
        raise ValueError("Actual and forecast must have same length")
    
    if len(actual) == 0:
        return 0.0
    
    errors = []
    for a, f in zip(actual, forecast):
        if a != 0:
            errors.append(abs((a - f) / a) * 100)
    
    mape = sum(errors) / len(errors) if errors else 0.0
    print(f"DEBUG [calculate_mape]: MAPE = {mape:.2f}% from {len(errors)} non-zero points")
    return mape

def calculate_mae(actual: List[float], forecast: List[float]) -> float:
    """Calculate Mean Absolute Error."""
    if len(actual) != len(forecast):
        raise ValueError("Actual and forecast must have same length")
    
    if len(actual) == 0:
        return 0.0
    
    errors = [abs(a - f) for a, f in zip(actual, forecast)]
    mae = sum(errors) / len(errors)
    print(f"DEBUG [calculate_mae]: MAE = {mae:.4f} from {len(errors)} points")
    return mae


def _get_stride_timedelta(stride: str):
    """Return timedelta for strides such as 1D/7D/1W; otherwise None."""
    try:
        offset = to_offset(str(stride))
        if hasattr(offset, "delta"):
            return offset.delta
        return pd.Timedelta(offset)
    except (ValueError, TypeError):
        return None


def _window_str_to_int(value: str) -> int:
    """Convert window/stride strings (e.g., 1D, 1W, 1M) to approximate integer days."""
    try:
        offset = to_offset(str(value))
        if hasattr(offset, "delta"):
            delta = offset.delta
            return max(int(delta / pd.Timedelta(days=1)), 1)
        delta = pd.Timedelta(offset)
        if delta is not None:
            return max(int(delta / pd.Timedelta(days=1)), 1)
        approx_map = {"M": 30, "Q": 90, "Y": 365}
        base = str(value).upper()
        for token, approx in approx_map.items():
            if token in base:
                return approx
        return max(int(getattr(offset, "n", 1)), 1)
    except Exception:
        return 1


async def run_backtest(
    ticker: str,
    timestamps: List[str],
    values: List[float],
    start_date: str,
    end_date: str,
) -> BacktestResult:
    """
    Run a backtest on a time series using Synthefy.
    
    Args:
        ticker: The ticker/series identifier
        timestamps: All timestamps in the time series
        values: All values in the time series
        start_date: Start of the selected region (cutoff date)
        end_date: End of the selected region
        
    Returns:
        BacktestResult with forecast windows and metrics
    """
    print("=" * 60)
    print("DEBUG [run_backtest]: Starting backtest")
    print(f"DEBUG [run_backtest]: Ticker: {ticker}")
    print(f"DEBUG [run_backtest]: Total data points: {len(timestamps)}")
    print(f"DEBUG [run_backtest]: Selected region: {start_date} to {end_date}")
    print("=" * 60)
    
    # Get API key
    api_key = get_synthefy_api_key()
    print(f"DEBUG [run_backtest]: API key loaded (length: {len(api_key)})")
    
    # Detect frequency
    freq_code, freq_name = detect_frequency(timestamps)
    forecast_window = get_forecast_window_string(freq_code)
    stride = forecast_window  # Same as forecast window
    
    print(f"DEBUG [run_backtest]: Forecast window: {forecast_window}")
    print(f"DEBUG [run_backtest]: Stride: {stride}")
    
    # Create DataFrame from all data
    df = pd.DataFrame({
        'date': pd.to_datetime(timestamps),
        'value': values,
    })
    df = df.sort_values('date').reset_index(drop=True)
    
    print(f"DEBUG [run_backtest]: DataFrame created with {len(df)} rows")
    print(f"DEBUG [run_backtest]: Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"DEBUG [run_backtest]: Value range: {df['value'].min():.2f} to {df['value'].max():.2f}")
    
    try:
        # Get dates in the target region
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        series_tz = df["date"].dt.tz
        if series_tz is not None:
            if start_dt.tzinfo is None:
                start_dt = start_dt.tz_localize(series_tz)
            if end_dt.tzinfo is None:
                end_dt = end_dt.tz_localize(series_tz)
        else:
            if start_dt.tzinfo is not None:
                start_dt = start_dt.tz_convert(None)
            if end_dt.tzinfo is not None:
                end_dt = end_dt.tz_convert(None)
        
        target_mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
        target_dates = df.loc[target_mask, 'date'].tolist()
        
        print(f"DEBUG [run_backtest]: Found {len(target_dates)} data points in target region")
        
        if len(target_dates) == 0:
            raise ValueError("No data points in selected region")
        
        # Process windows in batches to avoid overwhelming the API
        # We'll make individual requests for each window
        result_windows: List[BacktestWindow] = []
        all_actuals: List[float] = []
        all_forecasts: List[float] = []
        
        print(f"DEBUG [run_backtest]: Processing {len(target_dates)} rolling windows...")
        
        async with SynthefyAsyncAPIClient(api_key=api_key) as client:
            for i, target_date in enumerate(target_dates):
                # Create a DataFrame for this window
                # History: all data up to (but not including) target_date
                # We include target_date in the df so from_dfs_pre_split can create the target
                window_df = df[df['date'] <= target_date].copy()
                
                if len(window_df) < 10:
                    print(f"DEBUG [run_backtest]: Window {i+1} - Insufficient history, skipping")
                    continue
                
                # Get actual value for this target date
                actual_value = float(df.loc[df['date'] == target_date, 'value'].values[0])
                
                # Use cutoff_date as the day BEFORE target_date
                # This way target_date becomes the forecast target
                history_df = df[df['date'] < target_date].copy()
                if len(history_df) == 0:
                    continue
                    
                cutoff_ts = history_df['date'].max()
                cutoff_str = cutoff_ts.strftime('%Y-%m-%d')
                future_df = df[df["date"] > cutoff_ts]
                if len(future_df) < 1:
                    continue
                
                try:
                    request_kwargs = dict(
                        dfs=[window_df],
                        timestamp_col='date',
                        target_cols=['value'],
                        model='sfm-moe-v1',
                        metadata_cols=[],
                        leak_cols=[],
                    )

                    stride_delta = _get_stride_timedelta(stride)
                    future_end = future_df['date'].max()
                    gap = future_end - cutoff_ts
                    if stride_delta is not None and gap > stride_delta:
                        request_kwargs['num_target_rows'] = 1
                        request_kwargs['forecast_window'] = _window_str_to_int(forecast_window)
                        request_kwargs['stride'] = _window_str_to_int(stride)
                    else:
                        request_kwargs['cutoff_date'] = cutoff_str
                        request_kwargs['forecast_window'] = str(forecast_window)
                        request_kwargs['stride'] = str(stride)

                    request = ForecastV2Request.from_dfs_pre_split(**request_kwargs)
                    
                    if len(request.samples) == 0:
                        continue
                    
                    # Make API call
                    response = await client.forecast(request)
                    
                    if len(response.forecasts) > 0 and len(response.forecasts[0]) > 0:
                        forecast = response.forecasts[0][0]
                        
                        # Get forecast value
                        forecast_value = None
                        if forecast.values:
                            if isinstance(forecast.values[0], list):
                                forecast_value = float(forecast.values[0][0])
                            else:
                                forecast_value = float(forecast.values[0])
                        
                        if forecast_value is not None:
                            all_actuals.append(actual_value)
                            all_forecasts.append(forecast_value)
                            
                            # Get history info from the sample
                            sample = request.samples[0][0]
                            
                            result_windows.append(BacktestWindow(
                                history_start=str(sample.history_timestamps[0]),
                                history_end=str(sample.history_timestamps[-1]),
                                target_start=target_date.strftime('%Y-%m-%dT%H:%M:%S'),
                                target_end=target_date.strftime('%Y-%m-%dT%H:%M:%S'),
                                actual_values=[actual_value],
                                forecast_values=[forecast_value],
                                timestamps=[target_date.strftime('%Y-%m-%dT%H:%M:%S')],
                            ))
                            
                            # Log progress
                            if (i + 1) % 10 == 0 or i < 3 or i == len(target_dates) - 1:
                                print(f"DEBUG [run_backtest]: Window {i+1}/{len(target_dates)} - "
                                      f"Target: {target_date.date()}, Actual: {actual_value:.2f}, "
                                      f"Forecast: {forecast_value:.2f}")
                
                except Exception as e:
                    print(f"DEBUG [run_backtest]: Window {i+1} error: {e}")
                    continue
        
        print("\n" + "=" * 60)
        print(f"DEBUG [run_backtest]: Total windows processed: {len(result_windows)}")
        print(f"DEBUG [run_backtest]: Total data points for metrics: {len(all_actuals)}")
        
        # Calculate overall metrics
        if len(all_actuals) > 0:
            mape = calculate_mape(all_actuals, all_forecasts)
            mae = calculate_mae(all_actuals, all_forecasts)
        else:
            print("DEBUG [run_backtest]: No data points, setting metrics to 0")
            mape = 0.0
            mae = 0.0
        
        result = BacktestResult(
            ticker=ticker,
            cutoff_date=start_date,
            forecast_window=forecast_window,
            stride=stride,
            frequency=freq_name,
            windows=result_windows,
            mape=mape,
            mae=mae,
            total_points=len(all_actuals),
        )
        
        print("=" * 60)
        print("DEBUG [run_backtest]: Backtest completed successfully!")
        print(f"DEBUG [run_backtest]: Final MAPE: {mape:.2f}%")
        print(f"DEBUG [run_backtest]: Final MAE: {mae:.4f}")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print("=" * 60)
        print(f"DEBUG [run_backtest]: ERROR - {type(e).__name__}: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        raise ValueError(f"Backtest failed: {str(e)}")
