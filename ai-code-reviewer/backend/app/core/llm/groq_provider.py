from __future__ import annotations

import json

from groq import AsyncGroq

from app.config import settings
from app.core.llm.base import LLMProvider, ReviewResult

_MODEL = "llama-3.3-70b-versatile"


class GroqProvider(LLMProvider):
    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.groq_api_key)

    async def review(self, prompt: str) -> list[ReviewResult]:
        response = await self._client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        issues = data.get("issues", [])
        return [
            ReviewResult(
                category=i.get("category", "style"),
                severity=i.get("severity", "info"),
                line=int(i.get("line", 1)),
                comment=i.get("comment", ""),
                suggestion=i.get("suggestion"),
            )
            for i in issues
        ]
