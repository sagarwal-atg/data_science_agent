"""FastAPI backend for Time Series Dashboard."""

import asyncio
import uuid
import json
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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

# Lazy import for Market Intelligence to avoid circular imports
def _get_market_intelligence_funcs():
    from services.market_intelligence_service import (
        build_market_map,
        generate_market_intelligence_report,
        generate_comparison_report,
        search_specific_factor,
        extract_from_source,
        get_upcoming_events,
    )
    from services.factor_discovery_service import (
        get_factor_profile,
        analyze_asset_factors,
    )
    from services.enhanced_search_service import (
        multi_query_search,
        deep_research,
    )
    return {
        'build_market_map': build_market_map,
        'generate_market_intelligence_report': generate_market_intelligence_report,
        'generate_comparison_report': generate_comparison_report,
        'search_specific_factor': search_specific_factor,
        'extract_from_source': extract_from_source,
        'get_upcoming_events': get_upcoming_events,
        'get_factor_profile': get_factor_profile,
        'analyze_asset_factors': analyze_asset_factors,
        'multi_query_search': multi_query_search,
        'deep_research': deep_research,
    }

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
    # Time series data for the selected range
    timestamps: Optional[list[str]] = None
    values: Optional[list[float]] = None
    currency: Optional[str] = None


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


# Market Intelligence Request Models
class MarketMapRequest(BaseModel):
    """Request model for market map."""
    
    asset: str
    include_sentiment: bool = True


class MarketIntelligenceRequest(BaseModel):
    """Request model for full market intelligence report."""
    
    asset: str
    include_deep_research: bool = False


class AssetComparisonRequest(BaseModel):
    """Request model for comparing multiple assets."""
    
    assets: list[str]


class FactorSearchRequest(BaseModel):
    """Request model for searching specific factors."""
    
    asset: str
    query: str
    deep: bool = False


class MultiSearchRequest(BaseModel):
    """Request model for multi-query search."""
    
    queries: list[str]
    objective: str
    max_results_per_query: int = 10


class ExtractRequest(BaseModel):
    """Request model for URL extraction."""
    
    urls: list[str]
    objective: str


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
            timestamps=request.timestamps,
            values=request.values,
            currency=request.currency,
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


# =============================================================================
# Market Intelligence Endpoints (NEW)
# =============================================================================

@app.get("/api/factors/{asset}")
async def get_asset_factors(
    asset: str,
    discover_new: bool = Query(True, description="Use LLM to discover additional factors"),
):
    """
    Get factors that influence an asset's price.
    
    Returns a list of factors with their influence type, strength, and keywords.
    """
    try:
        funcs = _get_market_intelligence_funcs()
        profile = await funcs['get_factor_profile'](asset, use_templates=True, discover_new=discover_new)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get factors: {str(e)}")


@app.post("/api/market-map")
async def create_market_map(request: MarketMapRequest):
    """
    Build a market map graph for an asset.
    
    Returns nodes (factors) and edges (relationships) for visualization.
    """
    try:
        funcs = _get_market_intelligence_funcs()
        market_map = await funcs['build_market_map'](
            asset=request.asset,
            include_sentiment=request.include_sentiment,
        )
        return market_map
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build market map: {str(e)}")


@app.post("/api/market-intelligence")
async def get_market_intelligence(request: MarketIntelligenceRequest):
    """
    Generate comprehensive market intelligence report.
    
    Includes:
    - Market map with factors
    - Factor analysis with news
    - Overall sentiment
    - Short and medium term outlook
    - Key risks and opportunities
    - Upcoming economic events
    """
    print(f"[MARKET INTELLIGENCE] Received request for asset: {request.asset}")
    try:
        funcs = _get_market_intelligence_funcs()
        print(f"[MARKET INTELLIGENCE] Starting analysis...")
        report = await funcs['generate_market_intelligence_report'](
            asset=request.asset,
            include_deep_research=request.include_deep_research,
        )
        print(f"[MARKET INTELLIGENCE] Analysis complete!")
        return report
    except ValueError as e:
        print(f"[MARKET INTELLIGENCE] ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[MARKET INTELLIGENCE] Exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@app.get("/api/market-intelligence/stream/{asset}")
async def stream_market_intelligence(
    asset: str,
    include_deep_research: bool = Query(False),
):
    """
    Stream market intelligence analysis with real-time progress updates via SSE.
    
    Returns Server-Sent Events with progress updates, then the final report.
    """
    from services.progress_tracker import create_tracker, remove_tracker
    
    task_id = str(uuid.uuid4())
    tracker = create_tracker(task_id, total_steps=4)
    
    async def event_generator():
        report = None
        error_msg = None
        
        try:
            # Start the analysis in a background task
            funcs = _get_market_intelligence_funcs()
            
            print(f"[SSE] Starting analysis for {asset}")
            
            # Run analysis with progress tracker
            analysis_task = asyncio.create_task(
                funcs['generate_market_intelligence_report'](
                    asset=asset,
                    include_deep_research=include_deep_research,
                    progress_tracker=tracker,
                )
            )
            
            # Stream progress updates
            update_count = 0
            async for update in tracker.get_updates():
                update_count += 1
                event_data = {
                    "type": "progress",
                    "step": update.step,
                    "totalSteps": update.total_steps,
                    "stepName": update.step_name,
                    "stepDescription": update.step_description,
                    "progressPercent": update.progress_percent,
                    "subStep": update.sub_step,
                    "timestamp": update.timestamp,
                }
                print(f"[SSE] Sending progress update #{update_count}: Step {update.step} - {update.step_name} ({update.progress_percent:.0f}%)")
                yield f"data: {json.dumps(event_data)}\n\n"
            
            print(f"[SSE] Progress updates complete, sent {update_count} updates")
            
            # Wait for analysis to complete and get result
            report = await analysis_task
            print(f"[SSE] Analysis complete, sending report")
            
        except Exception as e:
            print(f"[SSE] Error during analysis: {e}")
            import traceback
            traceback.print_exc()
            error_msg = str(e)
        finally:
            remove_tracker(task_id)
        
        # Send final result
        if error_msg:
            error_data = {
                "type": "error",
                "message": error_msg,
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        elif report:
            result_data = {
                "type": "complete",
                "report": report.model_dump(),
            }
            yield f"data: {json.dumps(result_data)}\n\n"
            print(f"[SSE] Report sent successfully")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.post("/api/market-intelligence/compare")
async def compare_assets(request: AssetComparisonRequest):
    """
    Compare multiple assets.
    
    Shows shared factors, divergences, and correlation notes.
    """
    try:
        if len(request.assets) < 2:
            raise ValueError("At least 2 assets required for comparison")
        if len(request.assets) > 5:
            raise ValueError("Maximum 5 assets for comparison")
        
        funcs = _get_market_intelligence_funcs()
        report = await funcs['generate_comparison_report'](request.assets)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare assets: {str(e)}")


@app.post("/api/market-intelligence/factor-search")
async def search_factor(request: FactorSearchRequest):
    """
    Search for specific information about a factor affecting an asset.
    
    Use for drill-down queries like:
    - "What is the Fed likely to do in the next meeting?"
    - "How are corporate hedging flows affecting EUR/USD?"
    """
    try:
        funcs = _get_market_intelligence_funcs()
        result = await funcs['search_specific_factor'](
            asset=request.asset,
            factor_query=request.query,
            deep=request.deep,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Factor search failed: {str(e)}")


@app.get("/api/market-intelligence/events/{asset}")
async def get_events(
    asset: str,
    days_ahead: int = Query(14, ge=1, le=60, description="Days to look ahead"),
):
    """
    Get upcoming economic events that could affect an asset.
    """
    try:
        funcs = _get_market_intelligence_funcs()
        events = await funcs['get_upcoming_events'](asset, days_ahead)
        return {"asset": asset, "events": events}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@app.post("/api/market-intelligence/analyze")
async def analyze_factors(asset: str = Query(..., description="Asset to analyze")):
    """
    Analyze all factors for an asset with news.
    
    Returns factor profile with current news and sentiment for each factor.
    """
    try:
        funcs = _get_market_intelligence_funcs()
        analysis = await funcs['analyze_asset_factors'](
            asset=asset,
            include_news=True,
            max_factors_for_news=5,
        )
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# =============================================================================
# Advanced Search Endpoints
# =============================================================================

@app.post("/api/search/multi")
async def multi_search(request: MultiSearchRequest):
    """
    Perform multi-query parallel search.
    
    Much faster than sequential searches for gathering comprehensive information.
    """
    try:
        funcs = _get_market_intelligence_funcs()
        results = await funcs['multi_query_search'](
            queries=request.queries,
            objective=request.objective,
            max_results_per_query=request.max_results_per_query,
        )
        return {"results": [r.model_dump() for r in results]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-search failed: {str(e)}")


@app.post("/api/search/extract")
async def extract_urls(request: ExtractRequest):
    """
    Extract specific information from URLs.
    
    Great for:
    - Extracting key data from Fed minutes
    - Parsing earnings reports
    - Getting specific figures from economic releases
    """
    try:
        funcs = _get_market_intelligence_funcs()
        results = await funcs['extract_from_source'](
            urls=request.urls,
            extraction_objective=request.objective,
        )
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/api/search/deep")
async def deep_search(
    topic: str = Query(..., description="Research topic"),
    context: str = Query("", description="Additional context"),
):
    """
    Perform deep research using ultra processor.
    
    Takes longer but provides comprehensive analysis with citations.
    """
    try:
        funcs = _get_market_intelligence_funcs()
        result = await funcs['deep_research'](topic=topic, context=context, timeout=300)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deep research failed: {str(e)}")


# =============================================================================
# AlphaEvolve Trading Strategy Endpoints
# =============================================================================

class AlphaEvolveRequest(BaseModel):
    """Request model for AlphaEvolve strategy evolution."""
    
    pair: str  # Forex pair (e.g., 'EURUSD')
    iterations: int = 5  # Number of evolution iterations
    use_market_intel: bool = True  # Use market intelligence context
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    experiment_name: Optional[str] = None


class SingleBacktestRequest(BaseModel):
    """Request model for single strategy backtest."""
    
    code: str
    pair: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


def _get_alphaevolve_funcs():
    """Lazy import for AlphaEvolve to avoid circular imports."""
    from services.alphaevolve_forex_service import (
        evolve_forex_strategy,
        run_single_backtest,
        get_forex_pairs,
        get_seed_strategies,
        FOREX_SMA_MOMENTUM_SEED,
        FOREX_RSI_MEAN_REVERSION_SEED,
    )
    return {
        'evolve_forex_strategy': evolve_forex_strategy,
        'run_single_backtest': run_single_backtest,
        'get_forex_pairs': get_forex_pairs,
        'get_seed_strategies': get_seed_strategies,
        'FOREX_SMA_MOMENTUM_SEED': FOREX_SMA_MOMENTUM_SEED,
        'FOREX_RSI_MEAN_REVERSION_SEED': FOREX_RSI_MEAN_REVERSION_SEED,
    }


@app.get("/api/alphaevolve/pairs")
async def get_available_forex_pairs():
    """
    Get list of available forex pairs for trading.
    
    Returns pairs with base and quote currencies.
    """
    try:
        funcs = _get_alphaevolve_funcs()
        pairs = await funcs['get_forex_pairs']()
        return {"pairs": pairs}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get pairs: {str(e)}")


@app.get("/api/alphaevolve/seeds")
async def get_seed_strategies_endpoint():
    """
    Get available seed strategies for evolution.
    
    Returns code templates that can be used to start evolution.
    """
    try:
        funcs = _get_alphaevolve_funcs()
        return {"seeds": funcs['get_seed_strategies']()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get seeds: {str(e)}")


@app.post("/api/alphaevolve/backtest")
async def run_strategy_backtest(request: SingleBacktestRequest):
    """
    Run a single backtest on a strategy.
    
    Use this to test a specific strategy code before or after evolution.
    """
    try:
        funcs = _get_alphaevolve_funcs()
        result = await funcs['run_single_backtest'](
            code=request.code,
            pair=request.pair,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@app.post("/api/alphaevolve/evolve")
async def evolve_trading_strategy(request: AlphaEvolveRequest):
    """
    Run AlphaEvolve strategy evolution.
    
    This will:
    1. Optionally fetch market intelligence for the asset
    2. Initialize with seed strategies
    3. Run evolution iterations (mutating strategies via LLM)
    4. Return the best strategy with metrics
    
    Uses market intelligence to inform strategy generation when enabled.
    """
    try:
        funcs = _get_alphaevolve_funcs()
        
        # Optionally get market intelligence
        market_intel = None
        if request.use_market_intel:
            try:
                mi_funcs = _get_market_intelligence_funcs()
                print(f"[ALPHAEVOLVE] Fetching market intelligence for {request.pair}...")
                market_intel = await mi_funcs['generate_market_intelligence_report'](
                    asset=request.pair,
                    include_deep_research=False,
                )
                market_intel = market_intel.model_dump()
                print(f"[ALPHAEVOLVE] Market intelligence fetched successfully")
            except Exception as e:
                print(f"[ALPHAEVOLVE] Market intel fetch failed: {e}, continuing without")
                market_intel = None
        
        print(f"[ALPHAEVOLVE] Starting evolution for {request.pair} ({request.iterations} iterations)")
        result = await funcs['evolve_forex_strategy'](
            pair=request.pair,
            iterations=request.iterations,
            use_market_intel=request.use_market_intel,
            market_intel=market_intel,
            experiment_name=request.experiment_name,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        print(f"[ALPHAEVOLVE] Evolution complete! Best Sharpe: {result.best_metrics.sharpe:.3f}")
        
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Evolution failed: {str(e)}")


@app.get("/api/alphaevolve/evolve/stream/{pair}")
async def stream_evolution(
    pair: str,
    iterations: int = Query(5, ge=1, le=50),
    use_market_intel: bool = Query(True),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """
    Stream AlphaEvolve evolution with real-time progress updates via SSE.
    
    Returns Server-Sent Events with progress updates and the final result.
    """
    async def event_generator():
        result = None
        error_msg = None
        
        try:
            funcs = _get_alphaevolve_funcs()
            
            # Get market intelligence if requested
            market_intel = None
            if use_market_intel:
                try:
                    mi_funcs = _get_market_intelligence_funcs()
                    print(f"[SSE-EVOLVE] Fetching market intelligence for {pair}...")
                    
                    # Send progress update for market intel
                    yield f"data: {json.dumps({'type': 'progress', 'step': 0, 'totalSteps': iterations + 1, 'stepName': 'Fetching Market Intelligence', 'progressPercent': 2})}\n\n"
                    
                    market_intel = await mi_funcs['generate_market_intelligence_report'](
                        asset=pair,
                        include_deep_research=False,
                    )
                    market_intel = market_intel.model_dump()
                    print(f"[SSE-EVOLVE] Market intelligence fetched")
                    
                    yield f"data: {json.dumps({'type': 'progress', 'step': 0, 'totalSteps': iterations + 1, 'stepName': 'Market Intelligence Ready', 'progressPercent': 5})}\n\n"
                except Exception as e:
                    print(f"[SSE-EVOLVE] Market intel failed: {e}")
                    yield f"data: {json.dumps({'type': 'progress', 'step': 0, 'stepName': 'Skipping Market Intel', 'progressPercent': 5})}\n\n"
            
            # Progress callback for evolution
            async def progress_callback(progress):
                event_data = {
                    "type": "progress",
                    "step": progress.step,
                    "totalSteps": progress.total_steps,
                    "stepName": progress.step_name,
                    "stepDescription": progress.step_description,
                    "progressPercent": progress.progress_percent,
                    "currentStrategy": progress.current_strategy,
                    "timestamp": progress.timestamp,
                }
                return f"data: {json.dumps(event_data)}\n\n"
            
            print(f"[SSE-EVOLVE] Starting evolution...")
            
            # Run evolution with progress updates
            progress_events = []
            
            async def collect_progress(p):
                event = await progress_callback(p)
                progress_events.append(event)
            
            result = await funcs['evolve_forex_strategy'](
                pair=pair,
                iterations=iterations,
                use_market_intel=use_market_intel,
                market_intel=market_intel,
                start_date=start_date,
                end_date=end_date,
                progress_callback=collect_progress,
            )
            
            # Send collected progress events
            for event in progress_events:
                yield event
            
            print(f"[SSE-EVOLVE] Evolution complete!")
            
        except Exception as e:
            print(f"[SSE-EVOLVE] Error: {e}")
            import traceback
            traceback.print_exc()
            error_msg = str(e)
        
        # Send final result
        if error_msg:
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
        elif result:
            yield f"data: {json.dumps({'type': 'complete', 'result': result.to_dict()})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Dispose shared resources."""
    backtest_repo.close()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

