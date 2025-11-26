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
    "search_time_series_event",
    "SearchResult",
    "run_backtest",
    "BacktestResult",
    "BacktestWindow",
    "search_critical_events",
    "CriticalEventsResult",
]

