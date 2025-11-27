"""Read-only helpers for serving stored backtest results via the API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.engine import Engine

from .schema import Asset, BacktestRun, ForecastWindow
from .settings import DatabaseSettings, get_asset_databases, build_engine_for


class BacktestRepository:
    """Convenience layer for querying aggregated backtest results."""

    def __init__(self, settings: Optional[DatabaseSettings] = None):
        self.settings = settings or DatabaseSettings.from_env()
        self.targets = get_asset_databases(self.settings.app_prefix)
        self._engines: Dict[str, Engine] = {}

    def _get_engine(self, asset_class: str) -> Engine:
        if asset_class not in self.targets:
            raise ValueError(f"Unknown asset class '{asset_class}'")
        if asset_class not in self._engines:
            self._engines[asset_class] = build_engine_for(
                self.targets[asset_class],
                self.settings,
            )
        return self._engines[asset_class]

    def close(self):
        for engine in self._engines.values():
            engine.dispose()
        self._engines.clear()

    def fetch_asset_summaries(self, asset_class: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent backtest metrics per asset."""
        engine = self._get_engine(asset_class)
        stmt = text(
            """
            WITH latest AS (
                SELECT DISTINCT ON (asset_id)
                    id,
                    asset_id,
                    created_at,
                    mape,
                    mae,
                    total_points,
                    meta,
                    status,
                    run_key
                FROM backtest_runs
                WHERE status = 'success'
                ORDER BY asset_id, created_at DESC
            )
            SELECT
                a.symbol,
                a.name,
                a.asset_class,
                latest.mape,
                latest.mae,
                latest.total_points,
                latest.meta,
                latest.created_at,
                latest.run_key
            FROM latest
            JOIN assets a ON a.id = latest.asset_id
            ORDER BY latest.created_at DESC
            LIMIT :limit
            """
        )
        with engine.connect() as conn:
            rows = conn.execute(stmt, {"limit": limit}).mappings().all()
        results = []
        for row in rows:
            meta = row["meta"] or {}
            results.append(
                {
                    "symbol": row["symbol"],
                    "name": row["name"],
                    "asset_class": row["asset_class"],
                    "mape": row["mape"],
                    "mae": row["mae"],
                    "total_points": row["total_points"],
                    "run_week": meta.get("run_week"),
                    "run_key": row["run_key"],
                    "run_timestamp": row["created_at"].isoformat() if row["created_at"] else None,
                }
            )
        return results

    def fetch_backtest_detail(
        self,
        asset_class: str,
        symbol: str,
        window_limit: int = 500,
    ) -> Dict[str, Any]:
        """Return the latest backtest run plus window-level details."""
        engine = self._get_engine(asset_class)
        with engine.connect() as conn:
            asset = conn.execute(
                select(Asset.id, Asset.symbol, Asset.name).where(
                    Asset.asset_class == asset_class,
                    Asset.symbol == symbol,
                )
            ).first()
            if not asset:
                raise ValueError(f"Asset '{symbol}' not found in {asset_class} database")

            run = conn.execute(
                select(
                    BacktestRun.id,
                    BacktestRun.run_key,
                    BacktestRun.mape,
                    BacktestRun.mae,
                    BacktestRun.total_points,
                    BacktestRun.forecast_window,
                    BacktestRun.stride,
                    BacktestRun.frequency,
                    BacktestRun.meta,
                    BacktestRun.created_at,
                )
                .where(
                    BacktestRun.asset_id == asset.id,
                    BacktestRun.status == "success",
                )
                .order_by(BacktestRun.created_at.desc())
                .limit(1)
            ).first()

            if not run:
                raise ValueError(f"No successful backtests found for {symbol}")

            windows = conn.execute(
                select(
                    ForecastWindow.history_start,
                    ForecastWindow.history_end,
                    ForecastWindow.target_start,
                    ForecastWindow.target_end,
                    ForecastWindow.actual_value,
                    ForecastWindow.forecast_value,
                    ForecastWindow.timestamps,
                )
                .where(ForecastWindow.backtest_run_id == run.id)
                .order_by(ForecastWindow.target_start)
                .limit(window_limit)
            ).mappings().all()

        meta = run.meta or {}
        return {
            "summary": {
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_class": asset_class,
                "run_key": run.run_key,
                "mape": run.mape,
                "mae": run.mae,
                "total_points": run.total_points,
                "forecast_window": run.forecast_window,
                "stride": run.stride,
                "frequency": run.frequency,
                "run_week": meta.get("run_week"),
                "run_timestamp": run.created_at.isoformat() if run.created_at else None,
            },
            "windows": [
                {
                    "history_start": row["history_start"].isoformat(),
                    "history_end": row["history_end"].isoformat(),
                    "target_start": row["target_start"].isoformat(),
                    "target_end": row["target_end"].isoformat(),
                    "actual_value": row["actual_value"],
                    "forecast_value": row["forecast_value"],
                    "timestamps": row["timestamps"],
                }
                for row in windows
            ],
        }
