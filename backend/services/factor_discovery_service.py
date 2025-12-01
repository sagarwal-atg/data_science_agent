"""Factor Discovery Service for identifying what influences asset prices.

This service identifies and tracks factors that influence financial assets:
- Monetary policy (Fed, ECB, etc.)
- Economic indicators
- Corporate activity
- Geopolitical events
- Market sentiment

Uses Parallel's structured JSON output for reliable factor extraction.
"""

import os
import asyncio
from typing import Optional
from datetime import datetime

from pydantic import BaseModel

from .enhanced_search_service import (
    multi_query_search,
    search_with_structured_output,
    deep_research,
    search_factor_news,
    FactorNewsBundle,
)


# ============================================================================
# Factor Models
# ============================================================================

class Factor(BaseModel):
    """A factor that influences an asset."""
    id: str
    name: str
    category: str  # monetary_policy, economic_data, corporate, geopolitical, sentiment, technical
    description: str
    influence_direction: str  # positive, negative, complex
    influence_strength: str  # high, medium, low
    keywords: list[str]
    data_sources: list[str] = []  # Where to get data for this factor
    related_assets: list[str] = []  # Other assets this factor affects


class FactorRelationship(BaseModel):
    """Relationship between factors or between a factor and asset."""
    source: str  # Factor or asset name
    target: str  # Factor or asset name
    relationship_type: str  # influences, correlates_with, leads, lags
    strength: float  # 0-1
    description: str


class AssetFactorProfile(BaseModel):
    """Complete factor profile for an asset."""
    asset: str
    asset_type: str  # forex, stock, crypto, commodity, index
    factors: list[Factor]
    relationships: list[FactorRelationship]
    last_updated: str


class FactorAnalysisResult(BaseModel):
    """Result of analyzing factors for an asset."""
    asset: str
    profile: AssetFactorProfile
    factor_news: list[FactorNewsBundle]
    overall_outlook: str  # bullish, bearish, neutral, mixed
    confidence: str
    key_insights: list[str]


# ============================================================================
# Factor Templates - Pre-defined factor structures for common assets
# ============================================================================

FACTOR_TEMPLATES = {
    "forex": {
        "default": [
            {
                "id": "interest_rate_diff",
                "name": "Interest Rate Differential",
                "category": "monetary_policy",
                "description": "Difference in interest rates between the two currencies",
                "influence_direction": "complex",
                "influence_strength": "high",
                "keywords": ["interest rate", "rate differential", "yield spread", "carry trade"],
            },
            {
                "id": "economic_growth",
                "name": "Relative Economic Growth",
                "category": "economic_data",
                "description": "GDP growth comparison between economies",
                "influence_direction": "positive",
                "influence_strength": "high",
                "keywords": ["GDP", "economic growth", "expansion", "recession"],
            },
            {
                "id": "trade_balance",
                "name": "Trade Balance",
                "category": "economic_data",
                "description": "Net exports vs imports between countries",
                "influence_direction": "positive",
                "influence_strength": "medium",
                "keywords": ["trade deficit", "trade surplus", "exports", "imports", "current account"],
            },
            {
                "id": "risk_sentiment",
                "name": "Risk Sentiment",
                "category": "sentiment",
                "description": "Overall market risk appetite (risk-on vs risk-off)",
                "influence_direction": "complex",
                "influence_strength": "medium",
                "keywords": ["risk appetite", "risk aversion", "VIX", "safe haven", "flight to safety"],
            },
            {
                "id": "central_bank_policy",
                "name": "Central Bank Policy Divergence",
                "category": "monetary_policy",
                "description": "Differences in monetary policy stance between central banks",
                "influence_direction": "complex",
                "influence_strength": "high",
                "keywords": ["hawkish", "dovish", "quantitative easing", "tightening", "forward guidance"],
            },
        ],
        "EURUSD": [
            {
                "id": "fed_policy",
                "name": "Federal Reserve Policy",
                "category": "monetary_policy",
                "description": "US Federal Reserve interest rate decisions and forward guidance",
                "influence_direction": "negative",  # Hawkish Fed = stronger USD = lower EUR/USD
                "influence_strength": "high",
                "keywords": ["Federal Reserve", "FOMC", "Powell", "fed funds rate", "fed rate decision"],
            },
            {
                "id": "ecb_policy",
                "name": "ECB Monetary Policy",
                "category": "monetary_policy",
                "description": "European Central Bank interest rate decisions and policy",
                "influence_direction": "positive",  # Hawkish ECB = stronger EUR = higher EUR/USD
                "influence_strength": "high",
                "keywords": ["ECB", "Lagarde", "eurozone rates", "ECB meeting", "European Central Bank"],
            },
            {
                "id": "us_economic_data",
                "name": "US Economic Data",
                "category": "economic_data",
                "description": "Key US economic indicators (NFP, CPI, GDP)",
                "influence_direction": "negative",  # Strong US = stronger USD = lower EUR/USD
                "influence_strength": "high",
                "keywords": ["US jobs", "NFP", "US CPI", "US GDP", "unemployment rate", "US inflation"],
            },
            {
                "id": "eu_economic_data",
                "name": "Eurozone Economic Data",
                "category": "economic_data",
                "description": "Key Eurozone economic indicators",
                "influence_direction": "positive",
                "influence_strength": "high",
                "keywords": ["eurozone GDP", "EU inflation", "German manufacturing", "EU PMI"],
            },
            {
                "id": "us_eu_trade",
                "name": "US-EU Trade Relations",
                "category": "geopolitical",
                "description": "Trade policies and tariffs between US and EU",
                "influence_direction": "complex",
                "influence_strength": "medium",
                "keywords": ["US EU tariffs", "trade war", "transatlantic trade", "trade agreement"],
            },
            {
                "id": "corporate_hedging",
                "name": "Corporate FX Hedging",
                "category": "corporate",
                "description": "Large corporate hedging flows affecting EUR/USD",
                "influence_direction": "complex",
                "influence_strength": "medium",
                "keywords": ["corporate hedging", "FX hedging", "currency hedging", "multinational exposure"],
            },
        ],
        "USDJPY": [
            {
                "id": "fed_policy",
                "name": "Federal Reserve Policy",
                "category": "monetary_policy",
                "description": "US Federal Reserve interest rate decisions",
                "influence_direction": "positive",  # Hawkish Fed = higher USD/JPY
                "influence_strength": "high",
                "keywords": ["Federal Reserve", "FOMC", "Powell", "fed funds rate"],
            },
            {
                "id": "boj_policy",
                "name": "Bank of Japan Policy",
                "category": "monetary_policy",
                "description": "BOJ yield curve control and policy decisions",
                "influence_direction": "negative",  # Hawkish BOJ = lower USD/JPY
                "influence_strength": "high",
                "keywords": ["BOJ", "Bank of Japan", "Ueda", "yield curve control", "YCC"],
            },
            {
                "id": "japan_intervention",
                "name": "Japanese FX Intervention",
                "category": "monetary_policy",
                "description": "Ministry of Finance currency intervention",
                "influence_direction": "negative",
                "influence_strength": "high",
                "keywords": ["Japan intervention", "yen intervention", "MOF intervention", "yen buying"],
            },
            {
                "id": "risk_sentiment",
                "name": "Global Risk Sentiment",
                "category": "sentiment",
                "description": "Risk-on/risk-off flows (JPY as safe haven)",
                "influence_direction": "positive",  # Risk-on = higher USD/JPY
                "influence_strength": "medium",
                "keywords": ["risk appetite", "safe haven", "VIX", "market fear"],
            },
        ],
    },
    "stock": {
        "default": [
            {
                "id": "earnings",
                "name": "Earnings & Revenue",
                "category": "corporate",
                "description": "Company earnings reports and revenue growth",
                "influence_direction": "positive",
                "influence_strength": "high",
                "keywords": ["earnings", "revenue", "EPS", "quarterly results", "guidance"],
            },
            {
                "id": "sector_trends",
                "name": "Sector Trends",
                "category": "economic_data",
                "description": "Industry-wide trends and developments",
                "influence_direction": "positive",
                "influence_strength": "medium",
                "keywords": ["sector", "industry trend", "market share"],
            },
            {
                "id": "macro_environment",
                "name": "Macro Environment",
                "category": "economic_data",
                "description": "Overall economic conditions affecting business",
                "influence_direction": "positive",
                "influence_strength": "medium",
                "keywords": ["economy", "interest rates", "inflation", "consumer spending"],
            },
            {
                "id": "analyst_sentiment",
                "name": "Analyst Sentiment",
                "category": "sentiment",
                "description": "Wall Street analyst ratings and price targets",
                "influence_direction": "positive",
                "influence_strength": "medium",
                "keywords": ["analyst", "upgrade", "downgrade", "price target", "rating"],
            },
            {
                "id": "institutional_flows",
                "name": "Institutional Flows",
                "category": "corporate",
                "description": "Large institutional buying/selling activity",
                "influence_direction": "positive",
                "influence_strength": "medium",
                "keywords": ["institutional", "13F", "hedge fund", "fund flows"],
            },
        ],
    },
    "crypto": {
        "default": [
            {
                "id": "regulatory",
                "name": "Regulatory Developments",
                "category": "geopolitical",
                "description": "Government and regulatory actions on crypto",
                "influence_direction": "complex",
                "influence_strength": "high",
                "keywords": ["SEC", "regulation", "crypto ban", "Bitcoin ETF", "crypto legislation"],
            },
            {
                "id": "institutional_adoption",
                "name": "Institutional Adoption",
                "category": "corporate",
                "description": "Major institutions entering crypto space",
                "influence_direction": "positive",
                "influence_strength": "high",
                "keywords": ["institutional", "Bitcoin treasury", "crypto fund", "ETF flows"],
            },
            {
                "id": "network_metrics",
                "name": "Network Metrics",
                "category": "technical",
                "description": "On-chain metrics and network activity",
                "influence_direction": "positive",
                "influence_strength": "medium",
                "keywords": ["hash rate", "active addresses", "transaction volume", "on-chain"],
            },
            {
                "id": "macro_liquidity",
                "name": "Macro Liquidity",
                "category": "monetary_policy",
                "description": "Global liquidity conditions affecting risk assets",
                "influence_direction": "positive",
                "influence_strength": "high",
                "keywords": ["liquidity", "Fed balance sheet", "M2", "quantitative easing"],
            },
            {
                "id": "market_sentiment",
                "name": "Market Sentiment",
                "category": "sentiment",
                "description": "Social media and retail sentiment",
                "influence_direction": "positive",
                "influence_strength": "medium",
                "keywords": ["crypto Twitter", "fear greed index", "sentiment", "FOMO"],
            },
        ],
    },
}


# ============================================================================
# Factor Discovery Functions
# ============================================================================

def get_parallel_client():
    """Get Parallel client with API key."""
    from parallel import Parallel
    
    api_key = os.getenv("PARALLEL_API_KEY")
    if not api_key:
        raise ValueError("PARALLEL_API_KEY environment variable not set")
    return Parallel(api_key=api_key)


def detect_asset_type(asset: str) -> str:
    """Detect the type of asset from its symbol."""
    asset_upper = asset.upper().replace("/", "").replace("-", "")
    
    # Check for crypto
    crypto_symbols = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "MATIC", "LINK"]
    if any(crypto in asset_upper for crypto in crypto_symbols):
        return "crypto"
    
    # Check for forex (6-character currency pairs)
    currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]
    if len(asset_upper) == 6:
        if asset_upper[:3] in currencies and asset_upper[3:] in currencies:
            return "forex"
    
    # Check for common indices
    indices = ["SPX", "SPY", "QQQ", "DJI", "IXIC", "VIX"]
    if asset_upper in indices:
        return "index"
    
    # Default to stock
    return "stock"


def get_template_factors(asset: str, asset_type: str) -> list[Factor]:
    """Get pre-defined factors from templates."""
    templates = FACTOR_TEMPLATES.get(asset_type, {})
    
    # Try asset-specific template first
    asset_key = asset.upper().replace("/", "").replace("-", "").replace("=X", "")
    if asset_key in templates:
        factor_dicts = templates[asset_key]
    else:
        factor_dicts = templates.get("default", [])
    
    return [Factor(**f, data_sources=[], related_assets=[]) for f in factor_dicts]


async def discover_factors_with_llm(
    asset: str,
    asset_type: str,
    context: str = "",
) -> list[Factor]:
    """
    Use LLM to discover additional factors for an asset.
    
    This supplements the template factors with dynamically discovered ones.
    """
    prompt = f"""
Identify the most important factors that influence the price of {asset} ({asset_type}).

{f'Additional context: {context}' if context else ''}

Focus on:
1. Macroeconomic factors
2. Industry/sector specific factors
3. Company/asset specific factors
4. Sentiment and technical factors
5. Geopolitical factors

For each factor, provide:
- A unique ID (snake_case)
- Clear name
- Category (monetary_policy, economic_data, corporate, geopolitical, sentiment, technical)
- How it influences the asset (positive, negative, or complex)
- Strength of influence (high, medium, low)
- Keywords to search for news about this factor
"""
    
    result = await search_with_structured_output(
        query=prompt,
        output_schema={
            "type": "object",
            "properties": {
                "factors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "category": {
                                "type": "string",
                                "enum": ["monetary_policy", "economic_data", "corporate", "geopolitical", "sentiment", "technical"]
                            },
                            "description": {"type": "string"},
                            "influence_direction": {
                                "type": "string",
                                "enum": ["positive", "negative", "complex"]
                            },
                            "influence_strength": {
                                "type": "string",
                                "enum": ["high", "medium", "low"]
                            },
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["id", "name", "category", "description", "influence_direction", "influence_strength", "keywords"]
                    }
                }
            },
            "required": ["factors"]
        },
        processor="base",
    )
    
    factors = []
    for f in result.get("factors", []):
        factors.append(Factor(
            id=f.get("id", "unknown"),
            name=f.get("name", "Unknown Factor"),
            category=f.get("category", "economic_data"),
            description=f.get("description", ""),
            influence_direction=f.get("influence_direction", "complex"),
            influence_strength=f.get("influence_strength", "medium"),
            keywords=f.get("keywords", []),
        ))
    
    return factors


async def get_factor_profile(
    asset: str,
    use_templates: bool = True,
    discover_new: bool = True,
) -> AssetFactorProfile:
    """
    Get complete factor profile for an asset.
    
    Combines template factors with LLM-discovered factors.
    
    Args:
        asset: The asset to analyze
        use_templates: Whether to use pre-defined templates
        discover_new: Whether to use LLM to discover additional factors
        
    Returns:
        Complete AssetFactorProfile
    """
    asset_type = detect_asset_type(asset)
    print(f"    [Factor Profile] Asset type: {asset_type}")
    
    factors = []
    
    # Get template factors
    if use_templates:
        template_factors = get_template_factors(asset, asset_type)
        factors.extend(template_factors)
        print(f"    [Factor Profile] Got {len(template_factors)} template factors")
    
    # Discover additional factors with LLM
    if discover_new:
        existing_names = [f.name for f in factors]
        llm_factors = await discover_factors_with_llm(asset, asset_type)
        
        # Add only new factors (avoid duplicates)
        for f in llm_factors:
            if f.name not in existing_names:
                factors.append(f)
    
    # Build relationships (simple version - all factors relate to the asset)
    relationships = []
    for factor in factors:
        relationships.append(FactorRelationship(
            source=factor.name,
            target=asset,
            relationship_type="influences",
            strength=1.0 if factor.influence_strength == "high" else 0.7 if factor.influence_strength == "medium" else 0.4,
            description=f"{factor.name} influences {asset}: {factor.description}",
        ))
    
    return AssetFactorProfile(
        asset=asset,
        asset_type=asset_type,
        factors=factors,
        relationships=relationships,
        last_updated=datetime.now().isoformat(),
    )


async def analyze_asset_factors(
    asset: str,
    include_news: bool = True,
    max_factors_for_news: int = 3,
) -> FactorAnalysisResult:
    """
    Comprehensive factor analysis for an asset.
    
    1. Gets factor profile (template + LLM discovered)
    2. Searches for news about key factors (limited for speed)
    3. Determines overall outlook
    
    Args:
        asset: The asset to analyze
        include_news: Whether to search for factor news
        max_factors_for_news: Max factors to search news for (to limit API calls)
        
    Returns:
        Complete FactorAnalysisResult
    """
    # Get factor profile (without LLM discovery for speed)
    profile = await get_factor_profile(asset, use_templates=True, discover_new=False)
    
    factor_news = []
    overall_outlook = "neutral"
    key_insights = []
    
    # Search news for top factors - do sequentially to avoid overwhelming the API
    if include_news and profile.factors:
        # Take only top high-priority factors
        high_priority = [f for f in profile.factors if f.influence_strength == "high"]
        factors_to_search = high_priority[:max_factors_for_news]
        
        for factor in factors_to_search:
            try:
                news = await search_factor_news(
                    asset=asset,
                    factor_name=factor.name,
                    factor_keywords=factor.keywords[:3],  # Limit keywords
                )
                factor_news.append(news)
                if news.key_takeaways:
                    key_insights.extend(news.key_takeaways[:2])
            except Exception as e:
                print(f"Failed to get news for {factor.name}: {e}")
    
    # Calculate overall outlook
    if factor_news:
        avg_sentiment = sum(n.sentiment_score for n in factor_news) / len(factor_news)
        if avg_sentiment > 0.3:
            overall_outlook = "bullish"
        elif avg_sentiment < -0.3:
            overall_outlook = "bearish"
        elif abs(avg_sentiment) < 0.1:
            overall_outlook = "neutral"
        else:
            overall_outlook = "mixed"
    
    return FactorAnalysisResult(
        asset=asset,
        profile=profile,
        factor_news=factor_news,
        overall_outlook=overall_outlook,
        confidence="high" if len(factor_news) >= 3 else "medium" if factor_news else "low",
        key_insights=key_insights[:10],
    )


async def compare_asset_factors(
    assets: list[str],
) -> dict:
    """
    Compare factors across multiple assets.
    
    Useful for understanding shared drivers and divergences.
    
    Args:
        assets: List of assets to compare
        
    Returns:
        Comparison result with shared and unique factors
    """
    # Get profiles for all assets
    profiles = await asyncio.gather(*[
        get_factor_profile(asset)
        for asset in assets
    ])
    
    # Find shared factors
    all_factor_names = [set(f.name for f in p.factors) for p in profiles]
    shared_factors = set.intersection(*all_factor_names) if all_factor_names else set()
    
    # Build comparison result
    result = {
        "assets": assets,
        "shared_factors": list(shared_factors),
        "profiles": {p.asset: p.model_dump() for p in profiles},
        "unique_factors": {},
    }
    
    for profile in profiles:
        unique = set(f.name for f in profile.factors) - shared_factors
        result["unique_factors"][profile.asset] = list(unique)
    
    return result

