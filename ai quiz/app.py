"""
AI Based - Document and Assessment Management System
Flask application entry point.
"""
import os
import json
import random
import uuid
import string

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session
)
from werkzeug.utils import secure_filename

from utils import document_parser, question_generator, evaluator, storage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
BANK_DIR = os.path.join(BASE_DIR, "data", "question_banks")
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BANK_DIR, exist_ok=True)
storage.init_db()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def bank_path(bank_id):
    return os.path.join(BANK_DIR, f"{bank_id}.json")


def load_bank(bank_id):
    path = bank_path(bank_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bank(bank_id, questions):
    with open(bank_path(bank_id), "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)


# ---------------------------------------------------------------------
# Routes: Dashboard / Upload / Question bank
# ---------------------------------------------------------------------
@app.route("/")
def index():
    banks = storage.list_banks()
    return render_template("index.html", banks=banks)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("document")
        if not file or file.filename == "":
            flash("Please choose a document to upload.", "error")
            return redirect(url_for("upload"))
        if not allowed_file(file.filename):
            flash("Unsupported file type. Please upload PDF, DOCX, or TXT.", "error")
            return redirect(url_for("upload"))

        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        filepath = os.path.join(UPLOAD_DIR, unique_name)
        file.save(filepath)

        try:
            raw_text = document_parser.extract_text(filepath)
            text = document_parser.clean_text(raw_text)
        except Exception as e:
            flash(f"Could not read document: {e}", "error")
            return redirect(url_for("upload"))

        if len(text.split()) < 50:
            flash("Document has too little extractable text to generate questions.", "error")
            return redirect(url_for("upload"))

        questions, engine_used = question_generator.generate_question_bank(text)
        bank_id = uuid.uuid4().hex[:10]
        save_bank(bank_id, questions)
        storage.create_bank_record(bank_id, filename, engine_used, len(questions))

        flash(
            f"Generated {len(questions)} questions using the "
            f"{'AI (Claude)' if engine_used == 'ai' else 'offline heuristic'} engine.",
            "success",
        )
        return redirect(url_for("view_bank", bank_id=bank_id))

    return render_template("upload.html")


@app.route("/bank/<bank_id>")
def view_bank(bank_id):
    record = storage.get_bank_record(bank_id)
    questions = load_bank(bank_id)
    if not record or questions is None:
        flash("Question bank not found.", "error")
        return redirect(url_for("index"))
    return render_template("question_bank.html", record=record, questions=questions)


@app.route("/bank/<bank_id>/delete_question/<question_id>", methods=["POST"])
def delete_question(bank_id, question_id):
    questions = load_bank(bank_id)
    if questions is None:
        flash("Question bank not found.", "error")
        return redirect(url_for("index"))
    questions = [q for q in questions if q["id"] != question_id]
    save_bank(bank_id, questions)
    flash("Question removed from bank.", "success")
    return redirect(url_for("view_bank", bank_id=bank_id))


@app.route("/bank/<bank_id>/answer_key")
def answer_key(bank_id):
    record = storage.get_bank_record(bank_id)
    questions = load_bank(bank_id)
    if not record or questions is None:
        flash("Question bank not found.", "error")
        return redirect(url_for("index"))
    return render_template("answer_key.html", record=record, questions=questions)


@app.route("/bank/<bank_id>/answer_key/download")
def download_answer_key(bank_id):
    record = storage.get_bank_record(bank_id)
    questions = load_bank(bank_id)
    if not record or questions is None:
        flash("Question bank not found.", "error")
        return redirect(url_for("index"))

    letters = string.ascii_uppercase
    lines = [
        f"ANSWER KEY — {record['source_filename']}",
        f"Question bank ID: {bank_id}",
        f"Total questions: {len(questions)}",
        "=" * 60,
        "",
    ]
    for i, q in enumerate(questions, start=1):
        lines.append(f"{i}. [{ 'MULTI-SELECT' if q['type'] == 'multiple' else 'SINGLE-CHOICE' }] {q['question']}")
        for idx, opt in enumerate(q["options"]):
            marker = "*" if idx in q["correct"] else " "
            lines.append(f"   [{marker}] {letters[idx]}. {opt}")
        correct_letters = ", ".join(letters[i] for i in q["correct"])
        lines.append(f"   Correct answer: {correct_letters}")
        lines.append("")

    content = "\n".join(lines)
    from flask import Response
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename=answer_key_{bank_id}.txt"},
    )


# ---------------------------------------------------------------------
# Routes: Candidate registration & exam flow
# ---------------------------------------------------------------------
@app.route("/register/<bank_id>", methods=["GET", "POST"])
def register(bank_id):
    record = storage.get_bank_record(bank_id)
    if not record:
        flash("Question bank not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        if not name:
            flash("Candidate name is required.", "error")
            return redirect(url_for("register", bank_id=bank_id))
        candidate_id = storage.create_candidate(name, email, bank_id)
        return redirect(url_for("start_exam", candidate_id=candidate_id))

    return render_template("register.html", record=record)


@app.route("/exam/<int:candidate_id>/start")
def start_exam(candidate_id):
    candidate = storage.get_candidate(candidate_id)
    if not candidate:
        flash("Candidate not found.", "error")
        return redirect(url_for("index"))

    attempts = storage.get_attempts_for_candidate(candidate_id)
    attempt_number = len(attempts) + 1

    if attempts:
        last_outcome = attempts[-1]["outcome"]
        if last_outcome == "PASS":
            return redirect(url_for("result", candidate_id=candidate_id, attempt_number=len(attempts)))
        if last_outcome == "FAILED":
            return redirect(url_for("result", candidate_id=candidate_id, attempt_number=len(attempts)))
        if attempt_number > evaluator.MAX_ATTEMPTS:
            return redirect(url_for("result", candidate_id=candidate_id, attempt_number=len(attempts)))

    bank = load_bank(candidate["bank_id"])
    if not bank:
        flash("Question bank not found for this candidate.", "error")
        return redirect(url_for("index"))

    pool = bank if len(bank) <= evaluator.QUESTIONS_PER_ATTEMPT else random.sample(
        bank, evaluator.QUESTIONS_PER_ATTEMPT
    )
    session[f"attempt_{candidate_id}_questions"] = [q["id"] for q in pool]

    return render_template(
        "exam.html",
        candidate=candidate,
        questions=pool,
        attempt_number=attempt_number,
        max_attempts=evaluator.MAX_ATTEMPTS,
    )


@app.route("/exam/<int:candidate_id>/submit", methods=["POST"])
def submit_exam(candidate_id):
    candidate = storage.get_candidate(candidate_id)
    if not candidate:
        flash("Candidate not found.", "error")
        return redirect(url_for("index"))

    question_ids = session.get(f"attempt_{candidate_id}_questions")
    if not question_ids:
        flash("Your exam session expired. Please start again.", "error")
        return redirect(url_for("start_exam", candidate_id=candidate_id))

    bank = load_bank(candidate["bank_id"])
    bank_by_id = {q["id"]: q for q in bank}
    attempt_questions = [bank_by_id[qid] for qid in question_ids if qid in bank_by_id]

    answers = {}
    for q in attempt_questions:
        selected = request.form.getlist(f"q_{q['id']}")
        answers[q["id"]] = sorted(int(i) for i in selected)

    score, max_score, percentage, details = evaluator.grade_answers(attempt_questions, answers)

    attempts_so_far = storage.get_attempts_for_candidate(candidate_id)
    attempt_number = len(attempts_so_far) + 1
    outcome = evaluator.determine_outcome(percentage, attempt_number)

    storage.record_attempt(
        candidate_id, candidate["bank_id"], attempt_number,
        question_ids, answers, score, max_score, percentage, outcome,
    )
    session.pop(f"attempt_{candidate_id}_questions", None)

    return redirect(url_for("result", candidate_id=candidate_id, attempt_number=attempt_number))


@app.route("/exam/<int:candidate_id>/result/<int:attempt_number>")
def result(candidate_id, attempt_number):
    candidate = storage.get_candidate(candidate_id)
    if not candidate:
        flash("Candidate not found.", "error")
        return redirect(url_for("index"))

    attempts = storage.get_attempts_for_candidate(candidate_id)
    attempt = next((a for a in attempts if a["attempt_number"] == attempt_number), None)
    if not attempt:
        flash("Attempt not found.", "error")
        return redirect(url_for("index"))

    can_retry = (
        attempt["outcome"] == "RETRY"
        and attempt_number < evaluator.MAX_ATTEMPTS
    )

    return render_template(
        "result.html",
        candidate=candidate,
        attempt=attempt,
        all_attempts=attempts,
        can_retry=can_retry,
        max_attempts=evaluator.MAX_ATTEMPTS,
    )


# ---------------------------------------------------------------------
# Routes: Reporting
# ---------------------------------------------------------------------
@app.route("/reports")
def reports():
    candidates = storage.all_candidates_with_status()
    return render_template("dashboard.html", candidates=candidates)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
