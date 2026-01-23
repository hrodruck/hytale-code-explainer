from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)
client.recover_snapshot(
    collection_name="hytale_codebase",
    location="file:///snapshots/hytale_codebase-5188174292604745-2026-01-18-21-08-20.snapshot"  
)