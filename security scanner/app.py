"""
SecuScan — a small, self-contained security scanning dashboard.

Modules:
  1. Port Scanner   — TCP connect scan (NMAP-style), auto-uses `nmap` if installed
  2. Web Scanner     — HTTP/HTTPS header, TLS, cookie and exposure checks (OWASP-style)
  3. Code Scanner    — static pattern-based vulnerability detection (Python/JS/PHP)

Run locally, no Docker required:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, jsonify
from scanners import port_scanner, web_scanner, code_scanner
from scanners.target import TargetError

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Keep a small in-memory history for the current server session (no DB needed).
SCAN_HISTORY = []


def _record(scan_type, target, result, error=None):
    entry = {
        "id": len(SCAN_HISTORY) + 1,
        "type": scan_type,
        "target": target,
        "ok": error is None,
        "error": error,
        "result": result,
    }
    SCAN_HISTORY.insert(0, entry)
    del SCAN_HISTORY[50:]  # cap history
    return entry


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan/port", methods=["POST"])
def api_port_scan():
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    mode = data.get("mode", "common")
    if not target:
        return jsonify({"error": "Target host/IP is required."}), 400
    try:
        result = port_scanner.run_scan(target, port_mode=mode)
        entry = _record("port", target, result)
        return jsonify(entry)
    except TargetError as e:
        return jsonify(_record("port", target, None, error=str(e))), 400
    except Exception as e:
        return jsonify(_record("port", target, None, error=f"Unexpected error: {e}")), 500


@app.route("/api/scan/web", methods=["POST"])
def api_web_scan():
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"error": "Target URL is required."}), 400
    try:
        result = web_scanner.run_scan(target)
        entry = _record("web", target, result)
        return jsonify(entry)
    except TargetError as e:
        return jsonify(_record("web", target, None, error=str(e))), 400
    except Exception as e:
        return jsonify(_record("web", target, None, error=f"Unexpected error: {e}")), 500


@app.route("/api/scan/code", methods=["POST"])
def api_code_scan():
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "")
    filename = data.get("filename", "")
    language = data.get("language") or None
    try:
        result = code_scanner.run_scan(code, filename=filename, language=language)
        entry = _record("code", filename or "(pasted code)", result)
        return jsonify(entry)
    except Exception as e:
        entry = _record("code", filename or "(pasted code)", None, error=str(e))
        return jsonify(entry), 400


@app.route("/api/history")
def api_history():
    return jsonify(SCAN_HISTORY)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
