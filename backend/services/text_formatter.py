"""Text formatting service using OpenAI to improve readability."""

import os
from typing import Optional


async def format_text_with_llm(text: str) -> str:
    """
    Format text using OpenAI to add markdown formatting for better readability.
    
    Adds bold, colors, and structure to make the text more digestible.
    
    Args:
        text: Plain text to format
        
    Returns:
        Formatted markdown text
    """
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("WARNING: OPENAI_API_KEY not set, returning original text")
            return text
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""You are a financial analysis text formatter. Format the following text to make it more readable and digestible.

Rules:
1. Use **bold** for key metrics, percentages, dates, and important numbers
2. Use *italics* for emphasis on important concepts
3. Break long paragraphs into shorter, digestible chunks
4. Add bullet points or numbered lists where appropriate
5. Highlight critical information (price changes, percentages, dates) with **bold**
6. Keep the original meaning and facts intact
7. Use markdown formatting only (no HTML)
8. Make key statistics stand out with **bold**

Text to format:
{text}

Return only the formatted markdown text, no explanations:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for cost efficiency
            messages=[
                {"role": "system", "content": "You are a helpful assistant that formats financial analysis text to be more readable using markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        
        formatted_text = response.choices[0].message.content.strip()
        return formatted_text
        
    except Exception as e:
        print(f"WARNING: Failed to format text with LLM: {e}")
        return text  # Return original text if formatting fails
