# CodeMind delivery checklist

- [x] Repository and code ingestion through GitHub repository URLs plus local file uploads, with clear loading and validation states.
- [x] Language-aware parsing in `core/code_parser.py` that extracts AST structures, symbols, imports, functions, classes, comments, and docstrings from supported source files.
- [x] Structure-preserving code chunking in `core/code_chunker.py` that keeps semantic units and relevant documentation or comments together while retaining file paths and line metadata.
- [x] Embedding generation and persistent vector indexing through `core/embeddings.py` and `core/vector_store.py`, storing reusable repository indexes under `data/indexes/`.
- [x] Hybrid contextual retrieval in `core/retriever.py` that combines semantic relevance with code metadata such as language, symbol, file, and source location.
- [x] A grounded RAG pipeline in `core/rag_engine.py` that answers repository questions and produces contextual code suggestions or documentation based on retrieved source context.
- [x] An interactive `templates/index.html` workspace for selecting a repository or upload, asking development questions, viewing generated output, and inspecting cited source snippets.
- [x] A Python application entry point and centralized configuration using `app.py` and `config.py`, with dependencies documented in `requirements.txt` and modular GitHub loading in `core/github_loader.py`.
- [x] Responsive frontend behavior and presentation implemented in `static/js/script.js` and `static/css/style.css`, including progress, errors, syntax-friendly results, and copyable output.
