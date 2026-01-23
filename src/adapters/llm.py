# llm.py
import os
from openai import OpenAI

from src.config import LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE


class GrokCompleter:
    def __init__(self):
        self.client = OpenAI(
            base_url=LLM_BASE_URL,
            api_key=os.getenv("GROK_API_KEY")
        )
        self.model = LLM_MODEL
        self.temperature = LLM_TEMPERATURE

    def complete(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content