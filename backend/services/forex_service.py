"""Forex (Foreign Exchange) data service using yfinance library."""

from datetime import datetime
from typing import Optional

import pandas as pd
import yfinance as yf
from pydantic import BaseModel


class ForexTimeSeriesData(BaseModel):
    """Forex time series data response model."""
    
    ticker: str
    base_currency: str
    quote_currency: str
    timestamps: list[str]
    values: list[float]
    data_type: str = "close"


# Popular forex pairs
FOREX_PAIRS = {
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'USDCAD': 'USDCAD=X',
    'USDCHF': 'USDCHF=X',
    'NZDUSD': 'NZDUSD=X',
    'EURGBP': 'EURGBP=X',
    'EURJPY': 'EURJPY=X',
    'GBPJPY': 'GBPJPY=X',
    'AUDJPY': 'AUDJPY=X',
    'EURAUD': 'EURAUD=X',
    'EURCHF': 'EURCHF=X',
    'GBPAUD': 'GBPAUD=X',
    'GBPCAD': 'GBPCAD=X',
}


def normalize_forex_ticker(ticker: str) -> tuple[str, str, str]:
    """
    Normalize forex ticker to yfinance format.
    
    Examples:
        EURUSD -> (EURUSD=X, EUR, USD)
        EUR/USD -> (EURUSD=X, EUR, USD)
        eurusd -> (EURUSD=X, EUR, USD)
        EURUSD=X -> (EURUSD=X, EUR, USD)
    
    Returns:
        Tuple of (yfinance_ticker, base_currency, quote_currency)
    """
    ticker = ticker.upper().strip()
    
    # Remove slash if present
    ticker = ticker.replace('/', '')
    
    # If already in yfinance format
    if '=X' in ticker:
        base = ticker[:3]
        quote = ticker[3:6]
        return ticker, base, quote
    
    # Check if it's 6 characters (currency pair)
    if len(ticker) == 6:
        base = ticker[:3]
        quote = ticker[3:6]
        yf_ticker = f"{ticker}=X"
        return yf_ticker, base, quote
    
    # Check if it's a known pair
    if ticker in FOREX_PAIRS:
        yf_ticker = FOREX_PAIRS[ticker]
        base = ticker[:3]
        quote = ticker[3:6]
        return yf_ticker, base, quote
    
    raise ValueError(f"Invalid forex ticker format: {ticker}. Expected format: EURUSD, EUR/USD, or EURUSD=X")


async def fetch_forex_data(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> ForexTimeSeriesData:
    """
    Fetch forex data from Yahoo Finance.
    
    Args:
        ticker: Forex pair (e.g., 'EURUSD', 'EUR/USD', 'GBPUSD')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        ForexTimeSeriesData with timestamps and exchange rates
    """
    # Normalize ticker format
    yf_ticker, base_currency, quote_currency = normalize_forex_ticker(ticker)
    
    # Default to last 5 years if no dates provided
    if not start_date:
        start_date = (datetime.now() - pd.DateOffset(years=5)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch data using yfinance
    forex = yf.Ticker(yf_ticker)
    df = forex.history(start=start_date, end=end_date)
    
    if df.empty:
        raise ValueError(f"No data found for forex pair: {ticker} (normalized: {yf_ticker})")
    
    # Reset index to get dates as column
    df = df.reset_index()
    
    # Convert timestamps to ISO format strings
    timestamps = df["Date"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
    values = df["Close"].tolist()
    
    return ForexTimeSeriesData(
        ticker=yf_ticker,
        base_currency=base_currency,
        quote_currency=quote_currency,
        timestamps=timestamps,
        values=values,
        data_type="close"
    )


async def list_popular_forex_pairs():
    """
    List popular forex pairs.
    
    Returns:
        List of popular forex pairs with their tickers
    """
    return [
        {
            "pair": pair,
            "ticker": ticker,
            "base": pair[:3],
            "quote": pair[3:6],
        }
        for pair, ticker in FOREX_PAIRS.items()
    ]
