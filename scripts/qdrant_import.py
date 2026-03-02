from qdrant_client import QdrantClient
import os 

COLLECTION = "hytale_codebase"
SNAPSHOT = "file:///snapshots/hytale_codebase-1863882730595526-2026-02-18-13-57-13.snapshot"

client = QdrantClient(url=os.getenv("QDRANT_URL"))

if not client.collection_exists(COLLECTION):
    print(f"🔄 Recovering snapshot into '{COLLECTION}'...")
    client.recover_snapshot(collection_name=COLLECTION, location=SNAPSHOT)
    print("✅ Snapshot recovered!")
else:
    print(f"✅ Collection '{COLLECTION}' already exists — skipping import.")