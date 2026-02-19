import os
from typing import List, Dict
from openai import OpenAI

from src.config import (
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_ENVIRONMENT_KEY_NAME,
)

from src.domain.ports import LLMCompleter


class OpenAICompatibleCompleter:
    """Generic adapter for OpenAI-compatible vendors."""
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.2,
    ):
        if not api_key:
            raise ValueError("API key is required for LLM completer.")

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.temperature = temperature

    def complete(self, messages: List[Dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content


def get_llm_completer() -> LLMCompleter:
    """Factory returning single completer pointed at LiteLLM Proxy."""
    api_key = os.getenv(LLM_ENVIRONMENT_KEY_NAME)
    if not api_key:
        raise ValueError(f"LLM API key required. Looking for {LLM_ENVIRONMENT_KEY_NAME}")

    return OpenAICompatibleCompleter(
        base_url=LLM_BASE_URL,
        api_key=api_key,
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
    )