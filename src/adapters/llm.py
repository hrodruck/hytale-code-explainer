import os
from typing import List, Dict, Optional
from openai import OpenAI
from openai import AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError, APIError, APIStatusError

from src.config import (
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    FALLBACK_LLM_BASE_URL,
    FALLBACK_LLM_MODEL,
    FALLBACK_LLM_TEMPERATURE,
)

from src.domain.ports import LLMCompleter


class OpenAICompatibleCompleter:
    """Generic adapter for any OpenAI-compatible endpoint (xAI/Grok, OpenAI, etc.)"""
    def __init__(
        self,
        base_url: Optional[str],
        api_key: str,
        model: str,
        temperature: float = 0.2,
    ):
        if not api_key:
            raise ValueError("API key is required for LLM completer.")

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model
        self.temperature = temperature

    def complete(self, messages: List[Dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content


class FailoverLLMCompleter:
    """Tries primary first, falls back to secondary (if available) on transient/server errors"""
    def __init__(self, primary: LLMCompleter, secondary: Optional[LLMCompleter] = None):
        self.primary = primary
        self.secondary = secondary

    def complete(self, messages: List[Dict]) -> str:
        try:
            return self.primary.complete(messages)
        except AuthenticationError:
            # Auth failure = misconfiguration → fail fast, no fallback
            print("Primary LLM authentication failed (check the API key environment variable).")
            raise
        except (RateLimitError, APITimeoutError, APIConnectionError):
            # Classic transient errors
            if self.secondary:
                print("Primary LLM transient error – falling back to secondary.")
                return self.secondary.complete(messages)
            raise
        except APIStatusError as exc:
            # 5xx server errors
            if exc.status_code >= 500 or "capacity" in str(exc).lower():
                if self.secondary:
                    print(f"Primary LLM server error ({exc.status_code}) – falling back.")
                    return self.secondary.complete(messages)
                raise
            else:
                # 4xx = client error, don't fallback
                raise
        except APIError as exc:
            # Other API errors – check message for capacity
            if "capacity" in str(exc).lower():
                if self.secondary:
                    print("Primary LLM at capacity – falling back.")
                    return self.secondary.complete(messages)
                raise
            raise
        except Exception as exc:
            # Unexpected → don't silently fallback
            print(f"Unexpected primary LLM error: {exc}")
            raise

def get_llm_completer() -> LLMCompleter:
    """Factory that configures and returns the failover-wrapped LLM completer.
    Raises clear errors on misconfiguration."""
    grok_key = os.getenv("GROK_API_KEY")
    if not grok_key:
        raise ValueError("GROK_API_KEY environment variable is required for primary LLM.")

    primary = OpenAICompatibleCompleter(
        base_url=LLM_BASE_URL,
        api_key=grok_key,
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
    )

    fallback: Optional[OpenAICompatibleCompleter] = None
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            fallback = OpenAICompatibleCompleter(
                base_url=FALLBACK_LLM_BASE_URL,
                api_key=openai_key,
                model=FALLBACK_LLM_MODEL,
                temperature=FALLBACK_LLM_TEMPERATURE,
            )
            print("Fallback LLM (OpenAI) configured and ready.")
        except Exception as e:
            print(f"Warning: Failed to configure fallback LLM: {e}")
            # Continue without fallback rather than crashing startup

    return FailoverLLMCompleter(primary=primary, secondary=fallback)