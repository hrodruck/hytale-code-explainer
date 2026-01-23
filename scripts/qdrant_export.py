from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)  # Adjust if needed
snapshot = client.create_snapshot(collection_name="hytale_codebase")
print(snapshot)  # Shows name and location, e.g., /qdrant/snapshots/hytale_codebase/...

# Download the snapshot file (via HTTP or copy from storage dir)
# HTTP example:
import requests
snapshot_url = f"http://localhost:6333/collections/hytale_codebase/snapshots/{snapshot.name}"
with open(f"{snapshot.name}", "wb") as f:
    f.write(requests.get(snapshot_url).content)