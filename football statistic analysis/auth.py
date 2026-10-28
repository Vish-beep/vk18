"""User registration and login for Football Analytics.

Uses only Flask + the standard library (SQLite for storage, Werkzeug for
password hashing), so no extra dependencies are required.

Hook it into the app with:

    from auth import init_auth
    init_auth(app)

Set app.config["REQUIRE_LOGIN"] = False (before init_auth) if you want the
analysis pages to stay public while keeping the login/register pages.
"""

import os
import re
import secrets
import sqlite3
from datetime import timedelta

from flask import (
    Blueprint, current_app, flash, g, redirect,
    render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
MIN_PASSWORD_LENGTH = 8

# Endpoints that never require a login.
PUBLIC_ENDPOINTS = {"home", "static"}

# Hash checked when the user does not exist, so login timing does not reveal
# which usernames are registered.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


# ==========================================
# DATABASE
# ==========================================
def get_db():
    if "db" not in g:
        path = os.path.join(current_app.instance_path, "users.db")
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    os.makedirs(app.instance_path, exist_ok=True)
    db = sqlite3.connect(os.path.join(app.instance_path, "users.db"))
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
            email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


# ==========================================
# SECRET KEY
# ==========================================
def load_secret_key(app):
    """Use FLASK_SECRET_KEY if set, otherwise create and persist a random key
    in the instance folder (which is git-ignored), so no secret lives in code."""
    env_key = os.environ.get("FLASK_SECRET_KEY")
    if env_key:
        return env_key

    os.makedirs(app.instance_path, exist_ok=True)
    key_path = os.path.join(app.instance_path, "secret_key")

    if os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as handle:
            return handle.read().strip()

    key = secrets.token_hex(32)
    with open(key_path, "w", encoding="utf-8") as handle:
        handle.write(key)
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass  # Not supported on every platform (e.g. Windows)
    return key


# ==========================================
# CSRF PROTECTION
# ==========================================
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def csrf_is_valid():
    sent = request.form.get("csrf_token", "")
    expected = session.get("_csrf", "")
    return bool(expected) and secrets.compare_digest(sent, expected)


# ==========================================
# HELPERS
# ==========================================
def safe_next(target):
    """Only allow redirects to paths inside this site (blocks open redirects)."""
    if (
        target
        and target.startswith("/")
        and not target.startswith("//")
        and "\\" not in target
    ):
        return target
    return url_for("dashboard")


def validate_registration(username, email, password, confirm):
    errors = []

    if not USERNAME_RE.match(username):
        errors.append(
            "Username must be 3-30 characters: letters, numbers and underscores only."
        )
    if not EMAIL_RE.match(email) or len(email) > 254:
        errors.append("Enter a valid email address.")
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    elif len(password) > 128:
        errors.append("Password must be 128 characters or fewer.")
    elif password.isdigit() or password.lower() == username.lower():
        errors.append("Choose a stronger password (not just numbers or your username).")
    if password != confirm:
        errors.append("Passwords do not match.")

    return errors


def log_user_in(user_id, remember=False):
    session.clear()  # drop any old session data (prevents session fixation)
    session["user_id"] = user_id
    session.permanent = bool(remember)


# ==========================================
# ROUTES
# ==========================================
@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard"))

    form = {"username": "", "email": ""}
    errors = []

    if request.method == "POST":
        form["username"] = request.form.get("username", "").strip()
        form["email"] = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not csrf_is_valid():
            errors.append("Your session expired. Please try again.")
        else:
            errors = validate_registration(
                form["username"], form["email"], password, confirm
            )

        if not errors:
            db = get_db()
            try:
                cursor = db.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (form["username"], form["email"], generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                errors.append("That username or email is already registered.")
            else:
                log_user_in(cursor.lastrowid)
                flash(f"Welcome, {form['username']}! Your account has been created.", "success")
                return redirect(url_for("dashboard"))

    return render_template("register.html", errors=errors, form=form,
                           min_length=MIN_PASSWORD_LENGTH)


@bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.values.get("next", "")

    if g.user:
        return redirect(safe_next(next_url))

    identifier = ""
    error = None

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if not csrf_is_valid():
            error = "Your session expired. Please try again."
        else:
            user = get_db().execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (identifier, identifier),
            ).fetchone()

            hash_to_check = user["password_hash"] if user else _DUMMY_HASH
            password_ok = check_password_hash(hash_to_check, password)

            if user and password_ok:
                log_user_in(user["id"], remember)
                flash(f"Welcome back, {user['username']}!", "success")
                return redirect(safe_next(next_url))

            error = "Invalid username/email or password."

    return render_template("login.html", error=error, identifier=identifier,
                           next_url=next_url)


@bp.route("/logout", methods=["POST"])
def logout():
    if csrf_is_valid():
        session.clear()
        flash("You have been signed out.", "info")
    return redirect(url_for("home"))


# ==========================================
# APP INTEGRATION
# ==========================================
def init_auth(app):
    app.config.setdefault("REQUIRE_LOGIN", True)
    app.config["SECRET_KEY"] = load_secret_key(app)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    )

    init_db(app)
    app.teardown_appcontext(close_db)
    app.register_blueprint(bp)

    @app.before_request
    def load_current_user():
        user_id = session.get("user_id")
        g.user = None
        if user_id is not None:
            row = get_db().execute(
                "SELECT id, username, email FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if row is None:
                session.clear()  # account no longer exists
            g.user = row

    @app.before_request
    def require_login():
        if not app.config["REQUIRE_LOGIN"]:
            return None
        endpoint = request.endpoint
        if (
            endpoint is None
            or endpoint in PUBLIC_ENDPOINTS
            or endpoint.startswith("auth.")
            or g.user is not None
        ):
            return None

        target = request.full_path.rstrip("?")
        flash("Please sign in to view that page.", "info")
        return redirect(url_for("auth.login", next=target))

    @app.context_processor
    def inject_auth():
        return {"current_user": g.get("user"), "csrf_token": csrf_token}

    @app.after_request
    def no_store_for_private_pages(response):
        # Keep signed-in pages out of the browser cache so "Back" after
        # logging out doesn't reveal them.
        if g.get("user") is not None:
            response.headers.setdefault("Cache-Control", "no-store")
        return response
