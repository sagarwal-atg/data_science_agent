"""Download historical data for configured assets and ingest into Postgres."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config import load_asset_config
from db import (
    Asset,
    PriceHistory,
    DatabaseSettings,
    build_engine_for,
    get_asset_databases,
)
from services import (
    fetch_yahoo_data,
    fetch_crypto_data,
    fetch_forex_data,
    fetch_gdp_series,
    fetch_sp500_constituents,
)


ASSET_CLASSES = ("sp500", "crypto", "forex", "macro")


@dataclass
class AssetJob:
    asset_class: str
    symbol: str
    name: str
    currency: Optional[str]
    source: str
    meta: Dict[str, object] = field(default_factory=dict)


def _default_dates(asset_class: str) -> tuple[str, str]:
    config = load_asset_config().get(asset_class, {})
    if asset_class == "macro":
        start_year = config.get("start_year", 2021)
        end_year = config.get("end_year", 2025)
        return f"{start_year}-01-01", f"{end_year}-12-31"
    return config.get("start_date", "2021-01-01"), config.get("end_date", "2025-12-31")


def _chunk(records: List[dict], size: int):
    for i in range(0, len(records), size):
        yield records[i : i + size]


def _build_jobs(asset_class: str | None) -> List[AssetJob]:
    config = load_asset_config()
    jobs: List[AssetJob] = []

    def add_job(job: AssetJob):
        if asset_class in (None, "all", job.asset_class):
            jobs.append(job)

    if asset_class in (None, "all", "sp500"):
        for constituent in fetch_sp500_constituents():
            add_job(
                AssetJob(
                    asset_class="sp500",
                    symbol=constituent.symbol,
                    name=constituent.security,
                    currency="USD",
                    source="yahoo-finance",
                    meta={
                        "sector": constituent.sector,
                        "sub_industry": constituent.sub_industry,
                        "headquarters": constituent.headquarters,
                    },
                )
            )

    if asset_class in (None, "all", "crypto"):
        for ticker in config.get("crypto", {}).get("tickers", []):
            add_job(
                AssetJob(
                    asset_class="crypto",
                    symbol=ticker,
                    name=ticker,
                    currency="USD",
                    source="yahoo-crypto",
                    meta={"universe": "top15"},
                )
            )

    if asset_class in (None, "all", "forex"):
        for pair in config.get("forex", {}).get("pairs", []):
            add_job(
                AssetJob(
                    asset_class="forex",
                    symbol=pair,
                    name=pair,
                    currency=pair[-3:],
                    source="yahoo-forex",
                    meta={"pair": pair},
                )
            )

    if asset_class in (None, "all", "macro"):
        for country in config.get("macro", {}).get("country_codes", []):
            jobs.append(
                AssetJob(
                    asset_class="macro",
                    symbol=f"{country['iso3']}_GDP",
                    name=f"{country['name']} GDP",
                    currency="USD",
                    source="world-bank",
                    meta={
                        "iso2": country.get("iso2"),
                        "iso3": country.get("iso3"),
                        "indicator": config.get("macro", {}).get("indicator"),
                    },
                )
            )

    return jobs


async def _fetch_data(job: AssetJob, start_date: str, end_date: str):
    if job.asset_class == "sp500":
        return await fetch_yahoo_data(job.symbol, start_date, end_date)
    if job.asset_class == "crypto":
        return await fetch_crypto_data(job.symbol, start_date, end_date)
    if job.asset_class == "forex":
        return await fetch_forex_data(job.symbol, start_date, end_date)
    if job.asset_class == "macro":
        start_year = int(start_date[:4])
        end_year = int(end_date[:4])
        country_iso3 = job.meta.get("iso3", job.symbol[:3])
        return await fetch_gdp_series(country_iso3, start_year=start_year, end_year=end_year)
    raise ValueError(f"Unsupported asset class {job.asset_class}")


def _upsert_asset(job: AssetJob, engine):
    stmt = (
        pg_insert(Asset)
        .values(
            asset_class=job.asset_class,
            symbol=job.symbol,
            name=job.name,
            currency=job.currency,
            source=job.source,
            meta=job.meta,
        )
        .on_conflict_do_update(
            index_elements=["asset_class", "symbol"],
            set_={
                "name": job.name,
                "currency": job.currency,
                "source": job.source,
                "meta": job.meta,
                "updated_at": func.now(),
            },
        )
        .returning(Asset.id)
    )
    with engine.begin() as conn:
        return conn.execute(stmt).scalar_one()


def _store_prices(job: AssetJob, engine, asset_id: int, data, start_ts, end_ts, chunk_size: int) -> int:
    df = pd.DataFrame(
        {
            "timestamp": data.timestamps,
            "value": data.values,
        }
    )
    if df.empty:
        return 0
    df = df.dropna(subset=["value"])
    df["as_of"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df[(df["as_of"] >= start_ts) & (df["as_of"] <= end_ts)]
    if df.empty:
        return 0

    records = [
        {
            "asset_id": asset_id,
            "as_of": ts.to_pydatetime(),
            "value": float(val),
            "currency": job.currency,
            "source": job.source,
        }
        for ts, val in zip(df["as_of"], df["value"], strict=False)
    ]
    inserted = 0
    stmt = pg_insert(PriceHistory).on_conflict_do_nothing()
    with engine.begin() as conn:
        for batch in _chunk(records, chunk_size):
            conn.execute(stmt, batch)
            inserted += len(batch)
    return inserted


async def _download_impl(
    asset_class: str = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_assets: Optional[int] = None,
    chunk_size: int = 1000,
    dry_run: bool = False,
):
    if asset_class != "all" and asset_class not in ASSET_CLASSES:
        raise ValueError(f"asset_class must be one of {ASSET_CLASSES} or 'all'")

    jobs = _build_jobs(None if asset_class == "all" else asset_class)
    if max_assets:
        jobs = jobs[:max_assets]

    print(f"Prepared {len(jobs)} assets to process.")
    if dry_run:
        for job in jobs[:10]:
            print(f"- {job.asset_class}: {job.symbol}")
        if len(jobs) > 10:
            print("... (truncated)")
        return

    settings = DatabaseSettings.from_env()
    targets = get_asset_databases(settings.app_prefix)
    engines = {
        cls: build_engine_for(db_name, settings)
        for cls, db_name in targets.items()
        if asset_class == "all" or cls == asset_class
    }

    start_default, end_default = _default_dates(asset_class if asset_class != "all" else "sp500")
    start_dt = pd.Timestamp(start_date or start_default, tz="UTC")
    end_dt = pd.Timestamp(end_date or end_default, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    stats = {"processed": 0, "inserted": 0, "failed": 0}
    for job in jobs:
        print(f"[{job.asset_class}] Fetching {job.symbol} ...")
        try:
            data = await _fetch_data(job, start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
            engine = engines[job.asset_class]
            asset_id = _upsert_asset(job, engine)
            inserted = _store_prices(job, engine, asset_id, data, start_dt, end_dt, chunk_size)
            print(f"  -> stored {inserted} rows")
            stats["processed"] += 1
            stats["inserted"] += inserted
        except Exception as exc:  # noqa: BLE001
            stats["failed"] += 1
            print(f"  !! failed to process {job.symbol}: {exc}")

    for engine in engines.values():
        engine.dispose()

    print(f"Completed. Processed={stats['processed']} Failed={stats['failed']} Rows={stats['inserted']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and store price/macro history for configured assets."
    )
    parser.add_argument(
        "--asset-class",
        default="all",
        choices=[*ASSET_CLASSES, "all"],
        help="Asset class to ingest (default: all).",
    )
    parser.add_argument(
        "--start-date",
        help="Override start date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        help="Override end date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--max-assets",
        type=int,
        help="Optional limit on the number of assets processed.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Rows per bulk insert (default: 1000).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without executing API calls or inserts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(
        _download_impl(
            asset_class=args.asset_class,
            start_date=args.start_date,
            end_date=args.end_date,
            max_assets=args.max_assets,
            chunk_size=args.chunk_size,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
