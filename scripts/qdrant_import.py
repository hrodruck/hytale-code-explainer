from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)
client.recover_snapshot(
    collection_name="hytale_codebase",
    location="file:///snapshots/hytale_codebase-6604404928335678-2026-02-02-13-26-51.snapshot"
)