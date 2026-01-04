from __future__ import annotations
import json
from typing import Any

import boto3
from botocore.config import Config

from .llm_client import LLMClient


class BedrockClient(LLMClient):
    def __init__(
        self,
        region: str = "us-east-1",
        model_id: str = "anthropic.claude-3-sonnet-20240307",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.region = region
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(retries={"max_attempts": 3}),
        )

    def generate(
        self, prompt: str, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if "claude" in self.model_id.lower():
            return self._generate_claude(prompt, schema)
        elif "titan" in self.model_id.lower():
            return self._generate_titan(prompt, schema)
        else:
            return self._generate_claude(prompt, schema)

    def _generate_claude(
        self, prompt: str, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages,
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
        )

        response_body = json.loads(response["body"].read())
        text = response_body.get("content", [{}])[0].get("text", "")

        return self._extract_json(text, schema)

    def _generate_titan(
        self, prompt: str, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": self.max_tokens,
                "temperature": self.temperature,
                "stopSequences": [],
            },
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
        )

        response_body = json.loads(response["body"].read())
        text = response_body.get("results", [{}])[0].get("outputText", "")

        return self._extract_json(text, schema)

    def _extract_json(
        self, text: str, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        import re

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
            self.client.list_foundation_models()
            return True
        except Exception:
            return False
