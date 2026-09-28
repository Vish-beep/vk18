import os
import uuid
from flask import Flask, jsonify, render_template, request

from config import (
    UPLOAD_FOLDER,
    SUPPORTED_EXTENSIONS,
    MAX_UPLOAD_MB,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from document_processor import extract_text, clean_text, chunk_text
from ollama_client import get_embedding, check_ollama
from vector_store import add_documents, document_summary
from rag import answer_question
from agent import AgentOrchestrator
from logger import logger

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

orchestrator = AgentOrchestrator()

def safe_filename(filename):
    filename = os.path.basename(filename).strip()
    if not filename:
        raise ValueError("Invalid filename.")
    if len(filename) > 150:
        raise ValueError("Filename is too long.")
    return filename

@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": f"File exceeds {MAX_UPLOAD_MB} MB limit."}), 413

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "application": "ok",
        "ollama": check_ollama(),
        "index": document_summary(),
    })

@app.route("/documents")
def documents():
    return jsonify(document_summary())

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    file = request.files["file"]
    try:
        filename = safe_filename(file.filename)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    extension = os.path.splitext(filename)[1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        return jsonify({
            "error": "Unsupported format. Use PDF, DOCX, TXT or MD."
        }), 400

    stored_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, stored_name)
    try:
        file.save(file_path)
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            raise ValueError("The upload was empty or was not saved completely. Please upload the file again.")
        text = clean_text(extract_text(file_path))
        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        if not chunks:
            raise ValueError("No text chunks were produced.")

        items = []
        for index, chunk in enumerate(chunks):
            items.append({
                "id": uuid.uuid4().hex,
                "text": chunk,
                "embedding": get_embedding(chunk),
                "source": filename,
                "metadata": {
                    "chunk_index": index,
                    "stored_file": stored_name,
                },
            })
        add_documents(items)
        logger.info("Indexed %s: %d chunks", filename, len(items))
        return jsonify({
            "message": "Document indexed successfully.",
            "file": filename,
            "chunks": len(items),
        })
    except Exception as exc:
        logger.exception("Upload/indexing failed for %s", filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
        return jsonify({"error": str(exc)}), 500

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"error": "Question is required."}), 400
    if len(question) > 2000:
        return jsonify({"error": "Question is too long."}), 400
    try:
        return jsonify(answer_question(question))
    except Exception as exc:
        logger.exception("RAG question failed")
        return jsonify({"error": str(exc)}), 500

@app.route("/research", methods=["POST"])
def research():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()
    if not topic:
        return jsonify({"error": "Research topic is required."}), 400
    if len(topic) > 500:
        return jsonify({"error": "Research topic is too long."}), 400
    try:
        result = orchestrator.research_agent.run(topic)
        return jsonify(result["result"])
    except Exception as exc:
        logger.exception("Web research failed")
        return jsonify({"error": str(exc)}), 500

@app.route("/generate-report", methods=["POST"])
def generate_report():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()
    if not topic:
        return jsonify({"error": "Report topic is required."}), 400
    if len(topic) > 500:
        return jsonify({"error": "Report topic is too long."}), 400
    try:
        result = orchestrator.run(topic)
        report = result["agents"][-1]["report"]
        return jsonify({
            "topic": topic,
            "report": report,
            "agents": result["agents"],
        })
    except Exception as exc:
        logger.exception("Report generation failed")
        return jsonify({"error": str(exc)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
