"""Backend services."""

from .yahoo_finance import fetch_yahoo_data, TimeSeriesData
from .haver_service import (
    list_databases,
    list_series,
    fetch_haver_data,
    HaverDatabase,
    HaverSeries,
    HaverTimeSeriesData,
)
from .crypto_service import (
    fetch_crypto_data,
    list_popular_cryptos,
    CryptoTimeSeriesData,
)
from .forex_service import (
    fetch_forex_data,
    list_popular_forex_pairs,
    ForexTimeSeriesData,
)
from .parallel_search import search_time_series_event, SearchResult
from .backtest_service import run_backtest, BacktestResult, BacktestWindow
from .critical_events_service import search_critical_events, CriticalEventsResult

__all__ = [
    "fetch_yahoo_data",
    "TimeSeriesData",
    "list_databases",
    "list_series",
    "fetch_haver_data",
    "HaverDatabase",
    "HaverSeries",
    "HaverTimeSeriesData",
    "fetch_crypto_data",
    "list_popular_cryptos",
    "CryptoTimeSeriesData",
    "fetch_forex_data",
    "list_popular_forex_pairs",
    "ForexTimeSeriesData",
    "search_time_series_event",
    "SearchResult",
    "run_backtest",
    "BacktestResult",
    "BacktestWindow",
    "search_critical_events",
    "CriticalEventsResult",
]

