from __future__ import annotations
from typing import Any

from .llm_client import LLMClient
from .ollama_client import OllamaClient
from .bedrock_client import BedrockClient


def create_llm_client(
    provider: str = "ollama",
    ollama_base_url: str = "http://127.0.0.1:11434",
    ollama_model: str = "qwen2.5:1.5b-instruct",
    ollama_timeout: int = 60,
    bedrock_region: str = "us-east-1",
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240307",
    bedrock_temperature: float = 0.7,
) -> LLMClient:
    if provider == "bedrock":
        return BedrockClient(
            region=bedrock_region,
            model_id=bedrock_model_id,
            temperature=bedrock_temperature,
        )
    else:
        return OllamaClient(
            base_url=ollama_base_url,
            model=ollama_model,
            timeout_s=ollama_timeout,
        )
