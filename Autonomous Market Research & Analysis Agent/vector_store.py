import json
import math
import os
import threading
from config import VECTOR_STORE_FILE
from logger import logger

_LOCK = threading.Lock()

def load_store():
    if not os.path.exists(VECTOR_STORE_FILE):
        return []
    try:
        with open(VECTOR_STORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        logger.exception("Could not load vector store")
        return []

def save_store(data):
    os.makedirs(os.path.dirname(VECTOR_STORE_FILE), exist_ok=True)
    temp = VECTOR_STORE_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp, VECTOR_STORE_FILE)

def cosine_similarity(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    ma = math.sqrt(sum(x * x for x in a))
    mb = math.sqrt(sum(y * y for y in b))
    if ma == 0 or mb == 0:
        return 0.0
    return dot / (ma * mb)

def add_documents(items):
    with _LOCK:
        store = load_store()
        store.extend(items)
        save_store(store)

def clear_store():
    with _LOCK:
        save_store([])

def search(query_embedding, top_k=3):
    store = load_store()
    scored = []
    for item in store:
        score = cosine_similarity(query_embedding, item.get("embedding", []))
        scored.append({
            "id": item.get("id"),
            "text": item.get("text", ""),
            "source": item.get("source", ""),
            "metadata": item.get("metadata", {}),
            "score": round(score, 6),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

def document_summary():
    store = load_store()
    grouped = {}
    for item in store:
        name = item.get("source", "unknown")
        grouped[name] = grouped.get(name, 0) + 1
    return {"chunks": len(store), "documents": grouped}
