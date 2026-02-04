# config.py
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "hytale_codebase"
EMBEDDING_MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"

RETRIEVAL_FIRST_TOP_K = 30
RETRIEVAL_USUAL_TOP_K = 30

LLM_BASE_URL = "https://api.x.ai/v1"
LLM_MODEL = "grok-4-1-fast-reasoning"
LLM_TEMPERATURE = 0.2
FALLBACK_LLM_BASE_URL = "https://api.openai.com/v1"
FALLBACK_LLM_MODEL = "gpt-4o-mini"  
FALLBACK_LLM_TEMPERATURE = 0.2

DISCORD_COMMAND_PREFIX = "!"
MAX_HISTORY_MESSAGES = 12
HISTORY_KEEP_LAST = 8
MESSAGE_CHUNK_LIMIT = 1800

METRICS_FILE = "data/usage_metrics.jsonl"
