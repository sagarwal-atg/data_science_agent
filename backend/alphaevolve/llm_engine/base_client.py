from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Dict


class LLMClient(ABC):
    """Abstract base class for all LLM backends."""

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kw) -> Any:
        """Return the LLM response for a list of chat ``messages``."""
        raise NotImplementedError
