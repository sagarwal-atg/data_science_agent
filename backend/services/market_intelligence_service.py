"""Market Intelligence Service - Comprehensive financial news and analysis.

This service combines:
- Factor Discovery: Identifies what influences asset prices
- Enhanced Search: Multi-query, deep research, URL extraction
- News Aggregation: Real-time news about factors
- Sentiment Analysis: Overall market sentiment

Designed for building Market Maps and understanding asset drivers.
"""

import os
import asyncio
from typing import Optional
from datetime import datetime, timedelta

from pydantic import BaseModel

from .enhanced_search_service import (
    multi_query_search,
    extract_from_urls,
    deep_research,
    search_with_structured_output,
    comprehensive_asset_search,
    NewsArticle,
)
from .factor_discovery_service import (
    get_factor_profile,
    analyze_asset_factors,
    compare_asset_factors,
    Factor,
    AssetFactorProfile,
    FactorAnalysisResult,
)


# ============================================================================
# Market Intelligence Models
# ============================================================================

class SentimentIndicator(BaseModel):
    """Sentiment indicator for a factor or asset."""
    name: str
    sentiment: str  # very_bullish, bullish, neutral, bearish, very_bearish
    score: float  # -1 to 1
    confidence: float  # 0 to 1
    recent_change: Optional[str] = None  # improving, stable, declining


class MarketMapNode(BaseModel):
    """A node in the market map graph."""
    id: str
    label: str
    type: str  # asset, factor, indicator
    category: Optional[str] = None
    sentiment: Optional[SentimentIndicator] = None
    importance: float = 0.5  # 0-1, for node sizing


class MarketMapEdge(BaseModel):
    """An edge (relationship) in the market map graph."""
    source: str  # Node ID
    target: str  # Node ID
    relationship: str  # influences, correlates, leads, lags
    strength: float  # 0-1
    direction: str  # positive, negative, complex


class MarketMap(BaseModel):
    """Complete market map for an asset."""
    asset: str
    asset_type: str
    nodes: list[MarketMapNode]
    edges: list[MarketMapEdge]
    generated_at: str


class EconomicEvent(BaseModel):
    """An upcoming economic event."""
    date: str
    time: Optional[str] = None
    name: str
    country: str
    importance: str  # high, medium, low
    previous_value: Optional[str] = None
    forecast_value: Optional[str] = None
    affected_assets: list[str] = []


class MarketIntelligenceReport(BaseModel):
    """Complete market intelligence report for an asset."""
    asset: str
    asset_type: str
    generated_at: str
    
    # Market Map
    market_map: MarketMap
    
    # Factor Analysis
    factor_analysis: FactorAnalysisResult
    
    # Overall Assessment
    overall_sentiment: SentimentIndicator
    short_term_outlook: str  # 1-2 sentences
    medium_term_outlook: str  # 1-2 sentences
    
    # Key News
    top_news: list[NewsArticle]
    
    # Risks and Opportunities
    key_risks: list[str]
    key_opportunities: list[str]
    
    # Upcoming Events
    upcoming_events: list[EconomicEvent]


class AssetComparisonReport(BaseModel):
    """Comparison report for multiple assets."""
    assets: list[str]
    generated_at: str
    shared_factors: list[str]
    divergent_factors: dict[str, list[str]]
    correlation_notes: list[str]
    market_maps: dict[str, MarketMap]


# ============================================================================
# Market Intelligence Functions
# ============================================================================

async def build_market_map(
    asset: str,
    include_sentiment: bool = True,
) -> MarketMap:
    """
    Build a market map graph for an asset.
    
    The market map visualizes:
    - The asset at the center
    - Factors that influence it
    - Relationships between factors
    - Current sentiment for each factor
    
    Args:
        asset: The asset to map
        include_sentiment: Whether to include sentiment analysis
        
    Returns:
        MarketMap with nodes and edges for visualization
    """
    print(f"  [Market Map] Getting factor profile for {asset}...")
    # Get factor profile
    profile = await get_factor_profile(asset)
    print(f"  [Market Map] Got {len(profile.factors)} factors")
    
    nodes = []
    edges = []
    
    # Add central asset node
    nodes.append(MarketMapNode(
        id=f"asset_{asset.replace('/', '_')}",
        label=asset,
        type="asset",
        importance=1.0,
    ))
    
    # Get sentiment for all factors in one batch call if requested
    factor_sentiments = {}
    if include_sentiment and profile.factors:
        try:
            factor_names = [f.name for f in profile.factors[:8]]  # Limit to 8 factors
            print(f"  [Market Map] Analyzing sentiment for {len(factor_names)} factors...")
            sentiment_result = await search_with_structured_output(
                query=f"""Analyze the current market sentiment for each of these factors affecting {asset}:
{chr(10).join(f'- {name}' for name in factor_names)}

For each factor, determine if it is currently bullish, bearish, or neutral for {asset}, and give a sentiment score from -1 (very bearish) to 1 (very bullish).""",
                output_schema={
                    "type": "object",
                    "properties": {
                        "factors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "sentiment": {"type": "string", "enum": ["very_bullish", "bullish", "neutral", "bearish", "very_bearish"]},
                                    "score": {"type": "number"}
                                },
                                "required": ["name", "sentiment", "score"]
                            }
                        }
                    },
                    "required": ["factors"]
                },
                processor="base",
                timeout=60,
            )
            
            if sentiment_result.get("factors"):
                for f in sentiment_result["factors"]:
                    factor_sentiments[f.get("name", "")] = SentimentIndicator(
                        name=f.get("name", ""),
                        sentiment=f.get("sentiment", "neutral"),
                        score=f.get("score", 0.0),
                        confidence=0.7,
                    )
            print(f"  [Market Map] ✓ Got sentiment for {len(factor_sentiments)} factors")
        except Exception as e:
            print(f"  [Market Map] ⚠ Sentiment analysis failed: {e}")
    
    # Add factor nodes
    for factor in profile.factors:
        sentiment = factor_sentiments.get(factor.name)
        if not sentiment:
            sentiment = SentimentIndicator(
                name=factor.name,
                sentiment="neutral",
                score=0.0,
                confidence=0.3,
            )
        
        importance = 0.8 if factor.influence_strength == "high" else 0.6 if factor.influence_strength == "medium" else 0.4
        
        nodes.append(MarketMapNode(
            id=f"factor_{factor.id}",
            label=factor.name,
            type="factor",
            category=factor.category,
            sentiment=sentiment,
            importance=importance,
        ))
        
        # Add edge from factor to asset
        direction = factor.influence_direction
        edges.append(MarketMapEdge(
            source=f"factor_{factor.id}",
            target=f"asset_{asset.replace('/', '_')}",
            relationship="influences",
            strength=importance,
            direction=direction,
        ))
    
    return MarketMap(
        asset=asset,
        asset_type=profile.asset_type,
        nodes=nodes,
        edges=edges,
        generated_at=datetime.now().isoformat(),
    )


async def get_upcoming_events(
    asset: str,
    days_ahead: int = 14,
) -> list[EconomicEvent]:
    """
    Get upcoming economic events that could affect an asset.
    
    Uses search to find upcoming events from economic calendars.
    """
    query = f"""
Find upcoming economic events in the next {days_ahead} days that could significantly impact {asset}.

Focus on:
- Central bank meetings and rate decisions
- Key economic data releases (GDP, CPI, employment)
- Political events
- Earnings releases (if applicable)

For each event provide:
- Date
- Event name
- Country/region
- Importance level
- Previous and forecast values if available
"""
    
    result = await search_with_structured_output(
        query=query,
        output_schema={
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "time": {"type": "string"},
                            "name": {"type": "string"},
                            "country": {"type": "string"},
                            "importance": {"type": "string", "enum": ["high", "medium", "low"]},
                            "previous_value": {"type": "string"},
                            "forecast_value": {"type": "string"},
                        },
                        "required": ["date", "name", "country", "importance"]
                    }
                }
            },
            "required": ["events"]
        },
    )
    
    events = []
    for e in result.get("events", []):
        events.append(EconomicEvent(
            date=e.get("date", ""),
            time=e.get("time"),
            name=e.get("name", ""),
            country=e.get("country", ""),
            importance=e.get("importance", "medium"),
            previous_value=e.get("previous_value"),
            forecast_value=e.get("forecast_value"),
            affected_assets=[asset],
        ))
    
    return events


async def generate_market_intelligence_report(
    asset: str,
    include_deep_research: bool = False,
    progress_tracker = None,
) -> MarketIntelligenceReport:
    """
    Generate comprehensive market intelligence report for an asset.
    
    This is the main function that combines everything:
    1. Builds market map with factors
    2. Analyzes each factor with news
    3. Gets upcoming events
    4. Generates overall outlook
    
    Args:
        asset: The asset to analyze
        include_deep_research: Use ultra processor for deep research (slower)
        
    Returns:
        Complete MarketIntelligenceReport
    """
    print(f"[STEP 1/4] Building market map for {asset}...")
    if progress_tracker:
        await progress_tracker.start_step(1, "Building Market Map", "Identifying factors that influence the asset...")
    
    # Build market map first (includes sentiment)
    market_map = await build_market_map(asset, include_sentiment=True)
    print(f"[STEP 1/4] ✓ Market map complete - {len(market_map.nodes)} nodes, {len(market_map.edges)} edges")
    
    if progress_tracker:
        await progress_tracker.complete_step(1)
    
    print(f"[STEP 2/4] Analyzing factors with news for {asset}...")
    if progress_tracker:
        await progress_tracker.start_step(2, "Searching News", "Finding recent news for each factor...")
    
    # Get factor analysis (with limited news to keep it fast)
    factor_analysis = await analyze_asset_factors(asset, include_news=True, max_factors_for_news=2)
    print(f"[STEP 2/4] ✓ Factor analysis complete - {len(factor_analysis.profile.factors)} factors, {len(factor_analysis.factor_news)} news bundles")
    
    if progress_tracker:
        await progress_tracker.complete_step(2)
    
    print(f"[STEP 3/4] Calculating sentiment...")
    if progress_tracker:
        await progress_tracker.start_step(3, "Analyzing Sentiment", "Determining bullish/bearish signals...")
    
    # Get overall sentiment from market map
    sentiment_scores = []
    for node in market_map.nodes:
        if node.sentiment:
            sentiment_scores.append(node.sentiment.score)
    
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
    
    if avg_sentiment > 0.4:
        overall_label = "bullish"
    elif avg_sentiment > 0.15:
        overall_label = "slightly_bullish"
    elif avg_sentiment < -0.4:
        overall_label = "bearish"
    elif avg_sentiment < -0.15:
        overall_label = "slightly_bearish"
    else:
        overall_label = "neutral"
    
    overall_sentiment = SentimentIndicator(
        name=f"{asset} Overall",
        sentiment=overall_label,
        score=avg_sentiment,
        confidence=0.7 if len(sentiment_scores) >= 3 else 0.5,
    )
    print(f"[STEP 3/4] ✓ Sentiment: {overall_label} (score: {avg_sentiment:.2f})")
    
    if progress_tracker:
        await progress_tracker.complete_step(3)
    
    print(f"[STEP 4/4] Generating outlook and finding events...")
    if progress_tracker:
        await progress_tracker.start_step(4, "Generating Outlook", "Creating insights and finding events...")
    # Generate outlook and get events in one combined call for efficiency
    factor_names = [f.name for f in factor_analysis.profile.factors[:5]]
    insights = factor_analysis.key_insights[:3] if factor_analysis.key_insights else ["No recent insights"]
    
    outlook_result = await search_with_structured_output(
        query=f"""
Provide market analysis for {asset}:

Current sentiment: {overall_label} (score: {avg_sentiment:.2f})
Key factors: {', '.join(factor_names)}
Recent insights: {', '.join(insights)}

Provide:
1. Short-term outlook (next 1-2 weeks) - 1-2 sentences
2. Medium-term outlook (next 1-3 months) - 1-2 sentences
3. Key risks (3-4 bullet points)
4. Key opportunities (3-4 bullet points)
5. Upcoming important events in the next 2 weeks that could affect {asset}
""",
        output_schema={
            "type": "object",
            "properties": {
                "short_term_outlook": {"type": "string"},
                "medium_term_outlook": {"type": "string"},
                "key_risks": {"type": "array", "items": {"type": "string"}},
                "key_opportunities": {"type": "array", "items": {"type": "string"}},
                "upcoming_events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "name": {"type": "string"},
                            "country": {"type": "string"},
                            "importance": {"type": "string"}
                        },
                        "required": ["date", "name"]
                    }
                }
            },
            "required": ["short_term_outlook", "medium_term_outlook", "key_risks", "key_opportunities"]
        },
        timeout=90,
    )
    print(f"[STEP 4/4] ✓ Outlook generated")
    
    if progress_tracker:
        await progress_tracker.complete_step(4)
        await progress_tracker.complete()
    
    # Collect top news from factor analysis
    top_news = []
    for factor_news in factor_analysis.factor_news:
        top_news.extend(factor_news.articles[:3])
    top_news = top_news[:10]
    
    # Parse upcoming events
    upcoming_events = []
    for e in outlook_result.get("upcoming_events", []):
        upcoming_events.append(EconomicEvent(
            date=e.get("date", "TBD"),
            name=e.get("name", "Unknown Event"),
            country=e.get("country", "Global"),
            importance=e.get("importance", "medium"),
            affected_assets=[asset],
        ))
    
    return MarketIntelligenceReport(
        asset=asset,
        asset_type=market_map.asset_type,
        generated_at=datetime.now().isoformat(),
        market_map=market_map,
        factor_analysis=factor_analysis,
        overall_sentiment=overall_sentiment,
        short_term_outlook=outlook_result.get("short_term_outlook", "Outlook analysis pending."),
        medium_term_outlook=outlook_result.get("medium_term_outlook", "Outlook analysis pending."),
        top_news=top_news,
        key_risks=outlook_result.get("key_risks", []),
        key_opportunities=outlook_result.get("key_opportunities", []),
        upcoming_events=upcoming_events,
    )


async def generate_comparison_report(
    assets: list[str],
) -> AssetComparisonReport:
    """
    Generate comparison report for multiple assets.
    
    Shows shared factors, divergences, and correlations.
    """
    # Get market maps for all assets
    market_maps = await asyncio.gather(*[
        build_market_map(asset, include_sentiment=True)
        for asset in assets
    ])
    
    # Compare factors
    comparison = await compare_asset_factors(assets)
    
    # Generate correlation notes
    correlation_query = f"""
Analyze the correlation and relationship between these assets: {', '.join(assets)}

Consider:
- Historical price correlation
- Shared driving factors
- When they move together vs diverge
- Pair trading opportunities

Provide 3-5 key observations about their relationship.
"""
    
    correlation_result = await search_with_structured_output(
        query=correlation_query,
        output_schema={
            "type": "object",
            "properties": {
                "correlation_notes": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["correlation_notes"]
        },
    )
    
    return AssetComparisonReport(
        assets=assets,
        generated_at=datetime.now().isoformat(),
        shared_factors=comparison["shared_factors"],
        divergent_factors=comparison["unique_factors"],
        correlation_notes=correlation_result.get("correlation_notes", []),
        market_maps={m.asset: m for m in market_maps},
    )


async def search_specific_factor(
    asset: str,
    factor_query: str,
    deep: bool = False,
) -> dict:
    """
    Search for specific information about a factor affecting an asset.
    
    Use this for drill-down queries like:
    - "What is the Fed likely to do in the next meeting?"
    - "How are corporate hedging flows affecting EUR/USD?"
    
    Args:
        asset: The asset being analyzed
        factor_query: Specific question about a factor
        deep: Use ultra processor for comprehensive research
        
    Returns:
        Detailed search result
    """
    if deep:
        result = await deep_research(
            topic=factor_query,
            context=f"This relates to understanding what influences {asset}.",
        )
        return result.model_dump()
    else:
        result = await comprehensive_asset_search(
            asset=asset,
            query=factor_query,
            include_deep_research=False,
        )
        return result


async def extract_from_source(
    urls: list[str],
    extraction_objective: str,
) -> list[dict]:
    """
    Extract specific information from financial sources.
    
    Great for:
    - Extracting key data from Fed minutes
    - Parsing earnings reports
    - Getting specific figures from economic releases
    
    Args:
        urls: URLs to extract from
        extraction_objective: What to extract
        
    Returns:
        Extracted content from each URL
    """
    results = await extract_from_urls(
        urls=urls,
        objective=extraction_objective,
        include_excerpts=True,
    )
    
    return [r.model_dump() for r in results]

