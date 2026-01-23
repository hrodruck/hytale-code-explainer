# application.py
from typing import List, Dict

from src.domain.ports import LLMCompleter, CodeRetriever
from src.domain.prompts import system_prompt
from src.config import MAX_HISTORY_MESSAGES, HISTORY_KEEP_LAST


def get_initial_history() -> List[Dict]:
    return [{"role": "system", "content": system_prompt}]


def get_retrieval_top_k(history: List[Dict]) -> int:
    """Return the number of retrieval results to use based on conversation stage"""
    return 50 if len(history) == 1 else 10


def complete_conversation_turn(
    current_history: List[Dict],
    query: str,
    context: str,
    completer: LLMCompleter,
) -> tuple[str, List[Dict], bool]:
    user_content = f"Relevant code context:\n{context}\n\nQuestion: {query}"

    provisional_history = current_history + [{"role": "user", "content": user_content}]

    response = completer.complete(provisional_history)

    new_history = provisional_history + [{"role": "assistant", "content": response}]

    trimmed = len(new_history) > MAX_HISTORY_MESSAGES
    if trimmed:
        new_history = [new_history[0]] + new_history[-HISTORY_KEEP_LAST:]

    return response, new_history, trimmed

def process_conversation_turn(
    current_history: List[Dict],
    query: str,
    retriever: CodeRetriever,
    completer: LLMCompleter,
) -> tuple[str, List[Dict], bool]:
    top_k = get_retrieval_top_k(current_history)
    context = retriever.retrieve(query, top_k=top_k)
    return complete_conversation_turn(current_history, query, context, completer)
