"""FastAPI backend for Time Series Dashboard."""

import asyncio
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import BacktestRepository
from services import (
    fetch_yahoo_data,
    list_databases,
    list_series,
    fetch_haver_data,
    fetch_crypto_data,
    list_popular_cryptos,
    fetch_forex_data,
    list_popular_forex_pairs,
    search_time_series_event,
    run_backtest,
    search_critical_events,
)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Time Series Dashboard API",
    description="API for fetching financial and macroeconomic time series data",
    version="1.0.0",
)

backtest_repo = BacktestRepository()
# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SearchRequest(BaseModel):
    """Request model for time series search."""
    
    ticker: str
    query: str
    start_date: str
    end_date: str
    change_description: Optional[str] = None


class BacktestRequest(BaseModel):
    """Request model for backtest."""
    
    ticker: str
    timestamps: list[str]
    values: list[float]
    start_date: str
    end_date: str
    forecast_window_rows: int = 1  # Number of rows to forecast per window
    stride_rows: int = 1  # Number of rows to move forward between windows


class CriticalEventsRequest(BaseModel):
    """Request model for critical events search."""
    
    ticker: str
    start_date: str
    end_date: str
    num_events: int = 10


# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Yahoo Finance endpoints
@app.get("/api/yahoo/{ticker}")
async def get_yahoo_data(
    ticker: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Fetch stock data from Yahoo Finance.
    
    - **ticker**: Stock ticker symbol (e.g., NVDA, AAPL, MSFT)
    - **start_date**: Optional start date in YYYY-MM-DD format
    - **end_date**: Optional end date in YYYY-MM-DD format
    """
    try:
        data = await fetch_yahoo_data(ticker, start_date, end_date)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


# Crypto endpoints
@app.get("/api/crypto/popular")
async def get_popular_cryptos():
    """
    List popular cryptocurrencies.
    
    Returns a list of popular crypto symbols.
    """
    try:
        cryptos = await list_popular_cryptos()
        return {"cryptos": cryptos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cryptos: {str(e)}")


@app.get("/api/crypto/{ticker}")
async def get_crypto_data(
    ticker: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Fetch cryptocurrency data from Yahoo Finance.
    
    - **ticker**: Crypto symbol (e.g., BTC, ETH, BTC-USD)
    - **start_date**: Optional start date in YYYY-MM-DD format
    - **end_date**: Optional end date in YYYY-MM-DD format
    """
    try:
        data = await fetch_crypto_data(ticker, start_date, end_date)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


# Forex endpoints
@app.get("/api/forex/popular")
async def get_popular_forex_pairs():
    """
    List popular forex pairs.
    
    Returns a list of popular currency pairs.
    """
    try:
        pairs = await list_popular_forex_pairs()
        return {"pairs": pairs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list forex pairs: {str(e)}")


@app.get("/api/forex/{pair}")
async def get_forex_data(
    pair: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Fetch forex data from Yahoo Finance.
    
    - **pair**: Forex pair (e.g., EURUSD, EUR/USD, GBPUSD)
    - **start_date**: Optional start date in YYYY-MM-DD format
    - **end_date**: Optional end date in YYYY-MM-DD format
    """
    try:
        data = await fetch_forex_data(pair, start_date, end_date)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


# Haver Analytics endpoints
@app.get("/api/haver/databases")
async def get_haver_databases():
    """
    List all available Haver databases.
    
    Returns a list of database codes and names.
    """
    try:
        databases = await list_databases()
        return {"databases": databases}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list databases: {str(e)}")


@app.get("/api/haver/series/{database}")
async def get_haver_series(database: str):
    """
    List all series in a Haver database.
    
    - **database**: Database code (e.g., USECON, EUDATA)
    """
    try:
        series = await list_series(database)
        return {"database": database, "series": series}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list series: {str(e)}")


@app.get("/api/haver/{database}/{series}")
async def get_haver_data(database: str, series: str):
    """
    Fetch time series data from Haver Analytics.
    
    - **database**: Database code (e.g., USECON)
    - **series**: Series name (e.g., N997CE)
    """
    try:
        data = await fetch_haver_data(database, series)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


# Search endpoint
@app.post("/api/search")
async def search_event(request: SearchRequest):
    """
    Search for explanation of time series movement.
    
    Uses Parallel API to search the web for events that explain
    why a stock or economic indicator changed during a specific period.
    """
    try:
        result = await search_time_series_event(
            ticker=request.ticker,
            query=request.query,
            start_date=request.start_date,
            end_date=request.end_date,
            change_description=request.change_description,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Backtest endpoint
@app.post("/api/backtest")
async def backtest(request: BacktestRequest):
    """
    Run a backtest on a time series using Synthefy.
    
    Uses the selected region as the forecast target, with everything
    before as history. Returns MAPE and other metrics.
    
    Parameters:
        forecast_window_rows: Number of rows to forecast per window (default: 1)
        stride_rows: Number of rows to move forward between windows (default: 1)
    """
    try:
        result = await run_backtest(
            ticker=request.ticker,
            timestamps=request.timestamps,
            values=request.values,
            start_date=request.start_date,
            end_date=request.end_date,
            forecast_window_rows=request.forecast_window_rows,
            stride_rows=request.stride_rows,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


# Critical Events endpoint
@app.post("/api/critical-events")
async def get_critical_events(request: CriticalEventsRequest):
    """
    Search for critical events in a time series.
    
    Finds the most important events, news, or developments related to
    the ticker during the specified time period.
    """
    try:
        result = await search_critical_events(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            num_events=request.num_events,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Critical events search failed: {str(e)}")


@app.get("/api/backtests/{asset_class}")
async def list_backtests(
    asset_class: str,
    limit: int = Query(50, ge=1, le=500, description="Max number of assets to return"),
):
    """List the latest stored backtests for an asset class."""
    try:
        results = await asyncio.to_thread(backtest_repo.fetch_asset_summaries, asset_class, limit)
        return {
            "asset_class": asset_class,
            "count": len(results),
            "results": results,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load backtests: {str(e)}")


@app.get("/api/backtests/{asset_class}/{symbol}")
async def get_backtest_detail(
    asset_class: str,
    symbol: str,
    window_limit: int = Query(500, ge=10, le=5000, description="Max forecast windows to return"),
):
    """Return the latest backtest run (including forecast windows) for a given asset."""
    try:
        detail = await asyncio.to_thread(
            backtest_repo.fetch_backtest_detail,
            asset_class,
            symbol,
            window_limit,
        )
        return detail
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load backtest detail: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Dispose shared resources."""
    backtest_repo.close()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

