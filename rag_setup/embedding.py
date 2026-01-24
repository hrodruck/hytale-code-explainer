import json
import re
from pathlib import Path
from tqdm import tqdm
from typing import Dict, List, Set

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import PointStruct


def extract_code_symbols(content: str) -> Dict[str, List[str]]:
    class_names: Set[str] = set()
    method_names: Set[str] = set()

    for match in re.finditer(
        r'(?:public|private|protected|abstract|final)?\s*(?:class|interface|enum|record)\s+([A-Za-z0-9_]+)',
        content,
    ):
        class_names.add(match.group(1))

    method_pattern = (
        r'(?:public|private|protected|static|final|synchronized)?\s*'
        r'(?:[\w<>\[\]]+\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*'
        r'(?:throws\s+[\w, ]+)?\s*{'
    )
    for match in re.finditer(method_pattern, content):
        method_names.add(match.group(1))

    return {
        "class_names": list(class_names),
        "method_names": list(method_names),
    }


CHUNKS_FILE = "code_chunks/chunks.jsonl"
COLLECTION_NAME = "hytale_codebase"
MODEL_NAME = "jinaai/jina-embeddings-v2-base-code"
BATCH_SIZE = 2
QDRANT_URL = "http://localhost:6333"


print(f"Loading chunks from {CHUNKS_FILE}...")
chunks = []
with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            chunks.append(json.loads(line))

print(f"Loaded {len(chunks)} chunks.")

print(f"Loading embedding model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

texts = []
for chunk in chunks:
    metadata = chunk.get("metadata", {})
    lines_info = metadata.get("lines", "full file")
    text = f"File path: {chunk['path']}\nLines: {lines_info}\n\n{chunk['content']}"
    texts.append(text)

print("Computing embeddings...")
embeddings = model.encode(
    texts,
    batch_size=BATCH_SIZE,
    show_progress_bar=True,
    normalize_embeddings=True,
)

dimension = embeddings.shape[1]
print(f"Embeddings shape: {embeddings.shape} (dimension: {dimension})")

print(f"Connecting to Qdrant at {QDRANT_URL}")
client = QdrantClient(url=QDRANT_URL)

print(f"Creating/recreating collection '{COLLECTION_NAME}'")
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
)

print("Upserting vectors to Qdrant...")
batch_size = 100
points = []

for i, (chunk, vector) in tqdm(enumerate(zip(chunks, embeddings)), total=len(chunks)):
    symbols = extract_code_symbols(chunk["content"])

    points.append(
        PointStruct(
            id=i,
            vector=vector.tolist(),
            payload={
                "path": chunk["path"],
                "content": chunk["content"],
                "metadata": chunk.get("metadata", {}),
                "class_names": symbols["class_names"],
                "method_names": symbols["method_names"],
            },
        )
    )

    if len(points) >= batch_size:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        points = []

if points:
    client.upsert(collection_name=COLLECTION_NAME, points=points)

print(f"Done! {len(chunks)} vectors stored in collection '{COLLECTION_NAME}'.")
print("You can now query it in your retrieval script.")