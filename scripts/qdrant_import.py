from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)
client.recover_snapshot(
    collection_name="hytale_codebase",
    location="file:///snapshots/hytale_codebase-1863882730595526-2026-02-18-13-57-13.snapshot"
)