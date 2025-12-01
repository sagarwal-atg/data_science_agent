"""
Efficient data-loading helpers built on top of pwb-toolbox.

Usage
-----
symbols = ["SPY", "EFA", "IEF", "VNQ", "GSG"]
price_df = load_ohlc(symbols, start="1990-01-01")
cerebro    = bt.Cerebro()
add_feeds_to_cerebro(price_df, cerebro)
"""

from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd
import backtrader as bt
from tqdm import tqdm

# pwb_toolbox is optional - only needed for ETF data
try:
    import pwb_toolbox.datasets as pwb_ds
    PWB_AVAILABLE = True
except ImportError:
    pwb_ds = None
    PWB_AVAILABLE = False

CACHE_DIR = Path.home() / ".alpha_trader_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


from typing import Optional, Tuple

@lru_cache(maxsize=32)
def load_ohlc(
    symbols: Tuple[str, ...],
    start: Optional[str] = None,
    end: Optional[str] = None,
    dataset: str = "ETFs-Daily-Price",
) -> pd.DataFrame:
    """Return OHLC dataframe indexed by date with a 2-level column (field, symbol)."""
    if not PWB_AVAILABLE:
        raise ImportError(
            "pwb_toolbox is required for ETF data loading. "
            "Install with: pip install pwb-toolbox. "
            "For forex data, use alphaevolve.evaluator.forex_loader instead."
        )
    symbols = list(symbols)
    df = pwb_ds.load_dataset(dataset, symbols, extend=True)
    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]

    # pivot to (field, symbol) MultiIndex
    pivot_df = pd.pivot_table(
        df,
        index="date",
        columns="symbol",
        values=["open", "high", "low", "close", "volume"],
        aggfunc="first",
    ).sort_index()

    # fill weekends / holidays → NaNs; forward-fill to trading days later
    full_range = pd.date_range(pivot_df.index.min(), pivot_df.index.max(), freq="D")
    pivot_df = pivot_df.reindex(full_range)

    # persistent feather cache for faster reloads
    cache_key = (
        f"{dataset}_{'_'.join(symbols)}_ohlc_{pivot_df.index.min().date()}_"
        f"{pivot_df.index.max().date()}.feather"
    )
    cache_file = CACHE_DIR / cache_key
    if not cache_file.exists():
        pivot_df.reset_index().rename(columns={"index": "date"}).to_feather(cache_file)
    return pivot_df


def _trading_days(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return pd.bdate_range(idx.min(), idx.max())


def add_feeds_to_cerebro(df: pd.DataFrame, cerebro: bt.Cerebro) -> None:
    """Convert DataFrame produced by `load_ohlc` into individual Backtrader feeds."""
    trading_idx = _trading_days(df.index)
    tqdm_bar = tqdm(df.columns.levels[1], desc="Adding feeds")
    for symbol in tqdm_bar:
        tqdm_bar.set_postfix_str(symbol)
        sym_df = df.xs(symbol, axis=1, level=1, drop_level=False).copy().droplevel(1, axis=1)
        sym_df.index.name = "date"
        sym_df = sym_df.ffill().bfill()
        sym_df = sym_df.loc[trading_idx]

        data_feed = bt.feeds.PandasData(dataname=sym_df)
        cerebro.adddata(data_feed, name=symbol)
