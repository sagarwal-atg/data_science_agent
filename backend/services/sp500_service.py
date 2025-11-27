"""Utilities for fetching the full S&P 500 constituent list."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from config import get_sp500_settings


@dataclass
class SP500Constituent:
    """Represents a single S&P 500 constituent."""

    symbol: str
    security: str
    sector: str | None = None
    sub_industry: str | None = None
    headquarters: str | None = None


def fetch_sp500_constituents() -> List[SP500Constituent]:
    """Scrape the S&P 500 constituent table from Wikipedia."""
    settings = get_sp500_settings()
    url = settings.get("url")
    table_index = settings.get("table_index", 0)
    symbol_column = settings.get("symbol_column", "Symbol")
    name_column = settings.get("name_column", "Security")

    df = pd.read_csv("assets/sp500.csv")

    constituents: List[SP500Constituent] = []
    for _, row in df.iterrows():
        symbol = str(row[symbol_column]).strip()
        security = str(row[name_column]).strip()
        sector = str(row.get("GICS Sector", "")).strip() or None
        sub_industry = str(row.get("GICS Sub-Industry", "")).strip() or None
        hq = str(row.get("Headquarters Location", "")).strip() or None

        constituents.append(
            SP500Constituent(
                symbol=symbol,
                security=security,
                sector=sector,
                sub_industry=sub_industry,
                headquarters=hq,
            )
        )

    return constituents


def list_sp500_tickers() -> List[str]:
    """Return just the ticker symbols."""
    return [c.symbol for c in fetch_sp500_constituents()]
