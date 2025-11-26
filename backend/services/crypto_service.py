"""Cryptocurrency data service using yfinance library."""

from datetime import datetime
from typing import Optional

import pandas as pd
import yfinance as yf
from pydantic import BaseModel


class CryptoTimeSeriesData(BaseModel):
    """Crypto time series data response model."""
    
    ticker: str
    timestamps: list[str]
    values: list[float]
    data_type: str = "close"
    currency: str = "USD"
    

# Popular crypto symbols
CRYPTO_SYMBOLS = {
    'BTC': 'BTC-USD',
    'ETH': 'ETH-USD',
    'USDT': 'USDT-USD',
    'BNB': 'BNB-USD',
    'SOL': 'SOL-USD',
    'XRP': 'XRP-USD',
    'USDC': 'USDC-USD',
    'ADA': 'ADA-USD',
    'DOGE': 'DOGE-USD',
    'TRX': 'TRX-USD',
    'AVAX': 'AVAX-USD',
    'DOT': 'DOT-USD',
    'MATIC': 'MATIC-USD',
    'LINK': 'LINK-USD',
    'UNI': 'UNI-USD',
}


def normalize_crypto_ticker(ticker: str) -> str:
    """
    Normalize crypto ticker to yfinance format.
    
    Examples:
        BTC -> BTC-USD
        BTC-USD -> BTC-USD
        btc -> BTC-USD
    """
    ticker = ticker.upper().strip()
    
    # If already in correct format
    if '-' in ticker:
        return ticker
    
    # Check if it's a known symbol
    if ticker in CRYPTO_SYMBOLS:
        return CRYPTO_SYMBOLS[ticker]
    
    # Default to USD pair
    return f"{ticker}-USD"


async def fetch_crypto_data(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> CryptoTimeSeriesData:
    """
    Fetch cryptocurrency data from Yahoo Finance.
    
    Args:
        ticker: Crypto ticker symbol (e.g., 'BTC', 'ETH', 'BTC-USD')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        CryptoTimeSeriesData with timestamps and closing prices
    """
    # Normalize ticker format
    normalized_ticker = normalize_crypto_ticker(ticker)
    
    # Default to last 5 years if no dates provided
    if not start_date:
        start_date = (datetime.now() - pd.DateOffset(years=5)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch data using yfinance
    crypto = yf.Ticker(normalized_ticker)
    df = crypto.history(start=start_date, end=end_date)
    
    if df.empty:
        raise ValueError(f"No data found for crypto ticker: {ticker} (normalized: {normalized_ticker})")
    
    # Reset index to get dates as column
    df = df.reset_index()
    
    # Convert timestamps to ISO format strings
    timestamps = df["Date"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
    values = df["Close"].tolist()
    
    # Extract currency pair
    currency = "USD"
    if '-' in normalized_ticker:
        currency = normalized_ticker.split('-')[1]
    
    return CryptoTimeSeriesData(
        ticker=normalized_ticker,
        timestamps=timestamps,
        values=values,
        data_type="close",
        currency=currency
    )


async def list_popular_cryptos():
    """
    List popular cryptocurrencies.
    
    Returns:
        List of popular crypto symbols with their tickers
    """
    return [
        {"symbol": symbol, "ticker": ticker, "name": symbol}
        for symbol, ticker in CRYPTO_SYMBOLS.items()
    ]
