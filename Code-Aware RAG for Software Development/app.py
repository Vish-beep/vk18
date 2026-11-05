from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from config import INDEX_DIR, MAX_FILES, TOP_K
from core.code_chunker import chunk_repository
from core.embeddings import TfidfEmbedder
from core.github_loader import load_github_repository, load_uploaded_files
from core.rag_engine import RAGEngine
from core.retriever import Retriever
from core.vector_store import VectorStore

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


def _load_local_env() -> None:
    """Load simple KEY=VALUE pairs without making dotenv a runtime requirement."""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_local_env()


def _active_store() -> VectorStore:
    return VectorStore("active")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/manus-routes.json")
def route_manifest():
    return app.response_class(
        (Path(__file__).parent / "manus-routes.json").read_text(encoding="utf-8"),
        mimetype="application/json",
    )


@app.get("/api/status")
def status():
    payload = _active_store().load()
    if not payload:
        return jsonify({"indexed": False, "top_k": TOP_K})
    return jsonify({"indexed": True, "repository": payload.get("repository", {}), "stats": payload.get("stats", {}), "created_at": payload.get("created_at"), "top_k": TOP_K})


@app.post("/api/index/github")
def index_github():
    body = request.get_json(silent=True) or {}
    url = body.get("url", "")
    if not url:
        return jsonify({"error": "Enter a GitHub repository URL."}), 400
    try:
        repository = load_github_repository(url)
        chunks, stats = chunk_repository(repository["files"])
        embedder = TfidfEmbedder()
        embedder.fit([VectorStore._search_text(chunk) for chunk in chunks])
        _active_store().save(repository, chunks, embedder, stats)
        return jsonify({"ok": True, "repository": {"name": repository["name"], "source": repository["source"]}, "stats": stats})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/index/upload")
def index_upload():
    try:
        repository = load_uploaded_files(request.files.getlist("files"))
        chunks, stats = chunk_repository(repository["files"])
        embedder = TfidfEmbedder()
        embedder.fit([VectorStore._search_text(chunk) for chunk in chunks])
        _active_store().save(repository, chunks, embedder, stats)
        return jsonify({"ok": True, "repository": {"name": repository["name"], "source": repository["source"]}, "stats": stats})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/ask")
def ask():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Ask a question about the indexed codebase."}), 400
    if not _active_store().load():
        return jsonify({"error": "Index a repository or upload files before asking questions."}), 400
    try:
        result = RAGEngine(Retriever(_active_store())).answer(
            question,
            body.get("mode", "answer"),
            body.get("language", "all"),
        )
        return jsonify(result)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503


@app.get("/api/health")
def health():
    from config import LLM_MODEL, OLLAMA_URL
    import requests

    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        response.raise_for_status()
        models = [item.get("name", "") for item in response.json().get("models", [])]
        installed = any(name == LLM_MODEL or name.startswith(LLM_MODEL + ":") for name in models)
        return jsonify({
            "ollama": "connected",
            "model": LLM_MODEL,
            "model_installed": installed,
            "ready": installed,
        })
    except requests.RequestException:
        return jsonify({
            "ollama": "disconnected",
            "model": LLM_MODEL,
            "model_installed": False,
            "ready": False,
            "message": "Start Ollama to enable generated answers.",
        }), 503


@app.get("/api/files")
def files():
    payload = _active_store().load()
    if not payload:
        return jsonify({"files": []})
    unique = {}
    for chunk in payload.get("chunks", []):
        unique[chunk["path"]] = unique.get(chunk["path"], 0) + 1
    return jsonify({"files": [{"path": path, "chunks": count} for path, count in sorted(unique.items())]})


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Upload is too large. Keep the combined files under 25 MB."}), 413


if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    app.run(host="127.0.0.1", port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1")
