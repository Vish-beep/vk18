# Certify — AI Based Document and Assessment Management System

Turns training documents (PDF / Word / TXT) into a scored, retry-aware online
certification exam.

## What it does

1. **Upload** a document (manual, handbook, policy, SOP, etc.).
2. **Question generation** — the app extracts the text and builds a bank of
   25–75 single-choice and multiple-select questions.
   - If an `ANTHROPIC_API_KEY` environment variable is set, it uses **Claude**
     to write context-aware questions and distractors.
   - Otherwise it falls back to an **offline heuristic engine** (no external
     calls, no API key required) that extracts key sentences and terms and
     builds blank-style MCQs with plausible distractors.
3. **Register a candidate** against a question bank.
4. **Take the exam** — 20 questions are randomly drawn from the bank, 5
   points each (100 points total).
5. **Automatic evaluation and retest logic**:
   - Score **>= 35%** in any attempt → **PASS**, no further attempts.
   - Score **< 35%** on attempt 1 or 2 → a new attempt is auto-generated with
     a fresh random set of 20 questions (up to 3 attempts total).
   - Attempt 3: **>= 35% → PASS**, otherwise **FAILED** (no more attempts).
   - This ensures that if a candidate reaches the 35% threshold at any point, they are considered to have passed.
6. **Reports** — a dashboard of every candidate, their attempt count,
   latest score, and pass/fail/retry status.

## Project structure

```
app.py                     Flask app / routes
utils/
  document_parser.py       PDF / DOCX / TXT text extraction
  question_generator.py    AI (Claude) + heuristic question generation
  evaluator.py              Scoring + pass/fail/retry rules
  storage.py                SQLite persistence (candidates, attempts, banks)
templates/                 Jinja2 HTML templates
static/css/style.css       Styling
data/                      SQLite DB + generated question banks (JSON)
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000**.

### Optional: enable the AI question-generation engine

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python app.py
```

Without a key, the app still works fully using the offline heuristic engine
— nothing is required to get started.

## Notes / things you may want to extend

- Question banks are stored as JSON files under `data/question_banks/`, one
  per uploaded document, referenced by `bank_id` in the database.
- `app.secret_key` and any production deployment should set a real
  `SECRET_KEY` environment variable rather than the dev default.
- The heuristic engine is intentionally simple (frequency-based keyword
  extraction + sentence blanking) so the whole system runs with zero
  external dependencies beyond Flask/pypdf/python-docx. Swap in the AI
  engine (via `ANTHROPIC_API_KEY`) for noticeably higher-quality questions
  on nuanced or narrative documents.
