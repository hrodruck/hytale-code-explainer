# ports.py
from typing import Protocol
from typing import List, Dict

class LLMCompleter(Protocol):
    def complete(self, messages: List[Dict]) -> str: ...

class CodeRetriever(Protocol):
    def retrieve(self, query: str, top_k: int = 20) -> str: ...