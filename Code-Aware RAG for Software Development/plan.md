# CodeMind implementation plan

## Product
CodeMind is a code-aware RAG workspace for developers. It ingests public GitHub repositories or uploaded source files, parses structure and documentation, indexes semantic code chunks, and answers questions with citations.

The delivered archive also includes `run.sh` and `run.bat` launchers for users who do not want to create a Python virtual environment. They install the pinned dependencies into the normal user Python package location before starting the app.

## Implementation approach
- Flask serves a single-page workspace and JSON APIs on port 3000.
- `core/github_loader.py` downloads a public GitHub repository archive and filters source files safely.
- `core/code_parser.py` uses Python AST where available and a language-agnostic fallback for JavaScript, TypeScript, Java, Go, Rust, and Markdown.
- `core/code_chunker.py` creates structure-preserving chunks with file, line, symbol, language, and documentation metadata.
- `core/embeddings.py` provides deterministic TF-IDF vectors locally with no external embedding service.
- `core/vector_store.py` persists chunks and vectorizer state as JSON under `data/indexes/`.
- `core/retriever.py` ranks lexical/semantic similarity and boosts symbol/file/language matches.
- `core/rag_engine.py` builds grounded context and returns cited local explanations, suggestions, and documentation without an external chat endpoint.
- The browser UI exposes ingestion, indexing progress, question modes, answer rendering, citations, and copy actions.

## Design
Three possible directions: terminal-native observability (0.06); warm editorial developer notebook (0.08); neon cyberpunk IDE (0.04). Chosen: **terminal-native observability**.

- **Design movement:** utilitarian developer tooling with restrained terminal cues and editorial hierarchy.
- **Core principles:** evidence first; calm density; visible system state; fast scanning.
- **Color philosophy:** near-black graphite reduces glare, warm paper panels keep long answers readable, and acid lime marks only active or trustworthy states.
- **Layout paradigm:** asymmetric command deck: a narrow control rail, dominant conversation canvas, and a slim evidence rail rather than centered cards.
- **Signature elements:** lime “signal” line, bracketed labels, and monospaced metadata paired with humanist body text.
- **Interaction philosophy:** every action reports state; empty states teach the next move; sources stay one click from the answer.
- **Animation:** short 180–240ms fades and status pulses only for indexing or active requests; no decorative motion.
- **Typography:** Space Grotesk for interface hierarchy, IBM Plex Mono for code and metadata.
- **Brand essence:** “Understand the codebase before you change it.” Precise, grounded, unflashy.
- **Brand voice:** direct and evidence-led. Example: “Index a repository, then ask what the code actually does.” / “Every suggestion points back to a source chunk.”
- **Wordmark:** `CodeMind //` with a trailing cursor block.
- **Signature brand color:** acid lime `#c7f36b`.

## Project structure
`app.py` owns HTTP routes; `config.py` centralizes paths and limits; `core/` contains ingestion, parsing, chunking, indexing, retrieval, and generation; `templates/` and `static/` contain the workspace UI; `data/indexes/` stores reusable indexes; `uploads/` stores transient uploads.
