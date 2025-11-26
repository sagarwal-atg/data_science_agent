"""Yahoo Finance data service using yfinance library."""

from datetime import datetime
from typing import Optional

import pandas as pd
import yfinance as yf
from pydantic import BaseModel


class TimeSeriesData(BaseModel):
    """Time series data response model."""
    
    ticker: str
    timestamps: list[str]
    values: list[float]
    data_type: str = "close"
    

async def fetch_yahoo_data(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> TimeSeriesData:
    """
    Fetch stock data from Yahoo Finance.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        TimeSeriesData with timestamps and closing prices
    """
    # Default to last 5 years if no dates provided
    if not start_date:
        start_date = (datetime.now() - pd.DateOffset(years=5)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch data using yfinance
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    
    if df.empty:
        raise ValueError(f"No data found for ticker: {ticker}")
    
    # Reset index to get dates as column
    df = df.reset_index()
    
    # Convert timestamps to ISO format strings
    timestamps = df["Date"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
    values = df["Close"].tolist()
    
    return TimeSeriesData(
        ticker=ticker,
        timestamps=timestamps,
        values=values,
        data_type="close"
    )

