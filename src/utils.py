# utils.py
from typing import List

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