from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    @abstractmethod
    def generate(
        self, prompt: str, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate a response from the LLM given a prompt.

        Args:
            prompt: The prompt to send to the LLM
            schema: Optional JSON schema for the expected response

        Returns:
            Parsed JSON response as a dictionary
        """

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the LLM service is available.

        Returns:
            True if the service is healthy, False otherwise
        """
