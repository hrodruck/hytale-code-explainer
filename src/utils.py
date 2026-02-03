import datetime
import json
import sys
from typing import Any, Dict, List
import hashlib

def split_into_messages(text: str, limit: int = 1950) -> List[str]:
    """Split long responses into multiple Discord messages (preserves code blocks where possible)"""
    if len(text) <= limit:
        return [text]
    
    chunks = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > limit and current:
            chunks.append(current)
            current = line
        else:
            current += line
    if current:
        chunks.append(current)
    return chunks


def log_usage_metric(event: str, details: Dict[str, Any], filename: str = "usage_metrics.jsonl"):
    """
    Append a structured metric event as a JSON line to the metrics file.
    This is now in utils so it can potentially be reused by other adapters/modules in the future.
    """
    metric = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "event": event,
        **details,
    }
    try:
        with open(filename, "a", encoding="utf-8") as f:
            json.dump(metric, f)
            f.write("\n")
    except Exception as exc:
        # Fallback to stderr if file logging fails
        print(f"Failed to write metric to {filename}: {exc}", file=sys.stderr)
        

def anonymize_user_id(user_id: str) -> str:
    """Return a consistent hashed version of the user ID (pseudonymized)."""
    return hashlib.sha256(user_id.encode('utf-8')).hexdigest()