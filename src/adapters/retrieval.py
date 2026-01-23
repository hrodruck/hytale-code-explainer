import re
from typing import List

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

from src.config import EMBEDDING_MODEL_NAME, QDRANT_URL, COLLECTION_NAME

emb_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
emb_client = QdrantClient(url=QDRANT_URL)


class QdrantCodeRetriever:
    def retrieve(self, query: str, top_k: int = 30) -> str:
        query_vec = emb_model.encode([query], normalize_embeddings=True)[0]
        
        response = emb_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vec.tolist(),
            limit=3 * top_k,
        )
        
        hits = response.points
        
        raw_results = []
        for hit in hits:
            payload = hit.payload
            lines_info = payload["metadata"].get("lines", "full file")
            raw_results.append({
                "score": hit.score,
                "path": payload['path'],
                "lines_info": lines_info,
                "content": payload['content'],
                "metadata": payload.get("metadata", {}),
                "class_names": payload.get("class_names", []),
                "method_names": payload.get("method_names", []),
            })

        keywords = self._extract_keywords(query)
        if keywords:
            for res in raw_results:
                boost = 0.0
                text = (res["path"].lower() + " " + 
                        " ".join(res["class_names"]).lower() + " " + 
                        " ".join(res["method_names"]).lower() + " " + 
                        res["content"].lower())
                
                for kw in keywords:
                    if kw.lower() in text:
                        boost += 0.15
                
                res["boosted_score"] = res["score"] + boost * 0.3
            
            raw_results.sort(key=lambda x: x.get("boosted_score", x["score"]), reverse=True)
        else:
            raw_results.sort(key=lambda x: x["score"], reverse=True)

        results = []
        for res in raw_results[:top_k]:
            lines_info = res["lines_info"]
            header = (
                f"File: {res['path']} (lines {lines_info})\n"
                f"Relevance: {res['score']:.3f}"
            )
            if "boosted_score" in res and abs(res["boosted_score"] - res["score"]) > 0.01:
                header += f"  (boosted: {res['boosted_score']:.3f})"
            
            results.append(
                f"{header}\n"
                f"Classes: {', '.join(res['class_names']) if res['class_names'] else '—'}\n"
                f"Methods: {', '.join(res['method_names']) if res['method_names'] else '—'}\n"
                f"```\n{res['content']}\n```"
            )
        
        return "\n\n".join(results) if results else "No relevant code found."

    @staticmethod
    def _extract_keywords(query: str) -> List[str]:
        candidates = re.findall(r'[A-Z][a-zA-Z0-9_]+|[a-z]+[A-Z][a-zA-Z0-9_]*|[a-z_]+', query)
        words = re.findall(r'\b\w{4,}\b', query.lower())
        return list(set(candidates + words))