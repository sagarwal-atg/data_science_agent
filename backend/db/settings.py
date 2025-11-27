"""Database connection + bootstrap utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict

from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine

from config import load_asset_config

from .schema import Base


@dataclass
class DatabaseSettings:
    """Connection info for the Postgres cluster."""

    host: str
    port: int
    user: str
    password: str
    admin_db: str
    app_prefix: str = ""

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        """Load settings from environment variables."""
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            admin_db=os.getenv("POSTGRES_SUPER_DB", "postgres"),
            app_prefix=os.getenv("POSTGRES_APP_DB_PREFIX", ""),
        )


def get_asset_databases(prefix: str | None = None) -> Dict[str, str]:
    """Map asset classes to database names, applying the optional prefix."""
    config = load_asset_config()
    prefix = prefix or ""
    mapping = {}
    for asset_class in ("sp500", "crypto", "forex", "macro"):
        section = config.get(asset_class, {})
        db_name = section.get("database")
        if not db_name:
            raise ValueError(f"No database configured for asset class '{asset_class}'")
        mapping[asset_class] = f"{prefix}{db_name}"
    return mapping


def build_engine_for(
    database: str,
    settings: DatabaseSettings,
    *,
    autocommit: bool = False,
) -> Engine:
    """Create a SQLAlchemy engine for the given database."""
    url = URL.create(
        "postgresql+psycopg",
        username=settings.user,
        password=settings.password,
        host=settings.host,
        port=settings.port,
        database=database,
    )
    isolation = "AUTOCOMMIT" if autocommit else None
    return create_engine(url, isolation_level=isolation)


class DatabaseBootstrapper:
    """Create per-asset databases and core tables."""

    def __init__(self, settings: DatabaseSettings | None = None):
        self.settings = settings or DatabaseSettings.from_env()
        self.targets = get_asset_databases(self.settings.app_prefix)

    def _ensure_database_exists(self, admin_engine: Engine, db_name: str) -> None:
        """Create the database if it doesn't already exist."""
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                conn.commit()

    def bootstrap(self, *, create_tables: bool = True) -> None:
        """Ensure all databases exist and contain the latest schema."""
        admin_engine = build_engine_for(
            self.settings.admin_db,
            self.settings,
            autocommit=True,
        )
        try:
            for asset_class, db_name in self.targets.items():
                self._ensure_database_exists(admin_engine, db_name)
                if create_tables:
                    engine = build_engine_for(db_name, self.settings, autocommit=True)
                    try:
                        Base.metadata.create_all(engine)
                    finally:
                        engine.dispose()
        finally:
            admin_engine.dispose()

