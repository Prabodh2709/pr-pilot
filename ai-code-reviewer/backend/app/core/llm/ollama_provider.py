from __future__ import annotations

import json

import httpx

from app.config import settings
from app.core.llm.base import LLMProvider, ReviewResult

_MODEL = "codellama"


class OllamaProvider(LLMProvider):
    async def review(self, prompt: str) -> list[ReviewResult]:
        url = f"{settings.ollama_base_url}/api/generate"
        payload = {
            "model": _MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()

        raw = resp.json().get("response", "{}")
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
