from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
INDEX_DIR = BASE_DIR / "data" / "indexes"
MAX_UPLOAD_MB = int(os.getenv("CODEMIND_MAX_UPLOAD_MB", "20"))
MAX_FILES = int(os.getenv("CODEMIND_MAX_FILES", "250"))
TOP_K = int(os.getenv("CODEMIND_TOP_K", "6"))
# Local Ollama model. No API key or paid AI service is used.
OLLAMA_URL = os.getenv("CODEMIND_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
LLM_MODEL = os.getenv("CODEMIND_LLM_MODEL", "qwen2.5-coder:3b")
OLLAMA_TIMEOUT = int(os.getenv("CODEMIND_OLLAMA_TIMEOUT", "180"))
SUPPORTED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".md", ".txt", ".json", ".yaml", ".yml", ".css", ".html"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
