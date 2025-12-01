"""
AlphaEvolve Forex Service - Intelligent Trading Strategy Evolution

This service combines:
1. Market Intelligence (factors, sentiment, events, news)
2. AlphaEvolve Strategy Evolution (LLM-driven mutation)
3. Forex Backtesting with comprehensive metrics

The key innovation is filling the LLM context with public market
knowledge to generate strategies informed by real-world conditions.
"""

import asyncio
import json
import logging
import os
import re
import textwrap
import inspect
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List, Dict

logger = logging.getLogger(__name__)


# Popular forex pairs (standalone, no external dependencies)
FOREX_PAIRS = {
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'USDCAD': 'USDCAD=X',
    'USDCHF': 'USDCHF=X',
    'NZDUSD': 'NZDUSD=X',
    'EURGBP': 'EURGBP=X',
    'EURJPY': 'EURJPY=X',
    'GBPJPY': 'GBPJPY=X',
    'AUDJPY': 'AUDJPY=X',
    'EURAUD': 'EURAUD=X',
    'EURCHF': 'EURCHF=X',
    'GBPAUD': 'GBPAUD=X',
    'GBPCAD': 'GBPCAD=X',
}


# ============================================================================
# Seed Strategy Code with EVOLVE-BLOCKs for LLM mutation
# ============================================================================

FOREX_SMA_MOMENTUM_SEED = '''
from collections import deque
import backtrader as bt


class BaseLoggingStrategy(bt.Strategy):
    """Lightweight logger that stores equity curve for later KPIs."""

    params = (("log_equity", True),)

    def __init__(self):
        self._equity_log = deque()

    def next(self):
        if self.p.log_equity:
            self._equity_log.append(
                {
                    "date": self.datas[0].datetime.date(0),
                    "value": self.broker.getvalue(),
                }
            )

    @property
    def equity_curve(self):
        return list(self._equity_log)


class ForexSMAMomentum(BaseLoggingStrategy):
    """SMA crossover momentum strategy for forex."""
    
    # === EVOLVE-BLOCK: params =============================================
    params = dict(
        leverage=0.5,
        sma_fast=10,
        sma_slow=50,
        stop_loss_pct=0.02,
    )
    # === END EVOLVE-BLOCK =================================================
    
    def __init__(self):
        super().__init__()
        # === EVOLVE-BLOCK: indicators =====================================
        self.sma_fast = bt.indicators.SMA(self.data.close, period=self.p.sma_fast)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=self.p.sma_slow)
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
        # === END EVOLVE-BLOCK =============================================
        
        self.order = None
        self.entry_price = None
    
    def next(self):
        super().next()
        
        if self.order:
            return
        
        # === EVOLVE-BLOCK: trading_logic ==================================
        if not self.position:
            if self.crossover > 0:
                size = (self.broker.getvalue() * self.p.leverage) / self.data.close[0]
                self.order = self.buy(size=size)
                self.entry_price = self.data.close[0]
            elif self.crossover < 0:
                size = (self.broker.getvalue() * self.p.leverage) / self.data.close[0]
                self.order = self.sell(size=size)
                self.entry_price = self.data.close[0]
        else:
            if self.position.size > 0 and self.crossover < 0:
                self.order = self.close()
            elif self.position.size < 0 and self.crossover > 0:
                self.order = self.close()
            
            if self.entry_price and self.position.size > 0:
                if self.data.close[0] < self.entry_price * (1 - self.p.stop_loss_pct):
                    self.order = self.close()
            elif self.entry_price and self.position.size < 0:
                if self.data.close[0] > self.entry_price * (1 + self.p.stop_loss_pct):
                    self.order = self.close()
        # === END EVOLVE-BLOCK =============================================


Strategy = ForexSMAMomentum
'''

FOREX_RSI_MEAN_REVERSION_SEED = '''
from collections import deque
import backtrader as bt


class BaseLoggingStrategy(bt.Strategy):
    """Lightweight logger that stores equity curve for later KPIs."""

    params = (("log_equity", True),)

    def __init__(self):
        self._equity_log = deque()

    def next(self):
        if self.p.log_equity:
            self._equity_log.append(
                {
                    "date": self.datas[0].datetime.date(0),
                    "value": self.broker.getvalue(),
                }
            )

    @property
    def equity_curve(self):
        return list(self._equity_log)


class ForexRSIMeanReversion(BaseLoggingStrategy):
    """RSI-based mean reversion strategy for forex."""
    
    # === EVOLVE-BLOCK: params =============================================
    params = dict(
        leverage=0.5,
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70,
        take_profit_pct=0.015,
        stop_loss_pct=0.01,
    )
    # === END EVOLVE-BLOCK =================================================
    
    def __init__(self):
        super().__init__()
        # === EVOLVE-BLOCK: indicators =====================================
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.sma = bt.indicators.SMA(self.data.close, period=20)
        self.atr = bt.indicators.ATR(self.data, period=14)
        # === END EVOLVE-BLOCK =============================================
        
        self.order = None
        self.entry_price = None
    
    def next(self):
        super().next()
        
        if self.order:
            return
        
        # === EVOLVE-BLOCK: trading_logic ==================================
        if not self.position:
            if self.rsi < self.p.rsi_oversold:
                size = (self.broker.getvalue() * self.p.leverage) / self.data.close[0]
                self.order = self.buy(size=size)
                self.entry_price = self.data.close[0]
            elif self.rsi > self.p.rsi_overbought:
                size = (self.broker.getvalue() * self.p.leverage) / self.data.close[0]
                self.order = self.sell(size=size)
                self.entry_price = self.data.close[0]
        else:
            pnl_pct = (self.data.close[0] - self.entry_price) / self.entry_price
            if self.position.size > 0:
                pnl_pct = pnl_pct
            else:
                pnl_pct = -pnl_pct
            
            if pnl_pct >= self.p.take_profit_pct:
                self.order = self.close()
            elif pnl_pct <= -self.p.stop_loss_pct:
                self.order = self.close()
            
            if self.position.size > 0 and self.rsi > 50:
                self.order = self.close()
            elif self.position.size < 0 and self.rsi < 50:
                self.order = self.close()
        # === END EVOLVE-BLOCK =============================================


Strategy = ForexRSIMeanReversion
'''


# ============================================================================
# LLM Prompts for Strategy Evolution
# ============================================================================

EVOLUTION_SYSTEM_PROMPT = """You are AlphaEvolve, an expert quantitative trading strategy developer.
Your task is to evolve and improve forex trading strategies written for Backtrader.

The strategies have editable regions marked with EVOLVE-BLOCK comments:
    # === EVOLVE-BLOCK: <block_name> =====================
    ...code...
    # === END EVOLVE-BLOCK ================================

You can modify the code inside these blocks to improve the strategy.

**RESPOND WITH VALID JSON** containing:
1. Your reasoning process
2. A plain English summary of your changes
3. The actual code modifications

JSON Format:
{
  "reasoning": "Step-by-step analysis of the parent strategy and why you're making specific changes...",
  "summary": "A 2-3 sentence plain English summary of the key changes made and expected impact.",
  "changes": {
    "blocks_modified": ["params", "indicators", "trading_logic"],
    "key_improvements": ["Added RSI filter", "Reduced leverage", "Added trailing stop"]
  },
  "blocks": {
    "params": "params = dict(\\n    leverage=0.4,\\n    sma_fast=12,\\n    ...\\n)",
    "indicators": "self.sma = bt.indicators.SMA(...)",
    "trading_logic": "if condition:\\n    self.buy()..."
  }
}

OR for complete rewrites:
{
  "reasoning": "...",
  "summary": "...",
  "changes": {...},
  "code": "from collections import deque\\nimport backtrader as bt\\n\\nclass Strategy..."
}

**GUIDELINES:**
- Use Backtrader indicators (bt.indicators.SMA, RSI, MACD, Bollinger, ATR, etc.)
- Keep position sizing reasonable (leverage 0.2-0.8)
- Always include stop losses
- Consider trend-following AND mean-reversion approaches
- Try novel indicator combinations
- Optimize for Sharpe ratio > 1.0 and low max drawdown (< 25%)

IMPORTANT: Always include "reasoning", "summary", and "changes" fields!
"""

EVOLUTION_USER_TEMPLATE = """## Current Date: {today}

## Asset: {asset}

## Market Intelligence:
{market_intel}

## Parent Strategy Performance:
{parent_metrics}

## Parent Strategy Code:
```python
{parent_code}
```

## Hall of Fame (Top Strategies by Sharpe):
{hall_of_fame}

## Your Task:
Analyze the parent strategy and create an IMPROVED version that:
1. Has better risk-adjusted returns (higher Sharpe ratio)
2. Has lower maximum drawdown
3. Uses more sophisticated trading logic or indicators
4. Considers the market intelligence provided

Think about:
- Could different indicators work better?
- Are the entry/exit conditions optimal?
- Is position sizing appropriate?
- Could you add trend filters or volatility adjustments?

Return ONLY the JSON with your modifications."""


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class EvolutionProgress:
    """Progress update for evolution streaming."""
    step: int
    total_steps: int
    step_name: str
    step_description: str
    progress_percent: float
    current_strategy: Optional[dict] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class StrategyMetrics:
    """Comprehensive strategy metrics."""
    sharpe: float = 0.0
    sortino: float = 0.0
    cagr: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    calmar: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    n_trades: int = 0
    n_days: int = 0
    monthly_sharpe: float = 0.0
    annual_sharpe: float = 0.0
    monthly_sortino: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'sharpe': self.sharpe,
            'sortino': self.sortino,
            'cagr': self.cagr,
            'total_return': self.total_return,
            'max_drawdown': self.max_drawdown,
            'calmar': self.calmar,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'n_trades': self.n_trades,
            'n_days': self.n_days,
            'monthly_sharpe': self.monthly_sharpe,
            'annual_sharpe': self.annual_sharpe,
            'monthly_sortino': self.monthly_sortino,
        }


@dataclass
class EvolutionLogEntry:
    """Log entry for a single evolution iteration."""
    iteration: int
    parent_id: str
    child_id: str
    reasoning: str  # GPT-5.1's reasoning trace
    summary: str  # Plain English summary of changes
    changes: Dict[str, Any]  # Structured changes info
    parent_sharpe: float
    child_sharpe: float
    improvement: float
    success: bool
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            'iteration': self.iteration,
            'parent_id': self.parent_id,
            'child_id': self.child_id,
            'reasoning': self.reasoning,
            'summary': self.summary,
            'changes': self.changes,
            'parent_sharpe': self.parent_sharpe,
            'child_sharpe': self.child_sharpe,
            'improvement': self.improvement,
            'success': self.success,
            'error': self.error,
            'timestamp': self.timestamp,
        }


@dataclass
class EvolutionResult:
    """Result of strategy evolution run."""
    experiment_id: str
    asset: str
    iterations_completed: int
    best_strategy_id: str
    best_strategy_code: str
    best_metrics: StrategyMetrics
    all_strategies: List[dict]
    equity_curve: List[dict]
    market_intel_used: bool
    evolution_log: List[EvolutionLogEntry] = field(default_factory=list)  # Reasoning traces
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            'experiment_id': self.experiment_id,
            'asset': self.asset,
            'iterations_completed': self.iterations_completed,
            'best_strategy_id': self.best_strategy_id,
            'best_strategy_code': self.best_strategy_code,
            'best_metrics': self.best_metrics.to_dict(),
            'all_strategies': self.all_strategies,
            'equity_curve': self.equity_curve,
            'market_intel_used': self.market_intel_used,
            'evolution_log': [entry.to_dict() for entry in self.evolution_log],
            'created_at': self.created_at,
        }


# ============================================================================
# Simple API Functions (no heavy dependencies)
# ============================================================================

async def get_forex_pairs() -> List[Dict]:
    """Return available forex pairs."""
    return [
        {"pair": pair, "ticker": ticker, "base": pair[:3], "quote": pair[3:6]}
        for pair, ticker in FOREX_PAIRS.items()
    ]


def get_seed_strategies() -> List[Dict]:
    """Return available seed strategies."""
    return [
        {
            "name": "SMA Momentum",
            "description": "Simple moving average crossover strategy",
            "code": FOREX_SMA_MOMENTUM_SEED,
        },
        {
            "name": "RSI Mean Reversion",
            "description": "RSI-based mean reversion strategy",
            "code": FOREX_RSI_MEAN_REVERSION_SEED,
        },
    ]


# ============================================================================
# LLM Integration
# ============================================================================

async def _call_openai(messages: List[Dict[str, str]], model: str = "gpt-5.1") -> str:
    """Call OpenAI GPT-5.1 Responses API for strategy evolution."""
    import openai
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")
    
    client = openai.OpenAI(api_key=api_key)
    
    # Convert messages to Responses API format
    # Combine system and user messages into input
    system_msg = ""
    user_msg = ""
    for msg in messages:
        if msg.get("role") == "system":
            system_msg = msg.get("content", "")
        elif msg.get("role") == "user":
            user_msg = msg.get("content", "")
    
    # Build the input with system instructions
    full_input = f"""## System Instructions:
{system_msg}

## User Request:
{user_msg}

Remember: Respond ONLY with valid JSON. No markdown, no explanations."""
    
    try:
        # Use GPT-5.1 Responses API with high reasoning for complex coding tasks
        response = client.responses.create(
            model=model,
            input=full_input,
            reasoning={"effort": "high"},  # High reasoning for strategy evolution
            text={"verbosity": "medium"},  # Medium verbosity for code
        )
        return response.output_text
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise


def _apply_patch(parent_code: str, diff_json: Dict[str, Any]) -> str:
    """Apply LLM-generated patch to parent code."""
    # Full code replacement
    if "code" in diff_json:
        return diff_json["code"]
    
    blocks = diff_json.get("blocks", {})
    if not blocks:
        return parent_code
    
    # Regex for EVOLVE-BLOCK regions
    block_re = re.compile(
        r"(^[ \t]*# === EVOLVE-BLOCK:\s*(?P<name>\w+).*?$\n)"
        r"(?P<body>.*?)"
        r"(^\s*# === END EVOLVE-BLOCK.*?$)",
        re.M | re.S,
    )
    
    def replace_block(match):
        name = match.group("name")
        head = match.group(1)
        tail = match.group(4)
        new_body = blocks.get(name)
        
        if new_body is None:
            return match.group(0)
        
        # Preserve indentation
        indent = re.match(r"^[ \t]*", match.group("body")).group(0)
        new_body_indented = "\n".join(
            indent + line if line.strip() else line
            for line in new_body.strip().splitlines()
        ) + "\n"
        
        return head + new_body_indented + tail
    
    return block_re.sub(replace_block, parent_code)


def _format_metrics(metrics: Dict[str, Any]) -> str:
    """Format metrics for prompt."""
    if not metrics:
        return "  (No metrics yet - seed strategy)"
    
    lines = [
        f"  Sharpe Ratio: {metrics.get('sharpe', 0):.3f}",
        f"  Sortino Ratio: {metrics.get('sortino', 0):.3f}",
        f"  CAGR: {metrics.get('cagr', 0):.2%}",
        f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}",
        f"  Total Return: {metrics.get('total_return', 0):.2%}",
        f"  Calmar Ratio: {metrics.get('calmar', 0):.3f}",
    ]
    return "\n".join(lines)


def _format_hall_of_fame(strategies: List[Dict]) -> str:
    """Format top strategies for prompt."""
    if not strategies:
        return "  (No strategies in hall of fame yet)"
    
    lines = []
    for i, s in enumerate(strategies[:5], 1):
        m = s.get("metrics", {})
        lines.append(
            f"  {i}. Sharpe: {m.get('sharpe', 0):.3f} | "
            f"CAGR: {m.get('cagr', 0):.2%} | "
            f"MaxDD: {m.get('max_drawdown', 0):.2%}"
        )
    return "\n".join(lines)


def _format_market_intel(market_intel: Optional[Dict]) -> str:
    """Format market intelligence for prompt."""
    if not market_intel:
        return "  (No market intelligence available)"
    
    lines = []
    
    # Overall sentiment
    sentiment = market_intel.get("overall_sentiment", {})
    if sentiment:
        lines.append(f"  Overall Sentiment: {sentiment.get('sentiment', 'neutral')} (score: {sentiment.get('score', 0):.2f})")
    
    # Outlook
    if market_intel.get("short_term_outlook"):
        lines.append(f"  Short-term: {market_intel['short_term_outlook'][:200]}")
    if market_intel.get("medium_term_outlook"):
        lines.append(f"  Medium-term: {market_intel['medium_term_outlook'][:200]}")
    
    # Key risks
    risks = market_intel.get("key_risks", [])
    if risks:
        lines.append("  Key Risks:")
        for r in risks[:3]:
            lines.append(f"    - {r[:100]}")
    
    # Key opportunities
    opps = market_intel.get("key_opportunities", [])
    if opps:
        lines.append("  Key Opportunities:")
        for o in opps[:3]:
            lines.append(f"    - {o[:100]}")
    
    return "\n".join(lines) if lines else "  (No market intelligence available)"


# ============================================================================
# Backtesting
# ============================================================================

def _load_forex_data(pair: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Load forex OHLC data from Yahoo Finance."""
    import yfinance as yf
    import pandas as pd
    
    # Normalize pair name
    pair_clean = pair.upper().replace('/', '').replace(' ', '')
    
    # Build Yahoo Finance ticker
    if '=X' not in pair_clean:
        ticker = f"{pair_clean}=X"
    else:
        ticker = pair_clean
    
    logger.info(f"📈 Loading forex data: pair={pair} → ticker={ticker}")
    
    if not start_date:
        start_date = "2015-01-01"
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"   Date range: {start_date} to {end_date}")
    
    # Download fresh data (bypass cache)
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    except Exception as e:
        logger.error(f"   Failed to download {ticker}: {e}")
        # Fallback to Ticker method
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(start=start_date, end=end_date)
    
    if df.empty:
        raise ValueError(f"No data found for {pair} (ticker: {ticker})")
    
    # Handle multi-index columns from yfinance download
    if hasattr(df.columns, 'get_level_values'):
        df.columns = df.columns.get_level_values(0)
    
    # Normalize column names to lowercase
    df.columns = df.columns.str.lower()
    df.index.name = 'date'
    
    # Log data summary for debugging
    first_close = float(df['close'].iloc[0])
    last_close = float(df['close'].iloc[-1])
    logger.info(f"   ✓ Loaded {len(df)} rows for {ticker}")
    logger.info(f"   First: {df.index[0]} @ {first_close:.4f}")
    logger.info(f"   Last:  {df.index[-1]} @ {last_close:.4f}")
    
    return df


def _run_backtest_internal(code: str, pair: str, start_date: Optional[str], end_date: Optional[str]):
    """Run backtest using backtrader."""
    import importlib.util
    import sys
    import tempfile
    from pathlib import Path
    import backtrader as bt
    import pandas as pd
    import numpy as np
    
    # Load forex data
    df = _load_forex_data(pair, start_date, end_date)
    
    # Create strategy module from code
    name = f"strategy_{hash(code) % 10**8}"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(code)
        tmp_path = Path(tmp.name)
    
    try:
        spec = importlib.util.spec_from_file_location(name, tmp_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    finally:
        tmp_path.unlink(missing_ok=True)
    
    # Find strategy class
    strat_cls = None
    for attr in ("Strategy", "STRATEGY_CLASS"):
        if hasattr(mod, attr):
            cls = getattr(mod, attr)
            if inspect.isclass(cls) and issubclass(cls, bt.Strategy):
                strat_cls = cls
                break
    
    if not strat_cls:
        for v in mod.__dict__.values():
            if inspect.isclass(v) and issubclass(v, bt.Strategy) and v.__name__ not in ("BaseLoggingStrategy",):
                strat_cls = v
                break
    
    if not strat_cls:
        raise ValueError("No compatible Strategy class found in code")
    
    # Setup cerebro
    cerebro = bt.Cerebro()
    
    df_bt = df.copy()
    df_bt.index.name = 'datetime'
    data_feed = bt.feeds.PandasData(dataname=df_bt)
    cerebro.adddata(data_feed, name=pair)
    
    cerebro.addstrategy(strat_cls)
    cerebro.broker.set_cash(100_000)
    
    # Run backtest
    results = cerebro.run(maxcpus=1)
    strat = results[0]
    
    # Extract equity curve
    equity_raw = strat.equity_curve if hasattr(strat, 'equity_curve') else []
    if not equity_raw:
        equity_raw = [{"date": datetime.now().date(), "value": cerebro.broker.getvalue()}]
    
    curve = pd.Series(
        [pt["value"] for pt in equity_raw],
        index=[pt["date"] for pt in equity_raw],
        name="equity",
    )
    curve.index = pd.to_datetime(curve.index)
    
    # Calculate metrics
    rets = curve.pct_change().dropna().values
    
    def sharpe(returns, rf=0.0, periods_per_year=252):
        if len(returns) < 2:
            return 0.0
        excess = returns - rf / periods_per_year
        std = np.std(excess, ddof=1)
        if std == 0 or np.isnan(std):
            return 0.0
        return np.sqrt(periods_per_year) * np.mean(excess) / std
    
    def sortino(returns, rf=0.0, periods_per_year=252):
        if len(returns) < 2:
            return 0.0
        excess = returns - rf / periods_per_year
        downside = excess[excess < 0]
        if len(downside) < 2:
            return 0.0 if np.mean(excess) <= 0 else float('inf')
        downside_std = np.sqrt(np.mean(downside ** 2))
        if downside_std == 0 or np.isnan(downside_std):
            return 0.0
        return np.sqrt(periods_per_year) * np.mean(excess) / downside_std
    
    def cagr(equity_curve, periods_per_year=252):
        n_years = len(equity_curve) / periods_per_year
        if n_years <= 0:
            return 0.0
        return (equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / n_years) - 1
    
    def max_drawdown(equity_curve):
        cummax = equity_curve.cummax()
        dd = (equity_curve - cummax) / cummax
        return float(dd.min())
    
    metrics = StrategyMetrics(
        sharpe=sharpe(rets),
        sortino=sortino(rets),
        cagr=cagr(curve),
        total_return=float(curve.iloc[-1] / curve.iloc[0] - 1),
        max_drawdown=max_drawdown(curve),
        calmar=cagr(curve) / abs(max_drawdown(curve)) if max_drawdown(curve) != 0 else 0,
        n_days=len(curve),
    )
    
    equity_curve = [
        {"date": d.isoformat() if hasattr(d, 'isoformat') else str(d), "value": float(v)}
        for d, v in zip(curve.index, curve.values)
    ]
    
    return metrics, equity_curve


async def run_single_backtest(
    code: str,
    pair: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict:
    """Run a single backtest on provided code."""
    logger.info(f"🔬 Running single backtest for pair: {pair}")
    logger.info(f"   Date range: {start_date or 'default'} to {end_date or 'now'}")
    
    loop = asyncio.get_event_loop()
    metrics, equity_curve = await loop.run_in_executor(
        None,
        lambda: _run_backtest_internal(code, pair, start_date, end_date)
    )
    
    logger.info(f"   ✓ Backtest complete for {pair}: Sharpe={metrics.sharpe:.3f}")
    
    return {
        "code": code,
        "pair": pair,
        "metrics": metrics.to_dict(),
        "equity_curve": equity_curve,
        "start_date": start_date,
        "end_date": end_date,
    }


# ============================================================================
# Main Evolution Function with LLM
# ============================================================================

async def evolve_forex_strategy(
    pair: str,
    iterations: int = 5,
    use_market_intel: bool = True,
    market_intel: Optional[dict] = None,
    experiment_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    seed_strategies: Optional[List[str]] = None,
    progress_callback=None,
) -> EvolutionResult:
    """
    Run AlphaEvolve strategy evolution for forex using LLM (GPT-5.1).
    
    This uses OpenAI to generate intelligent strategy mutations,
    not just parameter tweaks.
    """
    import uuid
    import random
    
    experiment_id = experiment_name or f"forex_{pair}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    seeds = seed_strategies or [FOREX_SMA_MOMENTUM_SEED, FOREX_RSI_MEAN_REVERSION_SEED]
    
    # Population of strategies
    population: List[Dict] = []
    all_strategies = []
    
    if progress_callback:
        await progress_callback(EvolutionProgress(
            step=0,
            total_steps=iterations,
            step_name="Initialization",
            step_description="Evaluating seed strategies...",
            progress_percent=2,
        ))
    
    # Evaluate seed strategies
    logger.info(f"🧬 AlphaEvolve: Evaluating {len(seeds)} seed strategies for {pair}...")
    for i, seed_code in enumerate(seeds):
        try:
            metrics, equity_curve = _run_backtest_internal(seed_code, pair, start_date, end_date)
            
            strategy_id = str(uuid.uuid4())
            strategy_data = {
                "id": strategy_id,
                "iteration": 0,
                "metrics": metrics.to_dict(),
                "code": seed_code,
                "equity_curve": equity_curve,
            }
            population.append(strategy_data)
            all_strategies.append({
                "id": strategy_id,
                "iteration": 0,
                "metrics": metrics.to_dict(),
                "parent_id": None,
            })
            
            logger.info(f"  ✓ Seed {i+1}: Sharpe={metrics.sharpe:.3f}, CAGR={metrics.cagr:.2%}")
        except Exception as e:
            logger.error(f"  ✗ Seed {i+1} failed: {e}")
    
    if not population:
        raise RuntimeError("No seed strategies could be evaluated")
    
    # Evolution log to track reasoning traces
    evolution_log: List[EvolutionLogEntry] = []
    
    # Evolution loop with LLM
    logger.info(f"🚀 Starting LLM-based evolution with {iterations} iterations...")
    
    for iteration in range(1, iterations + 1):
        if progress_callback:
            await progress_callback(EvolutionProgress(
                step=iteration,
                total_steps=iterations,
                step_name=f"Iteration {iteration}",
                step_description=f"Generating strategy mutations with GPT-5.1...",
                progress_percent=5 + (iteration / iterations) * 90,
            ))
        
        # Sort by Sharpe (best first)
        population.sort(key=lambda x: x["metrics"]["sharpe"], reverse=True)
        
        # Select parent (top performer or random from top 50%)
        elite_count = max(1, len(population) // 2)
        parent = random.choice(population[:elite_count])
        
        logger.info(f"\n📊 Iteration {iteration}/{iterations}")
        logger.info(f"  Parent Sharpe: {parent['metrics']['sharpe']:.3f}")
        
        # Build prompt for LLM
        user_prompt = EVOLUTION_USER_TEMPLATE.format(
            today=datetime.now().strftime("%Y-%m-%d"),
            asset=pair,
            market_intel=_format_market_intel(market_intel),
            parent_metrics=_format_metrics(parent["metrics"]),
            parent_code=parent["code"][:6000],  # Truncate for token limits
            hall_of_fame=_format_hall_of_fame(population[:5]),
        )
        
        messages = [
            {"role": "system", "content": EVOLUTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        
        # Call LLM
        try:
            logger.info(f"  🤖 Calling GPT-5.1 for strategy evolution...")
            response = await _call_openai(messages, model="gpt-5.1")
            
            # Parse response
            try:
                diff_json = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"  ✗ Invalid JSON from LLM: {e}")
                # Log failed iteration
                evolution_log.append(EvolutionLogEntry(
                    iteration=iteration,
                    parent_id=parent["id"],
                    child_id="",
                    reasoning="Failed to parse LLM response",
                    summary=f"JSON parse error: {str(e)}",
                    changes={},
                    parent_sharpe=parent["metrics"]["sharpe"],
                    child_sharpe=0.0,
                    improvement=0.0,
                    success=False,
                    error=str(e),
                ))
                continue
            
            # Extract reasoning and summary from LLM response
            reasoning = diff_json.get("reasoning", "No reasoning provided by model")
            summary = diff_json.get("summary", "No summary provided")
            changes = diff_json.get("changes", {
                "blocks_modified": list(diff_json.get("blocks", {}).keys()) if "blocks" in diff_json else ["full_rewrite"],
                "key_improvements": ["See code changes"]
            })
            
            # Log reasoning trace
            logger.info(f"  💭 Reasoning: {reasoning[:200]}...")
            logger.info(f"  📝 Summary: {summary}")
            
            # Apply patch to create child
            child_code = _apply_patch(parent["code"], diff_json)
            
            # Log what was changed
            if "code" in diff_json:
                logger.info(f"  📝 LLM provided complete new strategy")
            elif "blocks" in diff_json:
                blocks_changed = list(diff_json["blocks"].keys())
                logger.info(f"  📝 LLM modified blocks: {blocks_changed}")
            
            # Evaluate child
            try:
                metrics, equity_curve = _run_backtest_internal(child_code, pair, start_date, end_date)
                
                child_id = str(uuid.uuid4())
                child_data = {
                    "id": child_id,
                    "iteration": iteration,
                    "metrics": metrics.to_dict(),
                    "code": child_code,
                    "equity_curve": equity_curve,
                }
                population.append(child_data)
                all_strategies.append({
                    "id": child_id,
                    "iteration": iteration,
                    "metrics": metrics.to_dict(),
                    "parent_id": parent["id"],
                })
                
                # Check if improvement
                improvement = metrics.sharpe - parent["metrics"]["sharpe"]
                if improvement > 0:
                    logger.info(f"  ✅ Child Sharpe: {metrics.sharpe:.3f} (+{improvement:.3f} improvement!)")
                else:
                    logger.info(f"  ⚠️ Child Sharpe: {metrics.sharpe:.3f} ({improvement:.3f})")
                
                # Create evolution log entry with reasoning
                evolution_log.append(EvolutionLogEntry(
                    iteration=iteration,
                    parent_id=parent["id"],
                    child_id=child_id,
                    reasoning=reasoning,
                    summary=summary,
                    changes=changes,
                    parent_sharpe=parent["metrics"]["sharpe"],
                    child_sharpe=metrics.sharpe,
                    improvement=improvement,
                    success=True,
                ))
                    
            except Exception as e:
                logger.error(f"  ✗ Child backtest failed: {e}")
                # Log failed backtest
                evolution_log.append(EvolutionLogEntry(
                    iteration=iteration,
                    parent_id=parent["id"],
                    child_id="",
                    reasoning=reasoning,
                    summary=summary,
                    changes=changes,
                    parent_sharpe=parent["metrics"]["sharpe"],
                    child_sharpe=0.0,
                    improvement=0.0,
                    success=False,
                    error=f"Backtest failed: {str(e)}",
                ))
                continue
                
        except Exception as e:
            logger.error(f"  ✗ LLM evolution failed: {e}")
            # Log failed LLM call
            evolution_log.append(EvolutionLogEntry(
                iteration=iteration,
                parent_id=parent["id"],
                child_id="",
                reasoning="LLM call failed",
                summary=str(e),
                changes={},
                parent_sharpe=parent["metrics"]["sharpe"],
                child_sharpe=0.0,
                improvement=0.0,
                success=False,
                error=str(e),
            ))
            continue
        
        # Prune population (keep top performers)
        population.sort(key=lambda x: x["metrics"]["sharpe"], reverse=True)
        max_pop_size = max(10, iterations * 2)
        population = population[:max_pop_size]
        
        # Small delay
        await asyncio.sleep(0.5)
    
    # Get best strategy
    population.sort(key=lambda x: x["metrics"]["sharpe"], reverse=True)
    best_strategy = population[0]
    best_metrics = StrategyMetrics(**best_strategy["metrics"])
    
    if progress_callback:
        await progress_callback(EvolutionProgress(
            step=iterations,
            total_steps=iterations,
            step_name="Complete",
            step_description=f"Best Sharpe: {best_metrics.sharpe:.3f}",
            progress_percent=100,
        ))
    
    logger.info(f"\n🏆 Evolution complete!")
    logger.info(f"  Best Sharpe: {best_metrics.sharpe:.3f}")
    logger.info(f"  Best CAGR: {best_metrics.cagr:.2%}")
    logger.info(f"  Max Drawdown: {best_metrics.max_drawdown:.2%}")
    
    return EvolutionResult(
        experiment_id=experiment_id,
        asset=pair,
        iterations_completed=iterations,
        best_strategy_id=best_strategy["id"],
        best_strategy_code=best_strategy["code"],
        best_metrics=best_metrics,
        all_strategies=all_strategies,
        equity_curve=best_strategy["equity_curve"],
        market_intel_used=use_market_intel and market_intel is not None,
        evolution_log=evolution_log,
    )
