"""Parallel API search service for time series event explanation."""

import os
from typing import Optional

from pydantic import BaseModel
from .text_formatter import format_text_with_llm


class Citation(BaseModel):
    """Citation from search results."""
    
    title: Optional[str] = None
    url: str
    excerpts: list[str] = []


class SearchBasis(BaseModel):
    """Basis for search output."""
    
    field: str
    citations: list[Citation]
    reasoning: str
    confidence: str = ""


class SearchResult(BaseModel):
    """Search result from Parallel API."""
    
    run_id: str
    status: str
    content: str
    basis: list[SearchBasis]


def _format_time_series_summary(
    timestamps: Optional[list[str]],
    values: Optional[list[float]],
    currency: Optional[str] = None,
) -> str:
    """
    Format time series data into a readable summary for the search context.
    
    Includes start/end values, min/max, percentage change, and key data points.
    """
    if not timestamps or not values or len(timestamps) == 0:
        return ""
    
    unit = f" {currency}" if currency else ""
    
    start_val = values[0]
    end_val = values[-1]
    min_val = min(values)
    max_val = max(values)
    min_idx = values.index(min_val)
    max_idx = values.index(max_val)
    
    # Calculate change
    abs_change = end_val - start_val
    pct_change = ((end_val - start_val) / start_val * 100) if start_val != 0 else 0
    
    summary_lines = [
        f"- Starting Value ({timestamps[0][:10]}): {start_val:,.2f}{unit}",
        f"- Ending Value ({timestamps[-1][:10]}): {end_val:,.2f}{unit}",
        f"- Absolute Change: {abs_change:+,.2f}{unit}",
        f"- Percentage Change: {pct_change:+.2f}%",
        f"- Period Minimum: {min_val:,.2f}{unit} on {timestamps[min_idx][:10]}",
        f"- Period Maximum: {max_val:,.2f}{unit} on {timestamps[max_idx][:10]}",
    ]
    
    # Add key intermediate data points (sample ~5 evenly spaced)
    if len(values) > 5:
        step = len(values) // 5
        sample_points = []
        for i in range(0, len(values), step):
            if i > 0 and i < len(values) - 1:  # Skip first and last (already shown)
                sample_points.append(f"  {timestamps[i][:10]}: {values[i]:,.2f}{unit}")
        if sample_points:
            summary_lines.append("- Key Data Points:")
            summary_lines.extend(sample_points[:5])  # Limit to 5 points
    
    return "\n".join(summary_lines)


async def search_time_series_event(
    ticker: str,
    query: str,
    start_date: str,
    end_date: str,
    change_description: Optional[str] = None,
    timestamps: Optional[list[str]] = None,
    values: Optional[list[float]] = None,
    currency: Optional[str] = None,
) -> SearchResult:
    """
    Search for explanation of time series movement using Parallel API.
    
    Args:
        ticker: Stock ticker or series name
        query: User's question about the movement
        start_date: Start date of the period (YYYY-MM-DD)
        end_date: End date of the period (YYYY-MM-DD)
        change_description: Optional description of price change
        timestamps: Optional list of timestamps for the selected range
        values: Optional list of values for the selected range
        currency: Optional currency/unit label
        
    Returns:
        SearchResult with explanation and citations
    """
    from parallel import Parallel
    from parallel.types import TaskSpecParam
    
    api_key = os.getenv("PARALLEL_API_KEY")
    if not api_key:
        raise ValueError("PARALLEL_API_KEY environment variable not set")
    
    client = Parallel(api_key=api_key)
    
    # Build time series summary if data is provided
    ts_summary = _format_time_series_summary(timestamps, values, currency)
    
    # Construct contextual search query
    search_input = f"""
{query}

Context:
- Asset/Series: {ticker}
- Time Period: {start_date} to {end_date}
{f'- Observed Change: {change_description}' if change_description else ''}
{f'''
Time Series Data for Selected Period:
{ts_summary}
''' if ts_summary else ''}
Please search for news, events, economic factors, or market conditions that could explain what happened to {ticker} during this specific time period ({start_date} to {end_date}). Focus on events that correlate with the observed data movements.
"""
    
    # Create task run
    task_run = client.task_run.create(
        input=search_input,
        task_spec=TaskSpecParam(
            output_schema=f"A detailed explanation of why {ticker} changed during {start_date} to {end_date}, including specific events, news, or market factors."
        ),
        processor="base"
    )
    
    # Wait for result (with timeout)
    run_result = client.task_run.result(task_run.run_id, api_timeout=120)
    
    # Parse output
    output = run_result.output
    
    # Build citations list
    citations = []
    basis_list = []
    
    if hasattr(output, "basis") and output.basis:
        for basis_item in output.basis:
            basis_citations = []
            if hasattr(basis_item, "citations") and basis_item.citations:
                for cit in basis_item.citations:
                    basis_citations.append(Citation(
                        title=getattr(cit, "title", None),
                        url=getattr(cit, "url", ""),
                        excerpts=getattr(cit, "excerpts", []),
                    ))
            
            basis_list.append(SearchBasis(
                field=getattr(basis_item, "field", "output"),
                citations=basis_citations,
                reasoning=getattr(basis_item, "reasoning", ""),
                confidence=getattr(basis_item, "confidence", ""),
            ))
    
    # Format the content with LLM for better readability
    raw_content = output.content if hasattr(output, "content") else str(output)
    formatted_content = await format_text_with_llm(raw_content)
    
    # Also format reasoning sections
    formatted_basis = []
    for basis_item in basis_list:
        formatted_reasoning = await format_text_with_llm(basis_item.reasoning) if basis_item.reasoning else basis_item.reasoning
        formatted_basis.append(SearchBasis(
            field=basis_item.field,
            citations=basis_item.citations,
            reasoning=formatted_reasoning,
            confidence=basis_item.confidence,
        ))
    
    return SearchResult(
        run_id=task_run.run_id,
        status=run_result.run.status,
        content=formatted_content,
        basis=formatted_basis,
    )

