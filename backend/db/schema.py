"""SQLAlchemy models shared across all asset databases."""

from __future__ import annotations

import datetime as dt
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all models."""


class TimestampMixin:
    """Reusable created/updated helper."""

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Asset(Base, TimestampMixin):
    """Catalog of all tracked tickers/series."""

    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("asset_class", "symbol", name="uq_asset_class_symbol"),
        Index("ix_assets_asset_class_symbol", "asset_class", "symbol"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_class: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    prices: Mapped[List["PriceHistory"]] = relationship(back_populates="asset")
    backtest_runs: Mapped[List["BacktestRun"]] = relationship(back_populates="asset")


class PriceHistory(Base, TimestampMixin):
    """Raw historical values per asset."""

    __tablename__ = "price_history"
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "as_of",
            "source",
            name="uq_price_asset_timestamp_source",
        ),
        Index("ix_price_asset_as_of", "asset_id", "as_of"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    as_of: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="yfinance")

    asset: Mapped[Asset] = relationship(back_populates="prices")


class BacktestRun(Base, TimestampMixin):
    """A single backtest execution for an asset."""

    __tablename__ = "backtest_runs"
    __table_args__ = (
        Index("ix_backtest_asset_created", "asset_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    start_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    forecast_window: Mapped[str] = mapped_column(String(16), nullable=False)
    stride: Mapped[str] = mapped_column(String(16), nullable=False)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'pending'"),
    )
    mape: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mae: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="backtest_runs")
    windows: Mapped[List["ForecastWindow"]] = relationship(
        back_populates="backtest_run",
        cascade="all, delete-orphan",
    )
    metrics: Mapped[List["RunMetric"]] = relationship(
        back_populates="backtest_run",
        cascade="all, delete-orphan",
    )


class ForecastWindow(Base, TimestampMixin):
    """Individual forecast/actual comparisons for a backtest run."""

    __tablename__ = "forecast_windows"
    __table_args__ = (
        Index("ix_forecast_run_target", "backtest_run_id", "target_start"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    backtest_run_id: Mapped[int] = mapped_column(
        ForeignKey("backtest_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    history_start: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    history_end: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_start: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_end: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    forecast_value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    backtest_run: Mapped[BacktestRun] = relationship(back_populates="windows")


class RunMetric(Base, TimestampMixin):
    """Additional metrics for a backtest run."""

    __tablename__ = "run_metrics"
    __table_args__ = (
        UniqueConstraint(
            "backtest_run_id",
            "metric_name",
            name="uq_backtest_metric_name",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    backtest_run_id: Mapped[int] = mapped_column(
        ForeignKey("backtest_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    backtest_run: Mapped[BacktestRun] = relationship(back_populates="metrics")

