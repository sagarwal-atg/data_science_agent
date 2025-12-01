"""Thin wrapper around the OpenAI GPT-5.1 Responses API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Dict, Optional

import backoff
import openai

from alphaevolve.config import settings

from .base_client import LLMClient


@dataclass
class ResponseMessage:
    """Wrapper to make Responses API output compatible with Chat Completions format."""
    content: str
    role: str = "assistant"
    
    def __getitem__(self, key):
        """Allow dict-like access for backwards compatibility."""
        return getattr(self, key)


class OpenAIClient(LLMClient):
    """Concrete :class:`LLMClient` using OpenAI's GPT-5.1 Responses API."""

    def __init__(self) -> None:
        openai.api_key = settings.openai_api_key
        self._client = openai.OpenAI(api_key=settings.openai_api_key)

    @backoff.on_exception(backoff.expo, openai.OpenAIError, max_tries=5, jitter=backoff.full_jitter)
    async def chat(self, messages: List[Dict[str, str]], **kw) -> ResponseMessage:
        """Call OpenAI GPT-5.1 Responses API returning a message-like object."""
        
        # Convert messages to Responses API input format
        system_msg = ""
        user_msg = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                system_msg = content
            elif role == "user":
                user_msg = content
        
        # Build combined input
        if system_msg:
            full_input = f"""## System Instructions:
{system_msg}

## User Request:
{user_msg}

Important: Respond ONLY with valid JSON. No markdown code blocks, no explanations."""
        else:
            full_input = user_msg
        
        # Determine reasoning effort based on task complexity
        reasoning_effort = kw.pop("reasoning_effort", "high")
        verbosity = kw.pop("verbosity", "medium")
        
        # Use sync client since we're wrapping in async anyway
        import asyncio
        loop = asyncio.get_event_loop()
        
        response = await loop.run_in_executor(
            None,
            lambda: self._client.responses.create(
                model=settings.openai_model,
                input=full_input,
                reasoning={"effort": reasoning_effort},
                text={"verbosity": verbosity},
            )
        )
        
        return ResponseMessage(content=response.output_text, role="assistant")


# Backwards compatible helper
client = OpenAIClient()


async def chat(messages: List[Dict[str, str]], **kw) -> Any:  # pragma: no cover - thin wrapper
    """Module level helper calling :class:`OpenAIClient.chat`."""
    return await client.chat(messages, **kw)
