import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.environ.get("OLLAMA_LLM_MODEL", "llama3.2:3b")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "uploads")
VECTOR_STORE_FILE = os.path.join(BASE_DIR, "data", "vector_store.json")
LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")

TOP_K = 3
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MAX_UPLOAD_MB = 25

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
