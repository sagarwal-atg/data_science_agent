"""
Common performance-metric helpers (numpy-friendly, no external deps).
"""

import numpy as np
import pandas as pd


def _to_np(arr):
    if isinstance(arr, (pd.Series | pd.DataFrame)):
        arr = arr.values
    return np.asarray(arr, dtype=float)


# ------------------------------------------------------------------ #
# BASIC METRICS
# ------------------------------------------------------------------ #
def daily_returns(equity_curve: pd.Series) -> np.ndarray:
    return _to_np(equity_curve.pct_change().dropna())


def cagr(equity_curve: pd.Series, periods_per_year: int = 252) -> float:
    arr = _to_np(equity_curve)
    n_years = len(arr) / periods_per_year
    if n_years <= 0:
        return 0.0
    return (arr[-1] / arr[0]) ** (1 / n_years) - 1


def sharpe(returns: np.ndarray, rf: float = 0.0, periods_per_year: int = 252) -> float:
    """
    Calculate annualized Sharpe ratio.
    
    Sharpe = sqrt(periods_per_year) * mean(excess_returns) / std(excess_returns)
    """
    excess = returns - rf / periods_per_year
    if len(excess) < 2:
        return 0.0
    std = excess.std(ddof=1)
    if std == 0 or np.isnan(std):
        return 0.0
    return np.sqrt(periods_per_year) * excess.mean() / std


def sortino(returns: np.ndarray, rf: float = 0.0, periods_per_year: int = 252) -> float:
    """
    Calculate annualized Sortino ratio.
    
    Sortino = sqrt(periods_per_year) * mean(excess_returns) / downside_deviation
    
    Uses only negative returns for downside deviation (penalizes downside risk only).
    """
    excess = returns - rf / periods_per_year
    if len(excess) < 2:
        return 0.0
    
    # Downside deviation: std of returns below target (0)
    downside_returns = excess[excess < 0]
    if len(downside_returns) < 2:
        return 0.0 if excess.mean() <= 0 else float('inf')  # No downside volatility
    
    downside_std = np.sqrt(np.mean(downside_returns ** 2))
    if downside_std == 0 or np.isnan(downside_std):
        return 0.0 if excess.mean() <= 0 else float('inf')
    
    return np.sqrt(periods_per_year) * excess.mean() / downside_std


def max_drawdown(equity_curve: pd.Series) -> float:
    """Return *percentage* max drawdown (negative value)."""
    cummax = equity_curve.cummax()
    dd = (equity_curve - cummax) / cummax
    return dd.min()


def calmar(cagr_: float, mdd: float) -> float:
    return cagr_ / abs(mdd) if mdd != 0 else 0


def monthly_sharpe(equity_curve: pd.Series, rf: float = 0.0) -> float:
    """Calculate Sharpe ratio from monthly returns."""
    # Resample to monthly
    monthly = equity_curve.resample('M').last()
    rets = _to_np(monthly.pct_change().dropna())
    return sharpe(rets, rf=rf, periods_per_year=12)


def annual_sharpe(equity_curve: pd.Series, rf: float = 0.0) -> float:
    """Calculate Sharpe ratio from annual returns."""
    # Resample to annual
    annual = equity_curve.resample('Y').last()
    rets = _to_np(annual.pct_change().dropna())
    if len(rets) < 2:
        return 0.0
    return sharpe(rets, rf=rf, periods_per_year=1)


def monthly_sortino(equity_curve: pd.Series, rf: float = 0.0) -> float:
    """Calculate Sortino ratio from monthly returns."""
    monthly = equity_curve.resample('M').last()
    rets = _to_np(monthly.pct_change().dropna())
    return sortino(rets, rf=rf, periods_per_year=12)


def win_rate(returns: np.ndarray) -> float:
    """Calculate percentage of positive return periods."""
    if len(returns) == 0:
        return 0.0
    return float(np.sum(returns > 0)) / len(returns)


def profit_factor(returns: np.ndarray) -> float:
    """Calculate ratio of gross profits to gross losses."""
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    if losses == 0:
        return float('inf') if gains > 0 else 0.0
    return gains / losses
