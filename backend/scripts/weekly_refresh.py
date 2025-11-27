"""Weekly orchestrator for downloading data, running backtests, and pruning history."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import typer
from sqlalchemy import delete

from db import (
    BacktestRun,
    DatabaseSettings,
    build_engine_for,
    get_asset_databases,
)
from scripts.download_prices import _download_impl
from scripts.run_backtests import _run_pipeline, ASSET_CLASSES

app = typer.Typer(help="Weekly refresh workflow for the forecasting database.")


def _prune_old_runs(
    settings: DatabaseSettings,
    asset_class: str,
    retain_weeks: int,
) -> None:
    """Delete backtest runs older than the retention window."""
    cutoff = datetime.now(timezone.utc) - timedelta(weeks=retain_weeks)
    targets = get_asset_databases(settings.app_prefix)
    selected = ASSET_CLASSES if asset_class == "all" else (asset_class,)

    for cls in selected:
        engine = build_engine_for(targets[cls], settings)
        with engine.begin() as conn:
            result = conn.execute(
                delete(BacktestRun).where(BacktestRun.created_at < cutoff)
            )
            typer.echo(
                f"[cleanup] {cls}: removed {result.rowcount or 0} runs older than {retain_weeks} weeks"
            )
        engine.dispose()


async def _run_refresh(
    asset_class: str,
    max_assets: Optional[int],
    skip_download: bool,
    skip_backtests: bool,
    retain_weeks: int,
    dry_run: bool,
) -> None:
    if asset_class != "all" and asset_class not in ASSET_CLASSES:
        raise typer.BadParameter(f"asset_class must be one of {ASSET_CLASSES} or 'all'")

    typer.echo(
        f"Weekly refresh plan -> class={asset_class}, "
        f"max_assets={max_assets}, skip_download={skip_download}, "
        f"skip_backtests={skip_backtests}, retain_weeks={retain_weeks}"
    )

    if dry_run:
        typer.echo("Dry run mode enabled; exiting before execution.")
        raise typer.Exit(0)

    if not skip_download:
        typer.echo("Step 1/3: Downloading latest data...")
        await _download_impl(asset_class=asset_class, max_assets=max_assets)
    else:
        typer.echo("Step 1/3: Download skipped.")

    if not skip_backtests:
        typer.echo("Step 2/3: Running backtests...")
        await _run_pipeline(
            asset_class=asset_class,
            max_assets=max_assets,
            start_date=None,
            end_date=None,
        )
    else:
        typer.echo("Step 2/3: Backtests skipped.")

    typer.echo("Step 3/3: Pruning old runs...")
    settings = DatabaseSettings.from_env()
    _prune_old_runs(settings, asset_class, retain_weeks)
    typer.echo("Weekly refresh completed.")


@app.command()
def run(
    asset_class: str = typer.Option("all", help="Asset class to refresh (or 'all')."),
    max_assets: Optional[int] = typer.Option(None, help="Limit number of assets per class."),
    skip_download: bool = typer.Option(False, help="Skip the download step."),
    skip_backtests: bool = typer.Option(False, help="Skip the backtest step."),
    retain_weeks: int = typer.Option(12, help="Number of weeks of backtest runs to retain."),
    dry_run: bool = typer.Option(False, help="Print the plan without executing."),
):
    """Execute the full weekly workflow."""
    asyncio.run(
        _run_refresh(
            asset_class=asset_class,
            max_assets=max_assets,
            skip_download=skip_download,
            skip_backtests=skip_backtests,
            retain_weeks=retain_weeks,
            dry_run=dry_run,
        )
    )


if __name__ == "__main__":
    app()
