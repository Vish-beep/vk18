from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import json
import os

from utils.pdf_loader import read_pdf, read_pdf_metadata
from utils.doc_loader import read_docx, read_docx_metadata
from utils.chunker import chunk_text
from utils.embedding import create_embeddings
from utils.vector_store import create_vector_store, vector_store_exists
from utils.chatbot import generate_answer
from utils.bibliography import extract_bibliographic_facts, merge_bibliographic_metadata
from utils import chat_store


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
VECTOR_FOLDER = "vectors"
STATE_FILE = os.path.join(VECTOR_FOLDER, "current_doc.json")
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB

for folder in (UPLOAD_FOLDER, VECTOR_FOLDER):
    if not os.path.exists(folder):
        os.makedirs(folder)


def _save_current_doc(filename, chunk_count, metadata=None):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "filename": filename,
            "chunks": chunk_count,
            "metadata": metadata or {},
        }, f, ensure_ascii=False, indent=2)


def _load_current_doc():
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


# -------------------------
# Home Page
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -------------------------
# Current document status
# -------------------------

@app.route("/status", methods=["GET"])
def status():
    ready = vector_store_exists()
    doc = _load_current_doc()

    if ready and not doc:
        # A vector store exists but predates the filename-tracking feature.
        doc = {"filename": "Previously uploaded document", "chunks": None}

    return jsonify({
        "ready": ready,
        "document": doc,
    })


# -------------------------
# Upload Document
# -------------------------

@app.route("/upload", methods=["POST"])
def upload():

    if "file" not in request.files:
        return jsonify({"ok": False, "message": "No file was sent."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"ok": False, "message": "No file selected."}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"ok": False, "message": "Only PDF and DOCX files are allowed."}), 400

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        file.save(filepath)

        if ext == ".pdf":
            text = read_pdf(filepath)
            embedded_metadata = read_pdf_metadata(filepath)
        else:
            text = read_docx(filepath)
            embedded_metadata = read_docx_metadata(filepath)

        if not text or not text.strip():
            return jsonify({
                "ok": False,
                "message": "Could not extract any text from that file. "
                           "It may be a scanned/image-only document.",
            }), 422

        # Extract facts from the complete visible document before chunking. This
        # prevents a creator field or an arbitrary name from being mistaken for
        # the document's author or publisher.
        visible_facts = extract_bibliographic_facts(text, embedded_metadata)
        metadata = merge_bibliographic_metadata(embedded_metadata, visible_facts)
        metadata["document_facts"] = visible_facts

        chunks = chunk_text(text, chunk_size=800, overlap=150)

        if not chunks:
            return jsonify({"ok": False, "message": "The document appears to be empty."}), 422

        embeddings = create_embeddings(chunks)

        create_vector_store(embeddings, chunks)

        _save_current_doc(filename, len(chunks), metadata)

        return jsonify({
            "ok": True,
            "message": f"\"{filename}\" is ready. Ask me anything about it.",
            "filename": filename,
            "chunks": len(chunks),
        })

    except Exception as exc:
        return jsonify({
            "ok": False,
            "message": f"Something went wrong while processing the file: {exc}",
        }), 500


# -------------------------
# Chat sessions (history)
# -------------------------

@app.route("/chats", methods=["GET"])
def list_chats():
    return jsonify({"chats": chat_store.list_chats()})


@app.route("/chats", methods=["POST"])
def create_chat():
    chat = chat_store.create_chat()
    return jsonify({
        "id": chat["id"],
        "title": chat["title"],
        "created_at": chat["created_at"],
        "updated_at": chat["updated_at"],
    })


@app.route("/chats/<chat_id>", methods=["GET"])
def get_chat(chat_id):
    chat = chat_store.get_chat(chat_id)

    if not chat:
        return jsonify({"error": "Chat not found."}), 404

    return jsonify(chat)


@app.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    if not chat_store.delete_chat(chat_id):
        return jsonify({"error": "Chat not found."}), 404

    return jsonify({"ok": True})


@app.route("/chats/<chat_id>/rename", methods=["PUT"])
def rename_chat(chat_id):
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()

    if not title:
        return jsonify({"error": "Title is required."}), 400

    chat = chat_store.rename_chat(chat_id, title)

    if not chat:
        return jsonify({"error": "Chat not found."}), 404

    return jsonify({"id": chat["id"], "title": chat["title"]})


# -------------------------
# Ask Question
# -------------------------

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    chat_id = (data.get("chat_id") or "").strip()

    if not question:
        return jsonify({"answer": "Please type a question."}), 400

    if not chat_id or not chat_store.get_chat(chat_id):
        return jsonify({"answer": "This chat session no longer exists. Start a new chat."}), 400

    chat_store.append_message(chat_id, "user", question)

    try:
        chat = chat_store.get_chat(chat_id) or {}
        history = chat.get("messages", [])[-8:]
        document = _load_current_doc() or {}
        answer = generate_answer(
            question,
            conversation=history,
            document_metadata=document.get("metadata", {}),
        )
        chat = chat_store.append_message(chat_id, "bot", answer)
        return jsonify({"answer": answer, "title": chat["title"]})

    except Exception as exc:
        answer = f"Something went wrong while answering: {exc}"
        chat_store.append_message(chat_id, "bot", answer)
        return jsonify({"answer": answer}), 500


if __name__ == "__main__":
    app.run(debug=True)
