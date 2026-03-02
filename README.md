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

## Usage

If not self-hosting, you can join [this discord server](https://discord.gg/nNFtFGgC) or add the [dicord bot](https://discord.com/oauth2/authorize?client_id=1354521709969014924&permissions=92160&integration_type=0&scope=bot) to your own server.

## Self-hosting

### Vector Database Snapshot
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
   - Use `qdrant_export.py` to generate a snapshot of the database
   - Change the snaptshot name in qdrant_import.py to match the result frmo the previous step

This prepares the vector database for retrieval.

### RAG assistant

1. Clone the repository
2. Create .env according to .env.example
3. Install docker
3a. (For the CLI that only you access) docker compose run --rm -it app cli
3b. (to replicate the discord bot) docker compose --profile discord up discord-bot

## Testing, Monitorability

For testing (manual and RAGAS) check the eval folder. For monitorability, LLMLite is used.

## Contributing

Feel free to open issues or PRs. The project emphasizes clean separation of concerns—keep delivery mechanisms thin and push rules inward.
Enjoy modding!
