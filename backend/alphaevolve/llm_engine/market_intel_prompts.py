"""
Market-Intelligence-Aware prompts for AlphaEvolve.

These prompts are designed to incorporate real-time market intelligence,
macroeconomic factors, and public events into strategy evolution.

The key innovation is filling the LLM context window with:
1. Asset-specific factors (what drives the price)
2. Current market sentiment
3. Upcoming economic events
4. Recent news and developments
5. Risk/opportunity analysis

This allows the LLM to generate strategies that are informed by
real-world market conditions.
"""

import textwrap
from datetime import datetime
from typing import Any, Optional, Dict, List

from alphaevolve.evolution.prompt_ga import PromptGenome
from alphaevolve.store.sqlite import ProgramStore

# Default metric for ranking
DEFAULT_HOF_METRIC = "sharpe"


MARKET_INTEL_SYSTEM_MSG = """\
You are Alpha-Trader Evolution-Engine, specialized in creating data-driven
trading strategies for forex and other financial assets.

Your strategies are built for Backtrader and must inherit from BaseLoggingStrategy.
All editable regions are delimited like this:

    # === EVOLVE-BLOCK: <block_name> =================================
    ...current implementation...
    # === END EVOLVE-BLOCK ===========================================

**IMPORTANT CONTEXT**: You will be provided with real-time market intelligence
including:
- Key factors that drive this asset's price
- Current market sentiment (bullish/bearish/neutral)
- Upcoming economic events that may impact the asset
- Recent news and developments
- Key risks and opportunities

Use this market intelligence to inform your strategy design. Consider:
1. Which factors should trigger position changes
2. How to adjust position sizing based on sentiment
3. When to be cautious around major events
4. How to capitalize on opportunities while managing risks

**STRATEGY GUIDELINES**:
- Prioritize risk-adjusted returns (Sharpe > 1.0, Sortino > 1.5)
- Keep maximum drawdown below -25%
- Use proper position sizing (never more than 20% in single position)
- Consider both trend-following and mean-reversion approaches
- Include proper entry/exit logic with stop losses

**Return ONLY valid JSON** with either:
  • "blocks": an object mapping <block_name> → replacement code *inside*
    that block (keep indentation coherent), or
  • "code": a complete strategy (if a wholesale rewrite is easier).

NO additional keys, NO markdown, NO prose explanation.
"""


MARKET_INTEL_USER_TEMPLATE = """\
Today's date: {today}

═══════════════════════════════════════════════════════════════════════════════
ASSET: {asset}
═══════════════════════════════════════════════════════════════════════════════

MARKET INTELLIGENCE SUMMARY
───────────────────────────────────────────────────────────────────────────────
Overall Sentiment: {sentiment} (Score: {sentiment_score:.2f})
Short-term Outlook: {short_term_outlook}
Medium-term Outlook: {medium_term_outlook}

KEY FACTORS DRIVING {asset}:
{factors_summary}

KEY RISKS:
{risks}

KEY OPPORTUNITIES:
{opportunities}

UPCOMING EVENTS:
{events}

RECENT NEWS:
{news_summary}

═══════════════════════════════════════════════════════════════════════════════
PARENT STRATEGY
═══════════════════════════════════════════════════════════════════════════════

Parent KPIs:
{metrics_tbl}

Parent code:
```python
{parent_code}
```

═══════════════════════════════════════════════════════════════════════════════
HALL OF FAME (Top {k} by {metric})
═══════════════════════════════════════════════════════════════════════════════
{hof}

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════════════════════════
1. Analyze the market intelligence and identify tradeable signals
2. Improve the strategy to achieve better risk-adjusted returns
3. Consider the current sentiment and upcoming events in your logic
4. Target: Sharpe > 1.0, Sortino > 1.5, Max Drawdown > -25%
5. Reply using the structured JSON schema described by the system prompt

Focus on incorporating the market factors and sentiment into the trading logic.
Think about how {asset} typically reacts to the factors listed above.
"""


def _format_metrics(metrics: Optional[Dict[str, Any]]) -> str:
    """Format strategy metrics for display."""
    if not metrics:
        return "  (none yet – seed strategy)"
    
    priority_metrics = ['sharpe', 'sortino', 'cagr', 'max_drawdown', 'calmar', 'total_return']
    lines = []
    
    for key in priority_metrics:
        if key in metrics:
            val = metrics[key]
            if isinstance(val, float):
                if key in ['cagr', 'total_return', 'max_drawdown']:
                    lines.append(f"  {key}: {val:.2%}")
                else:
                    lines.append(f"  {key}: {val:.4f}")
            else:
                lines.append(f"  {key}: {val}")
    
    # Add any remaining metrics
    for k, v in metrics.items():
        if k not in priority_metrics:
            if isinstance(v, float):
                lines.append(f"  {k}: {v:.4g}")
            else:
                lines.append(f"  {k}: {v}")
    
    return "\n".join(lines)


def _format_hof(store: ProgramStore, k: int = 5, metric: str = DEFAULT_HOF_METRIC) -> str:
    """Format hall of fame for display."""
    rows = store.top_k(k=k, metric=metric)
    if not rows:
        return "  (empty – still warming up)"
    
    lines = []
    for i, r in enumerate(rows, 1):
        m = r["metrics"]
        sharpe = m.get('sharpe', 0)
        sortino = m.get('sortino', 0)
        cagr = m.get('cagr', 0)
        mdd = m.get('max_drawdown', 0)
        lines.append(
            f"  {i}. Sharpe {sharpe:.3f} | Sortino {sortino:.3f} | "
            f"CAGR {cagr:.2%} | MaxDD {mdd:.2%}"
        )
    return "\n".join(lines)


def _format_factors(factors: List[Dict]) -> str:
    """Format market factors for display."""
    if not factors:
        return "  No factors identified"
    
    lines = []
    for f in factors[:8]:  # Limit to top 8 factors
        name = f.get('name', 'Unknown')
        category = f.get('category', 'general')
        influence = f.get('influence_strength', 'medium')
        direction = f.get('influence_direction', 'complex')
        
        icon = "🔵" if direction == "positive" else "🔴" if direction == "negative" else "⚪"
        lines.append(f"  {icon} {name} ({category})")
        lines.append(f"      Influence: {influence} | Direction: {direction}")
    
    return "\n".join(lines)


def _format_risks(risks: List[str]) -> str:
    """Format risks for display."""
    if not risks:
        return "  No major risks identified"
    return "\n".join(f"  ⚠️ {r}" for r in risks[:5])


def _format_opportunities(opportunities: List[str]) -> str:
    """Format opportunities for display."""
    if not opportunities:
        return "  No opportunities identified"
    return "\n".join(f"  ✅ {o}" for o in opportunities[:5])


def _format_events(events: List[Dict]) -> str:
    """Format upcoming events for display."""
    if not events:
        return "  No major upcoming events"
    
    lines = []
    for e in events[:5]:
        date = e.get('date', 'TBD')
        name = e.get('name', 'Unknown Event')
        importance = e.get('importance', 'medium')
        
        icon = "🔴" if importance == "high" else "🟡" if importance == "medium" else "🟢"
        lines.append(f"  {icon} {date}: {name}")
    
    return "\n".join(lines)


def _format_news(news: List[Dict]) -> str:
    """Format recent news for display."""
    if not news:
        return "  No recent news"
    
    lines = []
    for n in news[:5]:
        title = n.get('title', 'Untitled')
        source = n.get('source', 'Unknown')
        date = n.get('date', '')
        
        lines.append(f"  • {title}")
        if source or date:
            lines.append(f"    ({source}{', ' + date if date else ''})")
    
    return "\n".join(lines)


def build_market_intel_prompt(
    parent: Optional[Dict[str, Any]],
    store: ProgramStore,
    asset: str,
    market_intel: Optional[Dict[str, Any]] = None,
    metric: str = DEFAULT_HOF_METRIC,
    prompt: Optional[PromptGenome] = None,
) -> List[Dict[str, str]]:
    """
    Build prompt messages with market intelligence context.
    
    Args:
        parent: Parent strategy dict with 'code' and 'metrics'
        store: ProgramStore for hall of fame
        asset: Asset being traded (e.g., 'EURUSD')
        market_intel: Market intelligence report dict
        metric: Metric for ranking hall of fame
        prompt: Optional custom prompt genome
        
    Returns:
        List of message dicts for OpenAI API
    """
    prompt = prompt or PromptGenome(
        system_msg=MARKET_INTEL_SYSTEM_MSG,
        user_template=MARKET_INTEL_USER_TEMPLATE
    )
    
    today = datetime.utcnow().date().isoformat()
    parent_code = textwrap.indent(
        textwrap.dedent(parent["code"] if parent else ""),
        "    "
    )[:6000]  # Increased limit for full code
    
    # Extract market intelligence data
    if market_intel:
        sentiment = market_intel.get('overall_sentiment', {})
        sentiment_label = sentiment.get('sentiment', 'neutral') if isinstance(sentiment, dict) else 'neutral'
        sentiment_score = sentiment.get('score', 0.0) if isinstance(sentiment, dict) else 0.0
        
        short_term = market_intel.get('short_term_outlook', 'No outlook available')
        medium_term = market_intel.get('medium_term_outlook', 'No outlook available')
        
        # Extract factors from market map or factor analysis
        factors = []
        if 'market_map' in market_intel:
            map_nodes = market_intel['market_map'].get('nodes', [])
            for node in map_nodes:
                if node.get('type') == 'factor':
                    factors.append({
                        'name': node.get('label', ''),
                        'category': node.get('category', 'general'),
                        'influence_strength': 'high' if node.get('importance', 0) > 0.7 else 'medium',
                        'influence_direction': 'positive' if (node.get('sentiment', {}) or {}).get('score', 0) > 0 else 'negative',
                    })
        elif 'factor_analysis' in market_intel:
            fa_profile = market_intel['factor_analysis'].get('profile', {})
            factors = fa_profile.get('factors', [])
        
        risks = market_intel.get('key_risks', [])
        opportunities = market_intel.get('key_opportunities', [])
        events = market_intel.get('upcoming_events', [])
        news = market_intel.get('top_news', [])
    else:
        sentiment_label = "neutral"
        sentiment_score = 0.0
        short_term = "Market intelligence not available"
        medium_term = "Market intelligence not available"
        factors = []
        risks = []
        opportunities = []
        events = []
        news = []
    
    user_msg = prompt.user_template.format(
        today=today,
        asset=asset,
        sentiment=sentiment_label,
        sentiment_score=sentiment_score,
        short_term_outlook=short_term,
        medium_term_outlook=medium_term,
        factors_summary=_format_factors(factors),
        risks=_format_risks(risks),
        opportunities=_format_opportunities(opportunities),
        events=_format_events(events),
        news_summary=_format_news(news),
        metrics_tbl=_format_metrics(parent["metrics"] if parent else None),
        parent_code=parent_code or "(root seed – no parent)",
        hof=_format_hof(store, k=5, metric=metric),
        k=5,
        metric=metric,
    )
    
    return [
        {"role": "system", "content": prompt.system_msg},
        {"role": "user", "content": user_msg},
    ]


# Simplified prompt without market intelligence (for fallback)
SIMPLE_FOREX_SYSTEM_MSG = """\
You are Alpha-Trader Evolution-Engine for forex trading.

Your strategies are built for Backtrader and must inherit from BaseLoggingStrategy.
All editable regions are delimited with EVOLVE-BLOCK markers.

**Return ONLY valid JSON** with either:
  • "blocks": object mapping <block_name> → replacement code, or
  • "code": complete strategy code

NO additional keys, NO markdown, NO prose.
"""


SIMPLE_FOREX_USER_TEMPLATE = """\
Today's date: {today}

ASSET: {asset}

Parent KPIs:
{metrics_tbl}

Parent code:
```python
{parent_code}
```

Hall-of-fame (top {k} by {metric}):
{hof}

Task:
1. Improve risk-adjusted returns (target Sharpe > 1.0, Sortino > 1.5)
2. Keep max drawdown above -25%
3. Modify EVOLVE-BLOCKs or provide full "code"
4. Reply using structured JSON schema
"""


def build_simple_prompt(
    parent: Optional[Dict[str, Any]],
    store: ProgramStore,
    asset: str = "FOREX",
    metric: str = DEFAULT_HOF_METRIC,
) -> List[Dict[str, str]]:
    """Build simple prompt without market intelligence."""
    today = datetime.utcnow().date().isoformat()
    parent_code = textwrap.indent(
        textwrap.dedent(parent["code"] if parent else ""),
        "    "
    )[:4000]
    
    user_msg = SIMPLE_FOREX_USER_TEMPLATE.format(
        today=today,
        asset=asset,
        metrics_tbl=_format_metrics(parent["metrics"] if parent else None),
        parent_code=parent_code or "(root seed – no parent)",
        hof=_format_hof(store, k=3, metric=metric),
        k=3,
        metric=metric,
    )
    
    return [
        {"role": "system", "content": SIMPLE_FOREX_SYSTEM_MSG},
        {"role": "user", "content": user_msg},
    ]

