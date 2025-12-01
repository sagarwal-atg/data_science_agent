"""
Forex data loading utilities for AlphaEvolve backtesting.

Supports loading forex pair data from Yahoo Finance and converting
to Backtrader-compatible format.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
import backtrader as bt

CACHE_DIR = Path.home() / ".alpha_trader_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# Popular forex pairs with yfinance tickers
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


def normalize_forex_ticker(ticker: str) -> Tuple[str, str, str]:
    """
    Normalize forex ticker to yfinance format.
    
    Returns:
        Tuple of (yfinance_ticker, base_currency, quote_currency)
    """
    ticker = ticker.upper().strip().replace('/', '')
    
    if '=X' in ticker:
        base = ticker[:3]
        quote = ticker[3:6]
        return ticker, base, quote
    
    if len(ticker) == 6:
        base = ticker[:3]
        quote = ticker[3:6]
        return f"{ticker}=X", base, quote
    
    if ticker in FOREX_PAIRS:
        yf_ticker = FOREX_PAIRS[ticker]
        base = ticker[:3]
        quote = ticker[3:6]
        return yf_ticker, base, quote
    
    raise ValueError(f"Invalid forex ticker: {ticker}")


@lru_cache(maxsize=32)
def load_forex_ohlc(
    pair: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load forex OHLC data from Yahoo Finance.
    
    Args:
        pair: Forex pair (e.g., 'EURUSD', 'EUR/USD')
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with columns: open, high, low, close, volume (index: date)
    """
    yf_ticker, base, quote = normalize_forex_ticker(pair)
    
    # Default to last 10 years
    if not start:
        start = (datetime.now() - timedelta(days=365 * 10)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    
    # Check cache first
    cache_key = f"forex_{pair}_{start}_{end}.feather"
    cache_file = CACHE_DIR / cache_key
    
    if cache_file.exists():
        try:
            df = pd.read_feather(cache_file)
            df.set_index('date', inplace=True)
            return df
        except Exception:
            pass  # Cache invalid, reload
    
    # Fetch from yfinance
    ticker_obj = yf.Ticker(yf_ticker)
    df = ticker_obj.history(start=start, end=end)
    
    if df.empty:
        raise ValueError(f"No data found for {pair}")
    
    # Normalize column names
    df.columns = df.columns.str.lower()
    df.index.name = 'date'
    
    # Keep only OHLCV columns
    cols_to_keep = ['open', 'high', 'low', 'close', 'volume']
    available_cols = [c for c in cols_to_keep if c in df.columns]
    df = df[available_cols]
    
    # Forward fill any gaps
    df = df.ffill().bfill()
    
    # Cache for faster reloads
    try:
        df.reset_index().to_feather(cache_file)
    except Exception:
        pass  # Caching failed, continue anyway
    
    return df


def load_multi_forex_ohlc(
    pairs: List[str],
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load multiple forex pairs into a multi-level DataFrame.
    
    Returns:
        DataFrame with 2-level columns (field, pair), indexed by date.
    """
    dfs = {}
    for pair in pairs:
        try:
            df = load_forex_ohlc(pair, start, end)
            dfs[pair] = df
        except Exception as e:
            print(f"Warning: Could not load {pair}: {e}")
            continue
    
    if not dfs:
        raise ValueError("No forex data could be loaded")
    
    # Combine into multi-level columns
    combined = pd.concat(dfs, axis=1)
    combined.columns = pd.MultiIndex.from_tuples(
        [(col, pair) for pair, df in dfs.items() for col in df.columns],
        names=['field', 'pair']
    )
    
    # Reorder to (field, pair) format matching ETF loader
    combined = combined.swaplevel(axis=1).sort_index(axis=1)
    
    return combined


def add_forex_feed_to_cerebro(
    df: pd.DataFrame,
    cerebro: bt.Cerebro,
    pair_name: str = "FOREX"
) -> None:
    """
    Convert single-pair DataFrame to Backtrader feed and add to Cerebro.
    
    Args:
        df: DataFrame with OHLCV columns, indexed by date
        cerebro: Backtrader Cerebro instance
        pair_name: Name for the data feed
    """
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Backtrader requires specific column names
    bt_df = df.copy()
    bt_df.index.name = 'datetime'
    
    # Create feed
    data_feed = bt.feeds.PandasData(dataname=bt_df)
    cerebro.adddata(data_feed, name=pair_name)


def add_multi_forex_feeds_to_cerebro(
    df: pd.DataFrame,
    cerebro: bt.Cerebro
) -> None:
    """
    Convert multi-pair DataFrame to Backtrader feeds.
    
    Args:
        df: DataFrame with 2-level columns (field, pair)
        cerebro: Backtrader Cerebro instance
    """
    # Get unique pairs from column level
    if isinstance(df.columns, pd.MultiIndex):
        pairs = df.columns.get_level_values(1).unique()
    else:
        # Single pair
        add_forex_feed_to_cerebro(df, cerebro, "FOREX")
        return
    
    for pair in pairs:
        try:
            # Extract data for this pair
            pair_df = df.xs(pair, axis=1, level=1, drop_level=True).copy()
            pair_df.index.name = 'datetime'
            
            # Forward fill and backward fill
            pair_df = pair_df.ffill().bfill()
            
            # Create feed
            data_feed = bt.feeds.PandasData(dataname=pair_df)
            cerebro.adddata(data_feed, name=pair)
        except Exception as e:
            print(f"Warning: Could not add feed for {pair}: {e}")


def get_available_pairs() -> List[Dict]:
    """Return list of available forex pairs with metadata."""
    return [
        {
            "pair": pair,
            "ticker": ticker,
            "base": pair[:3],
            "quote": pair[3:6],
        }
        for pair, ticker in FOREX_PAIRS.items()
    ]

