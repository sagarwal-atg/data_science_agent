"""Service for finding critical events in a time series."""

import os
import re
from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class CriticalEvent(BaseModel):
    """A critical event with timestamp and summary."""
    
    timestamp: str  # ISO format timestamp
    date: str  # YYYY-MM-DD format
    summary: str
    title: Optional[str] = None
    citations: list[dict] = []


class CriticalEventsResult(BaseModel):
    """Result containing list of critical events."""
    
    ticker: str
    start_date: str
    end_date: str
    events: list[CriticalEvent]
    run_id: str


async def search_critical_events(
    ticker: str,
    start_date: str,
    end_date: str,
    num_events: int = 10,
) -> CriticalEventsResult:
    """
    Search for critical events in a time series using Parallel API.
    
    Args:
        ticker: Stock ticker or series name
        start_date: Start date of the period (YYYY-MM-DD)
        end_date: End date of the period (YYYY-MM-DD)
        num_events: Number of critical events to find (default: 10)
        
    Returns:
        CriticalEventsResult with list of events
    """
    from parallel import Parallel
    from parallel.types import TaskSpecParam
    
    api_key = os.getenv("PARALLEL_API_KEY")
    if not api_key:
        raise ValueError("PARALLEL_API_KEY environment variable not set")
    
    client = Parallel(api_key=api_key)
    
    # Construct search query for critical events
    search_input = f"""
Find the top {num_events} most important and critical events, news, or developments related to {ticker} between {start_date} and {end_date}.

Focus on:
- Major price movements or volatility spikes
- Significant news announcements
- Earnings reports or financial updates
- Regulatory changes or policy decisions
- Market events that significantly impacted {ticker}
- Product launches or major business developments

For each event, provide:
1. The exact date (YYYY-MM-DD format)
2. A concise title/summary (1-2 sentences)
3. A brief explanation of why it was critical

Return the events in chronological order from earliest to latest.
"""
    
    # Create task run with structured output schema
    output_schema = """Return a JSON object with a single key "events" containing an array of event objects.

Each event object must have these exact fields:
- "date": string in YYYY-MM-DD format (e.g., "2024-03-15")
- "title": string with a brief 5-10 word title describing the event
- "summary": string with 1-2 sentences explaining what happened and why it was critical

Return EXACTLY this JSON structure, no additional text:
{
  "events": [
    {
      "date": "YYYY-MM-DD",
      "title": "Brief event title",
      "summary": "1-2 sentence explanation."
    }
  ]
}"""
    
    task_run = client.task_run.create(
        input=search_input,
        task_spec=TaskSpecParam(
            output_schema=output_schema
        ),
        processor="base"
    )
    
    # Wait for result (with timeout)
    run_result = client.task_run.result(task_run.run_id, api_timeout=120)
    
    # Parse output
    output = run_result.output
    
    events = []
    
    # Try to parse structured output
    if hasattr(output, "events") and output.events:
        for event_data in output.events:
            date_str = getattr(event_data, "date", None)
            if not date_str:
                continue
                
            # Ensure date is in YYYY-MM-DD format
            try:
                # Parse and reformat to ensure consistency
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                date_str = parsed_date.strftime("%Y-%m-%d")
                timestamp = f"{date_str}T00:00:00Z"
            except ValueError:
                # Try other date formats
                try:
                    parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    date_str = parsed_date.strftime("%Y-%m-%d")
                    timestamp = f"{date_str}T00:00:00Z"
                except:
                    timestamp = f"{date_str}T00:00:00Z"
            
            title = getattr(event_data, "title", None)
            summary = getattr(event_data, "summary", "") or getattr(event_data, "description", "")
            
            # Get citations if available
            citations = []
            if hasattr(event_data, "citations") and event_data.citations:
                for cit in event_data.citations:
                    citations.append({
                        "url": getattr(cit, "url", ""),
                        "title": getattr(cit, "title", None),
                    })
            
            events.append(CriticalEvent(
                timestamp=timestamp,
                date=date_str,
                summary=summary,
                title=title,
                citations=citations,
            ))
    
    # If structured parsing failed, try to extract from content
    if not events and hasattr(output, "content"):
        content = str(output.content)
        
        # Try to parse as JSON first
        try:
            import json
            # Try to find JSON in the content
            json_match = re.search(r'\{[\s\S]*"events"[\s\S]*\}', content)
            if json_match:
                json_data = json.loads(json_match.group())
                if "events" in json_data:
                    for event_data in json_data["events"]:
                        date_str = event_data.get("date", "")
                        if date_str:
                            events.append(CriticalEvent(
                                timestamp=f"{date_str}T00:00:00Z",
                                date=date_str,
                                summary=event_data.get("summary", ""),
                                title=event_data.get("title"),
                                citations=[],
                            ))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # If JSON parsing failed, try to extract from markdown/text
        if not events:
            # Look for patterns like "1.", "**1.", "#### **1." or numbered events
            # Split by numbered items or headers
            event_blocks = re.split(r'(?:^|\n)(?:\#{1,4}\s*)?(?:\*{1,2})?(\d+)[.\)]\s*', content)
            
            for i in range(1, len(event_blocks), 2):  # Skip first empty split, process pairs
                if i + 1 >= len(event_blocks):
                    break
                    
                block = event_blocks[i + 1]
                
                # Extract date from block
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', block)
                if not date_match:
                    # Try other date formats like "November 20, 2023"
                    month_date_match = re.search(
                        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
                        block, re.IGNORECASE
                    )
                    if month_date_match:
                        month_names = {
                            'january': '01', 'february': '02', 'march': '03', 'april': '04',
                            'may': '05', 'june': '06', 'july': '07', 'august': '08',
                            'september': '09', 'october': '10', 'november': '11', 'december': '12'
                        }
                        month = month_names[month_date_match.group(1).lower()]
                        day = month_date_match.group(2).zfill(2)
                        year = month_date_match.group(3)
                        date_str = f"{year}-{month}-{day}"
                    else:
                        continue
                else:
                    date_str = date_match.group(1)
                
                # Extract title - usually the first line or bold text
                title_match = re.search(r'\*{1,2}([^*]+)\*{1,2}', block[:200])
                title = title_match.group(1).strip() if title_match else None
                
                # Clean up title - remove "Date:", "Title:", etc.
                if title:
                    title = re.sub(r'^(Date|Title|Event|Summary):\s*', '', title, flags=re.IGNORECASE)
                
                # Extract summary - look for text after "Summary:" or just take the main content
                summary_match = re.search(r'[Ss]ummary[:\s]+(.+?)(?:\n\n|$)', block, re.DOTALL)
                if summary_match:
                    summary = summary_match.group(1).strip()
                else:
                    # Take first substantial paragraph
                    paragraphs = [p.strip() for p in block.split('\n\n') if p.strip()]
                    summary = paragraphs[0] if paragraphs else block[:300]
                
                # Clean up summary - remove markdown formatting
                summary = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', summary)
                summary = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', summary)  # Remove links
                summary = summary.strip()[:500]  # Limit length
                
                if date_str and summary:
                    events.append(CriticalEvent(
                        timestamp=f"{date_str}T00:00:00Z",
                        date=date_str,
                        summary=summary,
                        title=title,
                        citations=[],
                    ))
    
    # Don't format summaries with LLM - keep them concise and plain
    # The UI already formats them appropriately
    formatted_events = events
    
    # Sort by date
    formatted_events.sort(key=lambda e: e.date)
    
    # Limit to requested number
    formatted_events = formatted_events[:num_events]
    
    return CriticalEventsResult(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        events=formatted_events,
        run_id=task_run.run_id,
    )
