import re
import json
from pathlib import Path

MAX_CHUNK_CHARS = 12000  # ~7.5k tokens, safe margin
OVERLAP_LINES = 400

def split_large_file(path: str, content: str):
    lines = content.splitlines()
    chunks = []
    start_line = 0
    while start_line < len(lines):
        end_line = start_line + 800
        while end_line < len(lines) and len("\n".join(lines[start_line:end_line+1])) < MAX_CHUNK_CHARS:
            end_line += 50
        chunk_text = "\n".join(lines[start_line:end_line])
        chunks.append({
            "path": path,
            "content": chunk_text,
            "start_line": start_line + 1,
            "end_line": end_line,
        })
        start_line = max(0, end_line - OVERLAP_LINES)
    return chunks

def parse_repomix_regex(xml_path: str, output_path: str = "code_chunks/chunks.jsonl"):
    content = Path(xml_path).read_text(encoding="utf-8")
    pattern = r'<file path="([^"]+)">(.*?)</file>'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    Path("code_chunks").mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for i, match in enumerate(matches):
            path = match.group(1)
            file_content = match.group(2).strip()
            if not file_content:
                continue
                
            metadata = {"path": path, "type": "full_file"}
            
            if len(file_content) <= MAX_CHUNK_CHARS:
                chunk = {
                    "id": i,
                    "path": path,
                    "content": file_content,
                    "metadata": metadata
                }
                f.write(json.dumps(chunk) + "\n")
            else:
                print(f"[SPLITTING] {path} ({len(file_content)} chars)")
                for j, sub in enumerate(split_large_file(path, file_content)):
                    sub_metadata = {
                        "path": path,
                        "lines": f"{sub['start_line']}–{sub['end_line']}",
                        "type": "file_fragment"
                    }
                    chunk = {
                        "id": f"{i}_{j}",
                        "path": path,
                        "content": sub["content"],
                        "metadata": sub_metadata
                    }
                    f.write(json.dumps(chunk) + "\n")


if __name__ == '__main__':
    parse_repomix_regex(Path("data/repomix-output.xml"))