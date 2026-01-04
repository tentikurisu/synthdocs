from __future__ import annotations
import json
import re
from typing import Any

import requests

from .llm_client import LLMClient


class OllamaClient(LLMClient):
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5:1.5b-instruct",
        timeout_s: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def generate(
        self, prompt: str, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        r = requests.post(url, json=payload, timeout=self.timeout_s)
        if not r.ok:
            try:
                detail = r.json()
            except Exception:
                detail = {"error": r.text[:500]}
            raise requests.HTTPError(
                f"Ollama request failed: {r.status_code} (model={self.model!r}) :: {detail}",
                response=r,
            )

        text = (r.json().get("response") or "").strip()
        return self._extract_json(text, schema)

    def _extract_json(
        self, text: str, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not text:
            return {}

        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        return {}

    def health_check(self) -> bool:
        try:
            url = f"{self.base_url}/api/tags"
            r = requests.get(url, timeout=5)
            return r.ok
        except Exception:
            return False


def ollama_generate(base_url: str, model: str, prompt: str, timeout_s: int = 60) -> str:
    client = OllamaClient(base_url=base_url, model=model, timeout_s=timeout_s)
    result = client.generate(prompt)
    return json.dumps(result)
