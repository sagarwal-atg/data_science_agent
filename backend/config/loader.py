"""Asset configuration loader utilities."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml


CONFIG_PATH = Path(__file__).resolve().parent / "assets.yaml"


@lru_cache(maxsize=1)
def load_asset_config() -> Dict[str, Any]:
    """Load and cache the asset configuration from YAML."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Asset configuration not found at {CONFIG_PATH}. "
            "Ensure backend/config/assets.yaml exists."
        )
    with CONFIG_PATH.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}
    return data


def get_sp500_settings() -> Dict[str, Any]:
    """Return S&P 500 ingestion settings."""
    config = load_asset_config()
    return config.get("sp500", {})


def get_crypto_tickers() -> List[str]:
    """Return the configured list of crypto tickers."""
    config = load_asset_config()
    return list(config.get("crypto", {}).get("tickers", []))


def get_forex_pairs() -> List[str]:
    """Return the configured list of forex pairs."""
    config = load_asset_config()
    return list(config.get("forex", {}).get("pairs", []))


def get_macro_countries() -> List[Dict[str, Any]]:
    """Return macro country definitions (top GDP countries)."""
    config = load_asset_config()
    return list(config.get("macro", {}).get("country_codes", []))

