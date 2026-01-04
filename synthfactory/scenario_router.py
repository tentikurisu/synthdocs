from __future__ import annotations
from .scenario_factory import Scenario, ScenarioFactory


def llm_route(
    prompt: str,
    enabled: bool,
    provider: str = "ollama",
    base_url: str = "http://127.0.0.1:11434",
    model: str = "qwen2.5:1.5b-instruct",
    timeout_s: int = 60,
) -> Scenario:
    return ScenarioFactory(enabled=enabled, provider=provider).next(prompt)
