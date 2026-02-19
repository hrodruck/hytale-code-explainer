# Hytale Codebase Assistant

A Clean Architecture-based RAG assistant for answering questions about the **Hytale server codebase**. It retrieves relevant Java code snippets from a vector database, injects them as context, and generates expert responses via LLM.

Supports two interfaces:
- **Discord bot** (`!hy` command to ask questions, `!clear` command to reset conversation)
- **Interactive CLI**

Multi-turn conversations with automatic history trimming are supported in both.

If you are interested, consider joining [this discord server](https://discord.gg/nNFtFGgC) or adding the [dicord bot](https://discord.com/oauth2/authorize?client_id=1354521709969014924&permissions=92160&integration_type=0&scope=bot) to your own server.

## Features

- Instant answers from the official, actual game codebase
- Helps debug common modding issues (cites paths/line numbers with precision)
- Clean Architecture structure for maintainability and extensibility

## Prerequisites

- Python 3.10+
- Local Qdrant instance (http://localhost:6333)
- OpenAI client-compatible API key
- (Optional) Discord bot token
- uv (for dependency management)
- VineFlower (for decompiling the Hytale JAR)
- Repomix (for merging the decompiled codebase into a single file)

## Preparing the Codebase

The assistant requires a processed version of the Hytale server codebase. Start with the official Hytale server JAR:

1. Purchase and download Hytale (available from the official website or launcher).
2. Locate the server JAR file (typically in the Hytale installation directory, e.g., `hytale_server.jar`).
3. Decompile the JAR into a standalone folder using VineFlower:
   - Download VineFlower (a Java decompiler) from its official repository or site.
   - Run: `java -jar vineflower.jar hytale_server.jar output_folder`
4. Use Repomix to merge the decompiled codebase into a single XML file:
   - Install Repomix
   - Run: `repomix pack output_folder repomix-output.xml` (this creates a merged representation suitable for chunking).
5. Process the Repomix output with the provided scripts:
   - Run `chunking.py` on `repomix-output.xml` to generate `code_chunks/chunks.jsonl`.
   - Run `embedding.py` on the chunks to compute embeddings and upsert to Qdrant.
   - (Optional) Use `qdrant_export.py` / `qdrant_import.py` for backups/restores.

This prepares the vector database for retrieval.

## Setup

1. Clone the repository
2. Install uv (if not already: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
3. Sync dependencies: `uv sync`
4. Set environment variables in a `.env` file or your shell:
```bash
XAI_API_KEY=any_onpenai_compatible_api_key #you can edit for a different provider in the configuration file.
DISCORD_TOKEN=your_discord_bot_token  # Only needed for Discord mode
OPENAI_API_KEY=any_onpenai_compatible_api_key #this is for the fallback model, you can also use a different provider
```
5. Ensure Qdrant is running and the codebase collection is indexed (use the scripts in `scripts/` if needed, or check section above)

## Running

Use the unified entry point:

```bash
# Discord bot
uv run main.py discord

# Interactive CLI
uv run main.py cli
```
## Testing

Prepare a dataset of questions and ansers, one question/answer per line in two different files. Then, run

```bash
uv run eval_ragas.py
```

For faithfulness and correctness.

## Contributing

Feel free to open issues or PRs. The project emphasizes clean separation of concerns—keep delivery mechanisms thin and push rules inward.
Enjoy exploring the Hytale codebase!
