import datetime
import json
import sys
from typing import Any, Dict, List
import hashlib

def split_into_messages(text: str, limit: int = 1950) -> List[str]:
    """Split long responses into multiple Discord messages.
    
    - If the entire response fits in one message, return it whole (preserves original formatting).
    - If too long, parse into text sections and code blocks.
    - Text sections are split line-by-line (like the original function).
    - Code blocks are kept intact when possible and placed in their own dedicated message(s).
    - Very long code blocks are split into multiple dedicated code block messages (repeating the language tag for consistent syntax highlighting).
    This ensures no code block is ever cut in the middle unnecessarily and each code block appears isolated in the chunks.
    """
    if len(text) <= limit:
        return [text]

    # --- Simple Markdown parser (handles ``` fences, including optional language) ---
    def parse_parts(text: str):
        parts = []
        lines = text.splitlines(keepends=True)
        in_code = False
        current_lines = []
        lang = None

        for line in lines:
            stripped = line.strip()
            if in_code:
                if stripped.startswith("```"):
                    # Closing fence
                    content = "".join(current_lines)
                    parts.append({"type": "code", "content": content, "lang": lang})
                    in_code = False
                    current_lines = []
                    lang = None
                else:
                    current_lines.append(line)
            else:
                if stripped.startswith("```"):
                    # Opening fence
                    if current_lines:  # Flush any pending text
                        parts.append({"type": "text", "content": "".join(current_lines)})
                        current_lines = []
                    lang = stripped[3:].strip()  # Empty string if no language
                    in_code = True
                else:
                    current_lines.append(line)

        # Flush whatever is left
        if current_lines:
            if in_code:
                parts.append({"type": "code", "content": "".join(current_lines), "lang": lang})
            else:
                parts.append({"type": "text", "content": "".join(current_lines)})
        return parts

    # --- Parse into alternating text/code parts ---
    parts = parse_parts(text)
    chunks: List[str] = []

    for part in parts:
        if part["type"] == "text":
            # Split text exactly like the original function (line-by-line, never mid-line)
            current = ""
            for line in part["content"].splitlines(keepends=True):
                if len(current) + len(line) > limit and current:
                    chunks.append(current)
                    current = line
                else:
                    current += line
            if current:
                chunks.append(current)

        else:  # code block
            lang = part["lang"]
            content = part["content"]

            header = f"```{lang}\n" if lang else "```\n"
            footer = "```\n"
            full_block = header + content + footer

            # If the whole code block fits, send it in its own dedicated message
            if len(full_block) <= limit:
                chunks.append(full_block)
                continue

            # Otherwise, split the code block into multiple dedicated messages
            code_lines = content.splitlines(keepends=True)
            current_lines: List[str] = []

            for line in code_lines:
                # Check if adding this line would exceed the limit for a full fenced block
                test = "".join(current_lines) + line
                if len(header + test + footer) > limit:
                    # Flush the current part
                    if current_lines:
                        chunk_content = "".join(current_lines)
                        chunks.append(header + chunk_content + footer)
                        current_lines = []
                    # Start new part with the current line
                    current_lines.append(line)
                else:
                    current_lines.append(line)

            # Flush the final part
            if current_lines:
                chunk_content = "".join(current_lines)
                chunks.append(header + chunk_content + footer)

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