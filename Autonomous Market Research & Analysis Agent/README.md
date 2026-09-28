# Autonomous Market Research & Analysis Agent

A Docker-free Flask + Python + HTML/CSS/JavaScript implementation of the six-week project brief.

## Project coverage

1. **Data ingestion & RAG foundation**
   - PDF/DOCX/TXT/MD ingestion
   - text cleaning and overlapping chunking
   - Ollama embeddings
   - local JSON vector database
   - Top-3 semantic retrieval

2. **Advanced RAG & evaluation**
   - semantic search with cosine similarity
   - grounded-answer prompt
   - lexical grounding/hallucination check
   - retrieval metrics (Precision@K, Recall@K, MRR when an evaluation set is supplied)

3. **Agent architecture**
   - Document Agent
   - Research Agent
   - Report Agent
   - Agent Orchestrator

4. **Web intelligence**
   - live DuckDuckGo HTML search using Python standard library
   - source extraction and URL citations
   - source validation (HTTP HEAD/GET fallback)

5. **Application development**
   - Flask API
   - browser UI
   - structured logging
   - basic filename/path validation
   - report generation

6. **Deployment & portfolio**
   - local production-style run instructions
   - tests
   - GitHub-ready structure
   - no Docker required

## Requirements

- Python 3.10+
- Flask
- pypdf
- python-docx
- Ollama installed and running locally
- Ollama models:
  - `llama3.2:3b`
  - `nomic-embed-text`

Install Python packages:

```bat
pip install -r requirements.txt
```

Install/check Ollama models:

```bat
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

Start Ollama if it is not already running:

```bat
ollama serve
```

Run the application:

```bat
python app.py
```

Open:

`http://127.0.0.1:5000`

## Main API endpoints

- `GET /` - web UI
- `POST /upload` - upload and index a document
- `POST /ask` - RAG question answering
- `POST /research` - live web research
- `POST /generate-report` - orchestrate document + web research and generate report
- `GET /documents` - indexed document/chunk summary
- `GET /health` - application/Ollama health

## Notes

The vector store is intentionally implemented as a local JSON vector database so the project can run without Docker or a separate database server. It stores each chunk, its embedding, source filename, and metadata and performs cosine similarity search in Python.

Web search uses DuckDuckGo's HTML results through Python's standard library. If a network blocks the search request, the application reports the source limitation rather than inventing results.

## Suggested demonstration

1. Upload a company/industry PDF.
2. Ask a document question.
3. Show the top-3 retrieved sources and similarity scores.
4. Run web research on the same topic.
5. Generate an executive report.
6. Show citations in the report.
7. Open `/health` and `/documents`.


## PDF upload troubleshooting

The application validates uploaded PDFs before indexing them. If you see `Stream has ended unexpectedly`, the PDF parser detected an incomplete/corrupted PDF stream. Try opening the PDF in Chrome/Adobe Reader and using **Print > Save as PDF** or **Save As** to create a fresh PDF, then upload that copy. The application uses `pypdf` with recovery mode (`strict=False`) and continues past individual unreadable pages when possible.

If the PDF is scanned/image-only, this project does not perform OCR because OCR is outside the required Python/Flask/HTML/CSS/JavaScript + Ollama stack. Convert it to a text PDF or provide a text-based PDF.


## Redesigned UI

The frontend (`templates/index.html`, `static/style.css`, `static/app.js`) was rebuilt with **no backend changes** and no external dependencies (works offline):

- Sidebar workspace: Overview, Knowledge Base, Ask Documents, Web Research, Executive Report
- Light/dark theme (follows your system, remembers your choice)
- Drag-and-drop multi-file upload with per-file status and client-side validation
- Chat-style Q&A with grounding meter and expandable top-3 sources with similarity bars
- Web research cards with HTTP status and validation badges
- Agent pipeline progress, evidence panels, and a formatted report with colour-coded
  `[DOCUMENT SOURCE n]` / `[WEB SOURCE n]` citations
- Copy, download (.md) and print/PDF for reports
- Live Ollama/model readiness checks, responsive layout for mobile
