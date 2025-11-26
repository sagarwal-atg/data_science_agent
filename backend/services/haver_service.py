"""Haver Analytics data service."""

import os
from typing import Any, Optional

from pydantic import BaseModel


class HaverDatabase(BaseModel):
    """Haver database info."""
    
    code: str
    name: str


class HaverSeries(BaseModel):
    """Haver series info."""
    
    name: str
    description: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    frequency: Optional[str] = None


class HaverTimeSeriesData(BaseModel):
    """Haver time series data response."""
    
    database: str
    series: str
    description: Optional[str] = None
    currency: Optional[str] = None
    timestamps: list[str]
    values: list[float]


import json
import hashlib
from pathlib import Path

# File-based cache setup
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_path(key: str) -> Path:
    """Generate a safe file path for a cache key."""
    # Use MD5 hash of the key to generate a safe filename
    safe_key = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{safe_key}.json"

def load_from_cache(key: str) -> Optional[Any]:
    """Load data from cache if it exists."""
    cache_path = get_cache_path(key)
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"DEBUG: Failed to load cache for {key}: {e}")
            return None
    return None

def save_to_cache(key: str, data: Any):
    """Save data to cache."""
    cache_path = get_cache_path(key)
    try:
        with open(cache_path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"DEBUG: Failed to save cache for {key}: {e}")


def get_haver_client():
    """Get Haver client instance."""
    from haver import Haver
    
    api_key = os.getenv("HAVER_API_KEY")
    if not api_key:
        raise ValueError("HAVER_API_KEY environment variable not set")
    
    return Haver(api_key=api_key)


async def list_databases() -> list[HaverDatabase]:
    """
    List all available Haver databases.
    
    Returns:
        List of HaverDatabase with code and name
    """
    haver = get_haver_client()
    databases = haver.get_databases()
    
    return [
        HaverDatabase(code=code, name=name)
        for code, name in databases.items()
    ]


async def list_series(database: str) -> list[HaverSeries]:
    """
    List all series in a Haver database.
    
    Args:
        database: Database code (e.g., 'USECON')
        
    Returns:
        List of HaverSeries with metadata
    """
    print(f"DEBUG: list_series called for {database}")
    cache_key = f"series:{database}"
    
    cached_data = load_from_cache(cache_key)
    if cached_data:
        print(f"DEBUG: Cache HIT for {cache_key} (file)")
        # Deserialize JSON back to HaverSeries objects
        return [HaverSeries(**item) for item in cached_data]
        
    print(f"DEBUG: Cache MISS for {cache_key}, fetching from Haver...")
    
    try:
        haver = get_haver_client()
        # Use full_info=False to improve performance for large databases
        series_data = haver.get_series(database=database, full_info=False)
        
        result = []
        
        # Handle dictionary response (name -> info/description)
        if isinstance(series_data, dict):
            print(f"DEBUG: Received dictionary with {len(series_data)} items")
            for series_name, info in series_data.items():
                if isinstance(info, dict):
                    result.append(HaverSeries(
                        name=series_name,
                        description=info.get("description", ""),
                        start_date=str(info.get("start_date", "")) if info.get("start_date") else None,
                        end_date=str(info.get("end_date", "")) if info.get("end_date") else None,
                        frequency=info.get("frequency", None),
                    ))
                else:
                    result.append(HaverSeries(
                        name=series_name,
                        description=str(info) if info else "",
                    ))
        # Handle list response (just names)
        elif isinstance(series_data, list):
            print(f"DEBUG: Received list with {len(series_data)} items")
            for series_name in series_data:
                result.append(HaverSeries(
                    name=str(series_name),
                    description="",
                ))
        
        print(f"DEBUG: Caching {len(result)} series for {database}")
        # Serialize objects to dicts for JSON storage
        save_to_cache(cache_key, [s.model_dump() for s in result])
        return result
    except Exception as e:
        print(f"DEBUG: Error in list_series: {e}")
        raise


import re

async def fetch_haver_data(database: str, series: str) -> HaverTimeSeriesData:
    """
    Fetch time series data from Haver Analytics.
    
    Args:
        database: Database code (e.g., 'USECON')
        series: Series name (e.g., 'N997CE')
        
    Returns:
        HaverTimeSeriesData with timestamps and values
    """
    print(f"DEBUG: fetch_haver_data called for {database}/{series}")
    cache_key = f"data:{database}:{series}"
    
    cached_data = load_from_cache(cache_key)
    if cached_data:
        print(f"DEBUG: Cache HIT for {cache_key} (file)")
        return HaverTimeSeriesData(**cached_data)

    print(f"DEBUG: Cache MISS for {cache_key}")
    
    try:
        # Fetch series metadata to get description
        series_list = await list_series(database)
        description = ""
        currency = None
        
        for s in series_list:
            if s.name == series:
                description = s.description
                # Extract currency/unit from parentheses at end of description
                # e.g., "Gross Domestic Product (Mil.Euros)" -> "Mil.Euros"
                match = re.search(r'\(([^)]+)\)$', description)
                if match:
                    currency = match.group(1)
                break

        haver = get_haver_client()
        
        # Construct Haver code as "series@database"
        haver_code = f"{series}@{database}"
        
        df = haver.read_df(haver_codes=[haver_code])
        
        if df is None or df.empty:
            print(f"DEBUG: No data found for {haver_code}")
            raise ValueError(f"No data found for Haver code: {haver_code}")
            
        print(f"DEBUG: DataFrame columns: {df.columns}")
        print(f"DEBUG: DataFrame index: {df.index}")
        print(f"DEBUG: DataFrame head:\n{df.head()}")
        
        # Handle timestamp column
        timestamp_col = None
        
        # 1. Check if index is DatetimeIndex
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            timestamp_col = df.columns[0] # formatted index becomes first col
            print(f"DEBUG: Using DatetimeIndex as timestamp (col: {timestamp_col})")
        # 2. Check if index is PeriodIndex
        elif isinstance(df.index, pd.PeriodIndex):
            df.index = df.index.to_timestamp()
            df = df.reset_index()
            timestamp_col = df.columns[0]
            print(f"DEBUG: Using PeriodIndex converted to timestamp (col: {timestamp_col})")
        else:
            # If index has a name that looks like date, use it
            if df.index.name and df.index.name.lower() in ['date', 'time', 'year', 'period']:
                df = df.reset_index()
                timestamp_col = df.columns[0]
                print(f"DEBUG: Using named index '{timestamp_col}' as timestamp")
            else:
                # Reset index to make it a column, but don't assume it's the timestamp yet
                # unless it was the only option
                df_reset = df.reset_index()
                
                # Look for specific column names
                candidates = [c for c in df_reset.columns if str(c).lower() in ['date', 'time', 'year', 'period']]
                if candidates:
                    timestamp_col = candidates[0]
                    df = df_reset
                    print(f"DEBUG: Found timestamp column by name: {timestamp_col}")
                else:
                    # Check for datetime dtype columns
                    dt_cols = df_reset.select_dtypes(include=['datetime', 'datetimetz']).columns
                    if not dt_cols.empty:
                        timestamp_col = dt_cols[0]
                        df = df_reset
                        print(f"DEBUG: Found timestamp column by dtype: {timestamp_col}")
                    else:
                        # Fallback: Check first column of original df (if it wasn't the index)
                        # If df had index, df_reset has 'index' at col 0.
                        # Usually Haver returns data where index is date.
                        # If index was RangeIndex, then it's useless.
                        # If we are here, index was not Datetime/Period and didn't have date name.
                        
                        # Let's try to use the first column of the RESET dataframe if it looks like years
                        first_col = df_reset.columns[0]
                        if pd.api.types.is_integer_dtype(df_reset[first_col]):
                             # check values range
                             vals = df_reset[first_col]
                             if vals.min() > 1900 and vals.max() < 2100:
                                 timestamp_col = first_col
                                 df = df_reset
                                 print(f"DEBUG: First column '{timestamp_col}' looks like years")
                        
                        if not timestamp_col:
                            # Absolute fallback: use first column of reset df
                            df = df_reset
                            timestamp_col = df.columns[0]
                            print(f"DEBUG: Fallback to first column '{timestamp_col}' as timestamp")

        print(f"DEBUG: Selected timestamp column: {timestamp_col}")
        print(f"DEBUG: First few raw timestamps: {df[timestamp_col].head().tolist()}")
        
        # Find value column
        value_col = "value" if "value" in df.columns else [c for c in df.columns if c != timestamp_col][0]
        
        import pandas as pd
        
        # Convert timestamps to ISO format strings
        try:
            # Check if timestamps are integers (likely years)
            if pd.api.types.is_integer_dtype(df[timestamp_col]):
                print("DEBUG: Detected integer timestamps, treating as years")
                dt_series = pd.to_datetime(df[timestamp_col].astype(str), format="%Y")
            else:
                # Try to convert to datetime objects first
                dt_series = pd.to_datetime(df[timestamp_col])
            
            timestamps = dt_series.dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
        except Exception as e:
            print(f"DEBUG: Failed to convert to datetime: {e}. Using string representation.")
            timestamps = [str(t) for t in df[timestamp_col].tolist()]
        
        values = df[value_col].tolist()
        
        result = HaverTimeSeriesData(
            database=database,
            series=series,
            description=description,
            currency=currency,
            timestamps=timestamps,
            values=values,
        )
        
        save_to_cache(cache_key, result.model_dump())
        print(f"DEBUG: Cached data for {cache_key} ({len(timestamps)} points)")
        return result
    except Exception as e:
        print(f"DEBUG: Error in fetch_haver_data: {e}")
        raise

