"""Backtest service using Synthefy API with async concurrent processing.

Note: Requires Python 3.10+ due to synthefy SDK type hints.

This implementation follows Synthefy's recommended async pattern:
- Individual API calls per forecast window
- Concurrent execution with semaphore control
- Delay between requests to prevent rate limiting
"""

import asyncio
import os
from typing import List, Tuple

import pandas as pd
from pydantic import BaseModel
from synthefy.data_models import ForecastV2Request, SingleEvalSamplePayload
from synthefy.api_client import SynthefyAsyncAPIClient
from tqdm import tqdm


# Configuration - following Synthefy's recommended settings
MAX_CONCURRENT_REQUESTS = 24  # Max parallel API calls
REQUEST_DELAY_SECONDS = 1.0  # Delay before each request to prevent rate limiting
MAX_RETRIES = 3  # Number of retries for transient failures


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
    """
    if len(timestamps) < 2:
        return 'D', 'day'
    
    try:
        dates = pd.to_datetime(timestamps)
    except Exception:
        return 'D', 'day'
    
    diffs = dates.diff()[1:]
    median_diff = diffs.median()
    days = median_diff.days
    
    if days <= 1:
        return ('D', 'day')
    elif days <= 7:
        return ('W', 'week')
    elif days <= 45:
        return ('M', 'month')
    elif days <= 100:
        return ('Q', 'quarter')
    else:
        return ('A', 'year')


def get_forecast_window_string(frequency: str) -> str:
    """Get the forecast window string for display based on frequency."""
    mapping = {
        'D': '1D',
        'W': '1W',
        'M': '1M',
        'Q': '1Q',
        'A': '1Y',
    }
    return mapping.get(frequency, '1D')


def calculate_mape(actual: List[float], forecast: List[float]) -> float:
    """Calculate Mean Absolute Percentage Error."""
    if len(actual) != len(forecast) or len(actual) == 0:
        return 0.0
    
    errors = []
    for a, f in zip(actual, forecast):
        if a != 0:
            errors.append(abs((a - f) / a) * 100)
    
    return sum(errors) / len(errors) if errors else 0.0


def calculate_mae(actual: List[float], forecast: List[float]) -> float:
    """Calculate Mean Absolute Error."""
    if len(actual) != len(forecast) or len(actual) == 0:
        return 0.0
    
    errors = [abs(a - f) for a, f in zip(actual, forecast)]
    return sum(errors) / len(errors)


def _process_sample_result(
    sample: List[SingleEvalSamplePayload],
    forecast_row: List,
) -> Tuple[List[float], List[float], BacktestWindow]:
    """
    Process a single forecast result and return actuals, forecasts, and window.
    """
    if len(sample) == 0 or len(forecast_row) == 0:
        return [], [], None
    
    sample_data = sample[0]
    forecast = forecast_row[0]
    
    # Get actual values
    actual_values = []
    if sample_data.target_values:
        for val in sample_data.target_values:
            if val is not None:
                actual_values.append(float(val[0]) if isinstance(val, list) else float(val))
    
    # Get forecast values
    forecast_values = []
    if forecast.values:
        for val in forecast.values:
            if val is not None:
                forecast_values.append(float(val[0]) if isinstance(val, list) else float(val))
    
    # Get timestamps
    target_timestamps = []
    if sample_data.target_timestamps:
        target_timestamps = [str(ts) for ts in sample_data.target_timestamps]
    
    min_len = min(len(actual_values), len(forecast_values))
    if min_len == 0:
        return [], [], None
    
    actual_values = actual_values[:min_len]
    forecast_values = forecast_values[:min_len]
    target_timestamps = target_timestamps[:min_len] if target_timestamps else []
    
    window = BacktestWindow(
        history_start=str(sample_data.history_timestamps[0]) if sample_data.history_timestamps else "",
        history_end=str(sample_data.history_timestamps[-1]) if sample_data.history_timestamps else "",
        target_start=str(sample_data.target_timestamps[0]) if sample_data.target_timestamps else "",
        target_end=str(sample_data.target_timestamps[-1]) if sample_data.target_timestamps else "",
        actual_values=actual_values,
        forecast_values=forecast_values,
        timestamps=target_timestamps,
    )
    
    return actual_values, forecast_values, window


async def _forecast_single_window(
    client: SynthefyAsyncAPIClient,
    sample: List[SingleEvalSamplePayload],
    model: str,
    semaphore: asyncio.Semaphore,
    window_index: int,
    total_windows: int,
    request_delay: float,
    pbar: tqdm,
) -> Tuple[List[float], List[float], BacktestWindow]:
    """
    Forecast a single window asynchronously with concurrency control.
    
    Following Synthefy's recommended async pattern:
    1. Acquire semaphore
    2. Add delay to prevent rate limiting
    3. Make API call
    """
    async with semaphore:
        # Add delay BEFORE request to prevent rate limiting (as per Synthefy docs)
        await asyncio.sleep(request_delay)
        
        # Create request for single window
        request = ForecastV2Request(samples=[sample], model=model)
        
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.forecast(request)
                
                if response.forecasts and len(response.forecasts) > 0:
                    actuals, forecasts, window = _process_sample_result(sample, response.forecasts[0])
                    pbar.update(1)
                    return actuals, forecasts, window
                
                pbar.update(1)
                return [], [], None
                
            except Exception as e:
                error_msg = str(e)
                is_retryable = any(x in error_msg for x in ["502", "503", "504", "timeout", "Bad Gateway"])
                
                if is_retryable and attempt < MAX_RETRIES - 1:
                    wait_time = 2 * (attempt + 1)
                    tqdm.write(f"  ⚠ Window {window_index+1}/{total_windows} retry {attempt+1}, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    tqdm.write(f"  ✗ Window {window_index+1}/{total_windows} failed: {error_msg[:80]}")
                    pbar.update(1)
                    return [], [], None
        
        pbar.update(1)
        return [], [], None


async def run_backtest(
    ticker: str,
    timestamps: List[str],
    values: List[float],
    start_date: str,
    end_date: str,
    forecast_window_rows: int = 1,
    stride_rows: int = 1,
    max_concurrent: int = MAX_CONCURRENT_REQUESTS,
    request_delay: float = REQUEST_DELAY_SECONDS,
    show_progress: bool = True,
) -> BacktestResult:
    """
    Run a backtest on a time series using Synthefy async API.
    
    This implementation follows Synthefy's recommended async pattern:
    - Individual API calls per forecast window
    - Concurrent execution with semaphore control
    - Delay between requests to prevent rate limiting
    
    Args:
        ticker: The ticker/series identifier
        timestamps: All timestamps in the time series
        values: All values in the time series
        start_date: Start of the selected region (where backtesting begins)
        end_date: End of the selected region
        forecast_window_rows: Number of rows to forecast per window (default: 1)
        stride_rows: Number of rows to move forward between windows (default: 1)
        max_concurrent: Maximum concurrent API calls (default: 8)
        request_delay: Delay in seconds before each request (default: 1.0)
        show_progress: Whether to show tqdm progress bar (default: True)
        
    Returns:
        BacktestResult with forecast windows and metrics
    """
    print(f"\n{'='*60}")
    print(f"🔄 Starting backtest for {ticker}")
    print(f"   Data points: {len(timestamps)}, Region: {start_date} to {end_date}")
    print(f"   Window: {forecast_window_rows} rows, Stride: {stride_rows} rows")
    print(f"   Concurrency: {max_concurrent}, Request delay: {request_delay}s")
    print(f"{'='*60}")
    
    api_key = get_synthefy_api_key()
    
    freq_code, freq_name = detect_frequency(timestamps)
    forecast_window_str = get_forecast_window_string(freq_code)
    stride_str = forecast_window_str
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': pd.to_datetime(timestamps),
        'value': values,
    })
    df = df.sort_values('date').reset_index(drop=True)
    
    try:
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
        
        # Filter dataframe to only include data up to end_date
        df = df[df['date'] <= end_dt].copy().reset_index(drop=True)
        print(f"📊 Filtered to {len(df)} rows (up to {end_date})")
        
        # Find target region
        target_mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
        target_indices = df.index[target_mask].tolist()
        
        if len(target_indices) == 0:
            raise ValueError("No data points in selected region")
        
        first_target_idx = target_indices[0]
        num_target_rows = len(df) - first_target_idx
        
        print(f"📊 Target region: {len(target_indices)} data points")
        
        if num_target_rows <= 0:
            raise ValueError("No rows available for backtesting")
        
        if first_target_idx < 10:
            raise ValueError("Not enough history data (need at least 10 rows)")
        
        cutoff_str = df.iloc[first_target_idx]['date'].strftime('%Y-%m-%d')
        
        # Create all forecast windows using from_dfs_pre_split
        print(f"📊 Creating forecast windows...")
        
        request = ForecastV2Request.from_dfs_pre_split(
            dfs=[df],
            timestamp_col='date',
            target_cols=['value'],
            model='sfm-moe-v1',
            num_target_rows=num_target_rows,
            forecast_window=forecast_window_rows,
            stride=stride_rows,
            metadata_cols=[],
            leak_cols=[],
        )
        
        total_windows = len(request.samples)
        print(f"✓ Created {total_windows} forecast windows")
        
        if total_windows == 0:
            raise ValueError("No valid forecast windows could be created")
        
        # Estimate time
        estimated_time = (total_windows / max_concurrent) * (request_delay + 2)  # rough estimate
        print(f"🚀 Running {total_windows} forecasts with {max_concurrent} concurrent requests")
        print(f"⏱️  Estimated time: ~{estimated_time:.0f}s ({estimated_time/60:.1f}min)")
        
        # Process windows concurrently
        result_windows: List[BacktestWindow] = []
        all_actuals: List[float] = []
        all_forecasts: List[float] = []
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async with SynthefyAsyncAPIClient(api_key=api_key) as client:
            pbar = tqdm(
                total=total_windows,
                desc=f"⏳ {ticker}",
                unit="windows",
                disable=not show_progress,
                ncols=80,
            )
            
            # Create tasks for all windows
            tasks = [
                _forecast_single_window(
                    client=client,
                    sample=sample,
                    model=request.model,
                    semaphore=semaphore,
                    window_index=i,
                    total_windows=total_windows,
                    request_delay=request_delay,
                    pbar=pbar,
                )
                for i, sample in enumerate(request.samples)
            ]
            
            # Execute all forecasts concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            pbar.close()
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    tqdm.write(f"  ⚠ Task exception: {result}")
                    continue
                actuals, forecasts, window = result
                if window is not None:
                    all_actuals.extend(actuals)
                    all_forecasts.extend(forecasts)
                    result_windows.append(window)
        
        # Calculate metrics
        if len(all_actuals) > 0:
            mape = calculate_mape(all_actuals, all_forecasts)
            mae = calculate_mae(all_actuals, all_forecasts)
        else:
            mape = 0.0
            mae = 0.0
        
        result = BacktestResult(
            ticker=ticker,
            cutoff_date=cutoff_str,
            forecast_window=forecast_window_str,
            stride=stride_str,
            frequency=freq_name,
            windows=result_windows,
            mape=mape,
            mae=mae,
            total_points=len(all_actuals),
        )
        
        print(f"{'='*60}")
        print(f"✅ Backtest completed for {ticker}")
        print(f"   Windows: {len(result_windows)}, Points: {len(all_actuals)}")
        print(f"   MAPE: {mape:.2f}%, MAE: {mae:.4f}")
        print(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        print(f"{'='*60}")
        print(f"❌ Backtest failed for {ticker}: {type(e).__name__}: {e}")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Backtest failed: {str(e)}")
