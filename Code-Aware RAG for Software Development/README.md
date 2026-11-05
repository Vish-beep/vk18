# CodeMind

CodeMind is a code-aware RAG workspace for software development. It parses source structure, preserves semantic units, retrieves relevant code with metadata-aware TF-IDF search, and returns grounded explanations, suggestions, and documentation.

## Run locally

### No virtual environment

Python 3.10+ is required. On macOS/Linux, make the launcher executable once and run it:

```bash
chmod +x run.sh
./run.sh
```

On Windows, first install [Ollama](https://ollama.com/download/windows), open Command Prompt, and run `ollama pull qwen2.5-coder:3b`. Then double-click `run.bat` or run it from Command Prompt. The launcher installs dependencies into the normal user Python package location and starts CodeMind on port 3000. No `.venv` is created.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # optional, for generated answers
python app.py
```

Open `http://127.0.0.1:3000`. The Flask server binds to localhost only. CodeMind indexes repositories locally and uses Ollama running on your computer to generate cited explanations, suggestions, and documentation. No API key or paid AI service is required. Install Ollama, then run `ollama pull qwen2.5-coder:3b` before asking questions.

## Architecture

The ingestion path lives in `core/github_loader.py`. `code_parser.py` extracts Python AST symbols and language-agnostic symbols/comments for other supported languages. `code_chunker.py` keeps semantic units together, while `embeddings.py`, `vector_store.py`, and `retriever.py` implement a persistent local hybrid index. `rag_engine.py` builds grounded context and calls the local Ollama chat model (`qwen2.5-coder:3b`) to generate natural-language answers. If Ollama is not running or the model is missing, the chat endpoint returns a clear setup error rather than displaying raw retrieved source chunks as if they were an AI answer.

Run the regression checks with `python3 -m unittest discover -s tests -v`. The active index is stored at `data/indexes/active.json`, with a repository-named snapshot written alongside it for reuse.
