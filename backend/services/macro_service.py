"""Macro data service for GDP series using World Bank API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from pandas_datareader import wb
from pydantic import BaseModel

from config import load_asset_config, get_macro_countries


class MacroTimeSeriesData(BaseModel):
    """Macro time series data response model."""

    indicator: str
    country_iso3: str
    country_name: str
    timestamps: list[str]
    values: list[float]
    units: str = "USD"


def _macro_config() -> Dict[str, Any]:
    """Return cached macro configuration."""
    return load_asset_config().get("macro", {})


def list_top_gdp_countries() -> List[Dict[str, Any]]:
    """Return configured top GDP countries."""
    return get_macro_countries()


def _find_country_metadata(country_code: str) -> Dict[str, Any]:
    """Find the country metadata from config."""
    normalized = country_code.upper()
    for country in list_top_gdp_countries():
        if (
            normalized == country.get("iso3", "").upper()
            or normalized == country.get("iso2", "").upper()
        ):
            return country
    return {
        "name": normalized,
        "iso3": normalized,
        "iso2": normalized[:2],
    }


async def fetch_gdp_series(
    country_code: str,
    indicator: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> MacroTimeSeriesData:
    """
    Fetch GDP data for a country using the World Bank API.

    Args:
        country_code: ISO2 or ISO3 country code.
        indicator: World Bank indicator id, defaults to config indicator.
        start_year: Lower bound year (inclusive).
        end_year: Upper bound year (inclusive).
    """

    config = _macro_config()
    indicator = indicator or config.get("indicator", "NY.GDP.MKTP.CD")
    start_year = start_year or config.get("start_year", 2000)
    end_year = end_year or config.get("end_year", pd.Timestamp.utcnow().year)

    country_meta = _find_country_metadata(country_code)
    iso3_code = country_meta.get("iso3", country_code).upper()

    df = wb.download(
        indicator=indicator,
        country=iso3_code,
        start=start_year,
        end=end_year,
    )

    if df.empty:
        raise ValueError(
            f"No GDP data found for {country_meta.get('name', iso3_code)} "
            f"({iso3_code}) using indicator {indicator} between "
            f"{start_year} and {end_year}."
        )

    df = df.reset_index().rename(columns={indicator: "value"}).sort_values("year")
    timestamps = pd.to_datetime(df["year"].astype(str)).dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
    values = df["value"].astype(float).fillna(0).tolist()

    return MacroTimeSeriesData(
        indicator=indicator,
        country_iso3=iso3_code,
        country_name=country_meta.get("name", iso3_code),
        timestamps=timestamps,
        values=values,
        units="USD",
    )

