"""Enhanced Parallel API search service with advanced capabilities.

This service leverages Parallel's powerful search APIs:
- beta.search(): Multi-query parallel search with rich results
- beta.extract(): Deep content extraction from specific URLs
- task_run with "ultra" processor: For comprehensive research reports
- Structured JSON schemas: For typed, reliable output
"""

import os
import asyncio
from typing import Optional
from datetime import datetime

from pydantic import BaseModel


# ============================================================================
# Models
# ============================================================================

class SearchResultItem(BaseModel):
    """A single search result item."""
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    source: Optional[str] = None


class MultiSearchResult(BaseModel):
    """Result from multi-query search."""
    query: str
    results: list[SearchResultItem]
    total_results: int


class ExtractedContent(BaseModel):
    """Content extracted from a URL."""
    url: str
    title: Optional[str] = None
    content: str
    excerpts: list[str] = []
    extraction_successful: bool = True


class DeepResearchResult(BaseModel):
    """Result from deep research using ultra processor."""
    run_id: str
    topic: str
    summary: str
    key_findings: list[str]
    sources: list[dict]
    confidence: str


class NewsArticle(BaseModel):
    """A news article with metadata."""
    title: str
    url: str
    summary: str
    published_date: Optional[str] = None
    source: str
    sentiment: Optional[str] = None  # bullish, bearish, neutral
    relevance_score: Optional[float] = None
    related_factors: list[str] = []


class FactorNewsBundle(BaseModel):
    """News bundle for a specific factor."""
    factor_name: str
    factor_category: str
    articles: list[NewsArticle]
    overall_sentiment: str
    sentiment_score: float  # -1 to 1
    key_takeaways: list[str]


# ============================================================================
# Enhanced Search Functions
# ============================================================================

def get_parallel_client():
    """Get Parallel client with API key."""
    from parallel import Parallel
    
    api_key = os.getenv("PARALLEL_API_KEY")
    if not api_key:
        raise ValueError("PARALLEL_API_KEY environment variable not set")
    return Parallel(api_key=api_key)


async def multi_query_search(
    queries: list[str],
    objective: str,
    max_results_per_query: int = 10,
    max_chars_per_result: int = 5000,
) -> list[MultiSearchResult]:
    """
    Perform multi-query parallel search using Parallel's beta.search API.
    
    Args:
        queries: List of search queries to run in parallel
        objective: Overall objective/context for the search
        max_results_per_query: Max results per query
        max_chars_per_result: Max characters per result snippet
        
    Returns:
        List of MultiSearchResult for each query
    """
    client = get_parallel_client()
    
    print(f"    [Search API] Searching with {len(queries)} queries...")
    
    # Use the beta.search API
    search_response = client.beta.search(
        objective=objective,
        search_queries=queries,
        max_results=max_results_per_query,
        max_chars_per_result=max_chars_per_result,
    )
    
    results = []
    all_items = []
    
    # Parse results from the search response
    if hasattr(search_response, 'results') and search_response.results:
        print(f"    [Search API] Got {len(search_response.results)} results")
        for result in search_response.results:
            # Extract excerpts as the snippet
            excerpts = getattr(result, 'excerpts', [])
            snippet = excerpts[0] if excerpts else ""
            
            all_items.append(SearchResultItem(
                title=getattr(result, 'title', 'Untitled'),
                url=getattr(result, 'url', ''),
                snippet=snippet[:max_chars_per_result] if snippet else "",
                published_date=getattr(result, 'publish_date', None),
                source=getattr(result, 'url', 'Web').split('/')[2] if getattr(result, 'url', '') else 'Web',
            ))
    else:
        print(f"    [Search API] No results found")
    
    results.append(MultiSearchResult(
        query=objective,
        results=all_items,
        total_results=len(all_items),
    ))
    
    return results


async def extract_from_urls(
    urls: list[str],
    objective: str,
    include_excerpts: bool = True,
    full_content: bool = False,
) -> list[ExtractedContent]:
    """
    Extract specific information from URLs using Parallel's beta.extract API.
    
    Args:
        urls: List of URLs to extract from (max 10)
        objective: What to extract from the pages
        include_excerpts: Include relevant excerpts
        full_content: Include full page content (slower)
        
    Returns:
        List of ExtractedContent for each URL
    """
    client = get_parallel_client()
    
    print(f"    [Extract API] Extracting from {len(urls)} URLs...")
    
    # Use the beta.extract API
    extract_response = client.beta.extract(
        urls=urls[:10],  # Max 10 URLs per request
        objective=objective,
        excerpts=include_excerpts,
        full_content=full_content,
    )
    
    results = []
    
    if hasattr(extract_response, 'results') and extract_response.results:
        print(f"    [Extract API] Got {len(extract_response.results)} extractions")
        for result in extract_response.results:
            excerpts = getattr(result, 'excerpts', [])
            results.append(ExtractedContent(
                url=getattr(result, 'url', ''),
                title=getattr(result, 'title', None),
                content=getattr(result, 'full_content', '') or (excerpts[0] if excerpts else ''),
                excerpts=excerpts if isinstance(excerpts, list) else [],
                extraction_successful=True,
            ))
    else:
        print(f"    [Extract API] No extractions returned")
    
    # Check for errors
    if hasattr(extract_response, 'errors') and extract_response.errors:
        for error in extract_response.errors:
            print(f"    [Extract API] Error: {error}")
    
    return results


async def deep_research(
    topic: str,
    context: str = "",
    timeout: int = 600,
) -> DeepResearchResult:
    """
    Perform deep research using the ultra processor.
    
    Uses Parallel's Deep Research capability for comprehensive,
    multi-step web exploration with analyst-grade intelligence.
    
    This is ideal for:
    - Comprehensive market analysis
    - Understanding complex factors affecting assets
    - Building detailed factor profiles
    
    Args:
        topic: The research topic
        context: Additional context for the research
        timeout: API timeout in seconds (ultra can take up to 45 minutes)
        
    Returns:
        DeepResearchResult with comprehensive findings
    """
    from parallel.types import TaskSpecParam
    
    client = get_parallel_client()
    
    # Build the research input
    research_input = f"{topic}"
    if context:
        research_input += f"\n\nAdditional context: {context}"
    
    print(f"    [Deep Research] Starting ultra processor research...")
    
    # Use ultra processor for deep research with structured output
    task_run = client.task_run.create(
        input=research_input,
        task_spec=TaskSpecParam(
            output_schema={
                "type": "json",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Executive summary of findings (2-3 paragraphs)"
                        },
                        "key_findings": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of key findings with specific data points"
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Overall confidence in the findings"
                        }
                    },
                    "required": ["summary", "key_findings", "confidence"],
                    "additionalProperties": False
                }
            }
        ),
        processor="ultra"  # Use ultra for deep research
    )
    
    print(f"    [Deep Research] Task created: {task_run.run_id}, waiting for result...")
    
    # Wait for result (ultra takes longer - up to 45 minutes)
    run_result = client.task_run.result(task_run.run_id, api_timeout=timeout)
    
    print(f"    [Deep Research] ✓ Research complete")
    
    output = run_result.output
    
    # Extract sources from basis if available
    sources = []
    if hasattr(output, 'basis') and output.basis:
        for basis_item in output.basis:
            if hasattr(basis_item, 'citations') and basis_item.citations:
                for citation in basis_item.citations:
                    sources.append({
                        "title": getattr(citation, 'title', None),
                        "url": getattr(citation, 'url', ''),
                        "relevance": getattr(basis_item, 'reasoning', '')[:100] if hasattr(basis_item, 'reasoning') else ''
                    })
    
    return DeepResearchResult(
        run_id=task_run.run_id,
        topic=topic,
        summary=getattr(output, 'summary', '') or (output.content if hasattr(output, 'content') else str(output)),
        key_findings=getattr(output, 'key_findings', []),
        sources=sources[:20],  # Limit to 20 sources
        confidence=getattr(output, 'confidence', 'medium'),
    )


async def search_with_structured_output(
    query: str,
    output_schema: dict,
    processor: str = "base",
    timeout: int = 120,
) -> dict:
    """
    Search with a specific structured JSON output schema.
    
    This ensures reliable, typed output from the search.
    
    Args:
        query: The search query/prompt
        output_schema: JSON schema for the output
        processor: "base" for fast, "ultra" for comprehensive
        timeout: API timeout
        
    Returns:
        Parsed output matching the schema
    """
    from parallel.types import TaskSpecParam
    
    client = get_parallel_client()
    
    print(f"    [Parallel API] Creating task with processor={processor}...")
    task_run = client.task_run.create(
        input=query,
        task_spec=TaskSpecParam(
            output_schema={
                "type": "json",
                "json_schema": output_schema
            }
        ),
        processor=processor
    )
    print(f"    [Parallel API] Task created: {task_run.run_id}, waiting for result...")
    
    run_result = client.task_run.result(task_run.run_id, api_timeout=timeout)
    print(f"    [Parallel API] ✓ Task complete: {task_run.run_id}")
    
    # Convert output to dict
    output = run_result.output
    if hasattr(output, '__dict__'):
        return output.__dict__
    return {"content": str(output)}


async def search_factor_news(
    asset: str,
    factor_name: str,
    factor_keywords: list[str],
    days_back: int = 7,
) -> FactorNewsBundle:
    """
    Search for news related to a specific factor affecting an asset.
    
    Uses Parallel's beta.search API for comprehensive coverage.
    
    Args:
        asset: The asset being analyzed (e.g., "EUR/USD")
        factor_name: Name of the factor (e.g., "Federal Reserve Policy")
        factor_keywords: Keywords to search for
        days_back: How many days back to search
        
    Returns:
        FactorNewsBundle with articles and sentiment
    """
    client = get_parallel_client()
    
    # Build search queries from keywords
    queries = [
        f"{keyword} {asset} news latest" for keyword in factor_keywords[:3]
    ] + [
        f"{factor_name} latest news {asset}",
    ]
    
    objective = f"""
    Find recent news and developments about {factor_name} and its impact on {asset}.
    Focus on:
    - Policy changes or announcements
    - Economic data releases
    - Market reactions and analysis
    - Expert opinions and forecasts
    
    Prioritize news from the last {days_back} days.
    """
    
    print(f"    [Factor News] Searching news for {factor_name}...")
    
    # Use the beta.search API directly
    try:
        search_response = client.beta.search(
            objective=objective,
            search_queries=queries,
            max_results=8,
            max_chars_per_result=2000,
        )
        
        # Convert to news articles
        articles = []
        if hasattr(search_response, 'results') and search_response.results:
            print(f"    [Factor News] Got {len(search_response.results)} results for {factor_name}")
            for result in search_response.results:
                excerpts = getattr(result, 'excerpts', [])
                snippet = excerpts[0] if excerpts else ""
                url = getattr(result, 'url', '')
                
                articles.append(NewsArticle(
                    title=getattr(result, 'title', 'Untitled'),
                    url=url,
                    summary=snippet[:300] if snippet else "",
                    published_date=getattr(result, 'publish_date', None),
                    source=url.split('/')[2] if url and '/' in url else 'Web',
                    related_factors=[factor_name],
                ))
        else:
            print(f"    [Factor News] No results for {factor_name}")
    except Exception as e:
        print(f"    [Factor News] Search failed for {factor_name}: {e}")
        articles = []
    
    # Get sentiment analysis using structured output
    if articles:
        sentiment_query = f"""
        Analyze the overall sentiment of these news items regarding {factor_name} and its impact on {asset}:
        
        {chr(10).join([f'- {a.title}: {a.summary[:100]}' for a in articles[:10]])}
        
        Determine if the news is bullish, bearish, or neutral for {asset}.
        """
        
        try:
            sentiment_result = await search_with_structured_output(
                query=sentiment_query,
                output_schema={
                    "type": "object",
                    "properties": {
                        "sentiment": {
                            "type": "string",
                            "enum": ["very_bullish", "bullish", "neutral", "bearish", "very_bearish"]
                        },
                        "sentiment_score": {
                            "type": "number",
                            "description": "Score from -1 (very bearish) to 1 (very bullish)"
                        },
                        "key_takeaways": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "3-5 key takeaways from the news"
                        }
                    },
                    "required": ["sentiment", "sentiment_score", "key_takeaways"]
                }
            )
            
            overall_sentiment = sentiment_result.get('sentiment', 'neutral')
            sentiment_score = sentiment_result.get('sentiment_score', 0.0)
            key_takeaways = sentiment_result.get('key_takeaways', [])
        except Exception as e:
            print(f"    [Factor News] Sentiment analysis failed: {e}")
            overall_sentiment = 'neutral'
            sentiment_score = 0.0
            key_takeaways = []
    else:
        overall_sentiment = 'neutral'
        sentiment_score = 0.0
        key_takeaways = []
    
    return FactorNewsBundle(
        factor_name=factor_name,
        factor_category="general",
        articles=articles,
        overall_sentiment=overall_sentiment,
        sentiment_score=sentiment_score,
        key_takeaways=key_takeaways,
    )


async def comprehensive_asset_search(
    asset: str,
    query: str,
    include_deep_research: bool = False,
) -> dict:
    """
    Comprehensive search about an asset combining multiple search strategies.
    
    This combines:
    1. Fast multi-query search for recent news
    2. Optional deep research for comprehensive analysis
    
    Args:
        asset: Asset to research
        query: Specific question or focus
        include_deep_research: Whether to include ultra processor research
        
    Returns:
        Dict with search results, and optionally deep research
    """
    results = {
        "asset": asset,
        "query": query,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Fast multi-query search
    queries = [
        f"{asset} latest news",
        f"{asset} price analysis",
        f"{asset} market outlook",
        query,
    ]
    
    search_results = await multi_query_search(
        queries=queries,
        objective=f"Find comprehensive information about {asset}: {query}",
        max_results_per_query=8,
    )
    
    results["quick_search"] = [r.model_dump() for r in search_results]
    
    # Optional deep research
    if include_deep_research:
        deep_result = await deep_research(
            topic=f"Comprehensive analysis of {asset}: {query}",
            context=f"Focus on factors that influence {asset}, recent developments, and outlook.",
        )
        results["deep_research"] = deep_result.model_dump()
    
    return results

