"""Run Synthefy backtests for stored assets and persist the results."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from config import load_asset_config
from db import (
    Asset,
    PriceHistory,
    BacktestRun,
    ForecastWindow,
    RunMetric,
    DatabaseSettings,
    build_engine_for,
    get_asset_databases,
)
from services import run_backtest


MIN_POINTS = 30
ASSET_CLASSES = ("sp500", "crypto", "forex", "macro")


def _current_run_week() -> str:
    iso = datetime.now(timezone.utc).isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


@dataclass
class BacktestJob:
    asset_class: str
    asset_id: int
    symbol: str
    name: Optional[str]
    engine: Engine


def _default_dates(asset_class: str) -> tuple[str, str]:
    config = load_asset_config().get(asset_class, {})
    if asset_class == "macro":
        start_year = config.get("start_year", 2021)
        end_year = config.get("end_year", 2025)
        return f"{start_year}-01-01", f"{end_year}-12-31"
    return config.get("start_date", "2021-01-01"), config.get("end_date", "2025-12-31")


def _load_assets(engine, asset_class: str, limit: Optional[int] = None) -> List[BacktestJob]:
    stmt = (
        select(Asset.id, Asset.symbol, Asset.name)
        .where(Asset.asset_class == asset_class)
        .order_by(Asset.symbol)
    )
    if limit:
        stmt = stmt.limit(limit)

    jobs: List[BacktestJob] = []
    with engine.connect() as conn:
        for row in conn.execute(stmt):
            jobs.append(
                BacktestJob(
                    asset_class=asset_class,
                    asset_id=row.id,
                    symbol=row.symbol,
                    name=row.name,
                    engine=engine,
                )
            )
    return jobs


def _load_time_series(job: BacktestJob, start_dt: datetime, end_dt: datetime) -> tuple[list[str], list[float]]:
    stmt = (
        select(PriceHistory.as_of, PriceHistory.value)
        .where(PriceHistory.asset_id == job.asset_id)
        .where(PriceHistory.as_of >= start_dt)
        .where(PriceHistory.as_of <= end_dt)
        .order_by(PriceHistory.as_of)
    )
    with job.engine.connect() as conn:
        rows = conn.execute(stmt).all()

    if not rows:
        return [], []

    df = pd.DataFrame(rows, columns=["as_of", "value"]).dropna()
    df["as_of"] = pd.to_datetime(df["as_of"], utc=True)
    timestamps = df["as_of"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist()
    values = df["value"].astype(float).tolist()
    return timestamps, values


def _record_failure(job: BacktestJob, start_dt: datetime, end_dt: datetime, error: Exception):
    run_week = _current_run_week()
    stmt = pg_insert(BacktestRun).values(
        asset_id=job.asset_id,
        run_key=f"{job.asset_class}:{job.symbol}:{uuid4().hex}",
        start_date=start_dt.date(),
        end_date=end_dt.date(),
        forecast_window="unknown",
        stride="unknown",
        frequency="unknown",
        status="failed",
        total_points=0,
        meta={"error": str(error), "run_week": run_week},
    )
    with job.engine.begin() as conn:
        conn.execute(stmt)


def _store_result(job: BacktestJob, start_dt: datetime, end_dt: datetime, result):
    run_key = f"{job.asset_class}:{job.symbol}:{uuid4().hex}"
    run_week = _current_run_week()
    meta = {
        "cutoff_date": result.cutoff_date,
        "windows": len(result.windows),
        "run_week": run_week,
    }
    run_stmt = (
        pg_insert(BacktestRun)
        .values(
            asset_id=job.asset_id,
            run_key=run_key,
            start_date=start_dt.date(),
            end_date=end_dt.date(),
            forecast_window=result.forecast_window,
            stride=result.stride,
            frequency=result.frequency,
            status="success",
            mape=result.mape,
            mae=result.mae,
            total_points=result.total_points,
            meta=meta,
        )
        .returning(BacktestRun.id)
    )

    with job.engine.begin() as conn:
        run_id = conn.execute(run_stmt).scalar_one()

        if result.windows:
            window_rows = []
            for window in result.windows:
                window_rows.append(
                    {
                        "backtest_run_id": run_id,
                        "history_start": pd.Timestamp(window.history_start).to_pydatetime(),
                        "history_end": pd.Timestamp(window.history_end).to_pydatetime(),
                        "target_start": pd.Timestamp(window.target_start).to_pydatetime(),
                        "target_end": pd.Timestamp(window.target_end).to_pydatetime(),
                        "actual_value": window.actual_values[0],
                        "forecast_value": window.forecast_values[0],
                        "timestamps": window.timestamps,
                    }
                )
            conn.execute(pg_insert(ForecastWindow), window_rows)

        metric_rows = [
            {"backtest_run_id": run_id, "metric_name": "mape", "metric_value": result.mape},
            {"backtest_run_id": run_id, "metric_name": "mae", "metric_value": result.mae},
        ]
        conn.execute(pg_insert(RunMetric).on_conflict_do_nothing(index_elements=["backtest_run_id", "metric_name"]), metric_rows)


async def _run_job(
    job: BacktestJob,
    history_start_dt: datetime,
    backtest_start_dt: datetime,
    end_dt: datetime,
    forecast_window_rows: int = 1,
    stride_rows: int = 1,
):
    timestamps, values = _load_time_series(job, history_start_dt, end_dt)
    if len(timestamps) < MIN_POINTS:
        print(f"[{job.asset_class}] Skipping {job.symbol} (insufficient data: {len(timestamps)} points)")
        return

    print(
        f"[{job.asset_class}] Running backtest for {job.symbol} "
        f"({len(timestamps)} pts, eval start {backtest_start_dt.date()}, "
        f"window={forecast_window_rows}, stride={stride_rows})"
    )
    try:
        result = await run_backtest(
            ticker=job.symbol,
            timestamps=timestamps,
            values=values,
            start_date=backtest_start_dt.strftime("%Y-%m-%d"),
            end_date=end_dt.strftime("%Y-%m-%d"),
            forecast_window_rows=forecast_window_rows,
            stride_rows=stride_rows,
        )
        _store_result(job, backtest_start_dt, end_dt, result)
        print(f"  -> success MAPE={result.mape:.2f}% MAE={result.mae:.4f}")
    except Exception as exc:  # noqa: BLE001
        print(f"  !! backtest failed for {job.symbol}: {exc}")
        _record_failure(job, backtest_start_dt, end_dt, exc)


async def _run_job_with_semaphore(
    semaphore: asyncio.Semaphore,
    job: BacktestJob,
    history_start_dt: datetime,
    backtest_start_dt: datetime,
    end_dt: datetime,
    forecast_window_rows: int = 1,
    stride_rows: int = 1,
):
    """Run a job with semaphore for concurrency control."""
    async with semaphore:
        await _run_job(
            job, history_start_dt, backtest_start_dt, end_dt,
            forecast_window_rows, stride_rows
        )


async def _run_pipeline(
    asset_class: str,
    max_assets: Optional[int],
    start_date: Optional[str],
    end_date: Optional[str],
    backtest_start_date: Optional[str],
    max_concurrent: int = 5,
    forecast_window_rows: int = 1,
    stride_rows: int = 1,
):
    """
    Run backtests for all assets in parallel with controlled concurrency.
    
    Args:
        asset_class: Asset class to backtest ('sp500', 'crypto', 'forex', 'macro', or 'all')
        max_assets: Limit number of assets per class
        start_date: Override history start date
        end_date: Override end date
        backtest_start_date: Date when evaluation begins
        max_concurrent: Maximum number of concurrent backtests (default: 5)
        forecast_window_rows: Number of rows to forecast per window (default: 1)
        stride_rows: Number of rows to move forward between windows (default: 1)
    """
    if asset_class != "all" and asset_class not in ASSET_CLASSES:
        raise ValueError(f"asset_class must be one of {ASSET_CLASSES} or 'all'")

    settings = DatabaseSettings.from_env()
    targets = get_asset_databases(settings.app_prefix)

    # Semaphore to control concurrent API calls
    semaphore = asyncio.Semaphore(max_concurrent)

    selected_classes = ASSET_CLASSES if asset_class == "all" else (asset_class,)
    for cls in selected_classes:
        engine = build_engine_for(targets[cls], settings)
        jobs = _load_assets(engine, cls, limit=max_assets)
        print(f"\n{'='*60}")
        print(f"Processing {len(jobs)} assets for class '{cls}'")
        print(f"  Max concurrent: {max_concurrent}, Window: {forecast_window_rows}, Stride: {stride_rows}")
        print(f"{'='*60}")
        cls_start_default, cls_end_default = _default_dates(cls)
        history_start_dt = pd.Timestamp(start_date or cls_start_default, tz="UTC")
        end_dt = pd.Timestamp(end_date or cls_end_default, tz="UTC")
        backtest_start_dt = (
            pd.Timestamp(backtest_start_date, tz="UTC")
            if backtest_start_date
            else history_start_dt
        )
        if backtest_start_dt < history_start_dt:
            raise ValueError("backtest_start_date must be >= start_date/history start date")
        if backtest_start_dt >= end_dt:
            raise ValueError("backtest_start_date must be before end_date")
        
        # Run all jobs in parallel with semaphore-controlled concurrency
        tasks = [
            _run_job_with_semaphore(
                semaphore, job, history_start_dt, backtest_start_dt, end_dt,
                forecast_window_rows, stride_rows
            )
            for job in jobs
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Synthefy backtests across stored assets."
    )
    parser.add_argument(
        "--asset-class",
        default="all",
        choices=[*ASSET_CLASSES, "all"],
        help="Asset class to backtest (default: all).",
    )
    parser.add_argument(
        "--max-assets",
        type=int,
        help="Limit the number of assets per class.",
    )
    parser.add_argument(
        "--start-date",
        help="Override history start date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        help="Override end date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--backtest-start-date",
        help="Date (YYYY-MM-DD) when evaluation begins; defaults to start-date/history start.",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum number of concurrent backtests (default: 5).",
    )
    parser.add_argument(
        "--forecast-window",
        type=int,
        default=1,
        help="Number of rows to forecast per window (default: 1).",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=1,
        help="Number of rows to move forward between windows (default: 1).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(
        _run_pipeline(
            asset_class=args.asset_class,
            max_assets=args.max_assets,
            start_date=args.start_date,
            end_date=args.end_date,
            backtest_start_date=args.backtest_start_date,
            max_concurrent=args.max_concurrent,
            forecast_window_rows=args.forecast_window,
            stride_rows=args.stride,
        )
    )


if __name__ == "__main__":
    main()
