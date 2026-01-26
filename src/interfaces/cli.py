# cli.py
import sys
import traceback

from src.adapters.retrieval import QdrantCodeRetriever
from src.adapters.llm import GrokCompleter
from src.application.application import get_initial_history, process_conversation_turn

# Concrete gateway instances (wiring / dependency injection)
code_retriever = QdrantCodeRetriever()
llm_completer = GrokCompleter()

def main():
    print("Hytale Modding Assistant CLI")
    print("Type your question about the Hytale server codebase.")
    print("Commands: /clear (reset conversation), /exit (quit)")
    print("Multi-line input: type your message, press Enter for new lines,")
    print("then Ctrl+D (Unix/macOS) or Ctrl+Z+Enter (Windows) on a new line to send.")
    print("-" * 50)

    history = get_initial_history()

    while True:
        print("\nYou: ", end="", flush=True)

        try:
            lines = sys.stdin.readlines()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)

        query_raw = "".join(lines)
        query_stripped = query_raw.strip()

        if not query_stripped:
            continue

        if query_stripped.lower() == "/exit":
            print("Goodbye!")
            break

        if query_stripped.lower() == "/clear":
            history = get_initial_history()
            print("Conversation history cleared.")
            continue

        query = query_raw

        print("Processing...", end="", flush=True)

        try:
            response, history, trimmed = process_conversation_turn(
                history,
                query,
                code_retriever,
                llm_completer,
            )
        except Exception:
            print("\nSorry, something went wrong.")
            traceback.print_exc()
            continue
        else:
            print(" done.")

        if trimmed:
            print("Conversation history was trimmed to prevent token overflow.")

        print("\nAssistant:")
        print(response)
        print("-" * 50)


if __name__ == "__main__":
    main()