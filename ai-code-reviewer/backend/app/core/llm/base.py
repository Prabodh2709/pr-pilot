from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ReviewResult:
    category: str   # security | architecture | performance | style | bug
    severity: str   # critical | warning | info
    line: int
    comment: str
    suggestion: str | None = None


class LLMProvider(ABC):
    @abstractmethod
    async def review(self, prompt: str) -> list[ReviewResult]:
        """Send a prompt and return a list of ReviewResult objects."""
