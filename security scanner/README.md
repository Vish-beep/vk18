# VulnScope — Security Scanner Tool

A self-contained security scanning dashboard covering the three modules from
the project brief: **port scanning**, **web/URL scanning**, and **code
vulnerability scanning**. Pure Python + Flask + vanilla JS/HTML/CSS — no
Docker, no database, no external paid services.

## What it does

| Module | Notes |
|---|---|
| **Port Scanner** | TCP connect scan of a host. Uses the `nmap` CLI automatically for service/version detection if it's installed on your machine; otherwise falls back to a built-in multi-threaded Python socket scanner (no root needed). Flags risky open ports (Telnet, exposed Redis/Mongo, RDP, etc). |
| **Web Scanner** | Passive OWASP-style checks on a URL: missing security headers (HSTS, CSP, X-Frame-Options...), TLS certificate expiry/validity, cookie `Secure`/`HttpOnly` flags, common exposed paths (`.env`, `.git/config`, backups...), and basic form hygiene (password fields over HTTP, missing CSRF hints). Sends no attack payloads — read-only checks. |
| **Code Scanner** | Static pattern analysis for Python / JavaScript-TypeScript / PHP. Flags `eval()`/`exec()`, shell/SQL injection patterns, hardcoded secrets, weak hashing (MD5/SHA1), insecure deserialization (`pickle`, unsafe `yaml.load`), XSS-prone patterns (`innerHTML`, `document.write`), and more. Paste code or upload a file. |

Each finding gets a severity (Critical / High / Medium / Low / Info), the exact
evidence/line where relevant, and a three-part explanation:

| Field | Answers |
|---|---|
| **Threat** | What can an attacker do with this? |
| **Vulnerability** | What exactly is the weakness? |
| **Why it happened** | The root cause: a risky default, a missed setting, or a coding habit |

Each finding also carries a CWE reference. All of this lives in
`scanners/knowledge.py`; `test_scanners.py` fails if any rule the scanners can
emit has no entry there.

## Input handling & accuracy notes

- Targets are cleaned before scanning: typos such as `httos /host`, `htps:/host`,
  stray spaces/quotes are auto-corrected (and reported in the results), and bad
  hostnames/schemes give a clear message instead of a raw DNS traceback.
- Exposed-file checks only report a hit when the response body looks like the real
  file (e.g. `.env` must contain `KEY=value` lines), so sites that return HTTP 200
  for every URL no longer produce false positives.
- Only scan systems you own or have written permission to test.
- Run `python test_scanners.py` for the offline self-test.

## Setup

Requires Python 3.9+.

```bash
cd vulnscope
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

Optional: install `nmap` (e.g. `sudo apt install nmap` / `brew install nmap`)
for richer service/version detection in the Port Scanner. It's entirely
optional — the socket-based fallback works with zero extra setup.

## Project layout

```
vulnscope/
├── app.py                  # Flask routes / API
├── scanners/
│   ├── port_scanner.py     # TCP scan + nmap integration
│   ├── web_scanner.py      # HTTP header / TLS / exposure checks
│   ├── knowledge.py        # threat / vulnerability / cause text for every finding
│   └── code_scanner.py     # Static regex-based vulnerability rules
├── templates/index.html
├── static/css/style.css
├── static/js/app.js
└── requirements.txt
```

## Extending it

- **More code rules**: add entries to `PYTHON_RULES` / `JS_RULES` / `PHP_RULES`
  in `scanners/code_scanner.py` — each is just `(regex, severity, title, detail)`.
  Then add a matching `"code:<title>"` entry in `scanners/knowledge.py` so the
  finding shows its threat, vulnerability and cause.
- **More web checks**: add functions in `scanners/web_scanner.py` and call them
  from `run_scan()`.
- **Persist scan history**: currently kept in memory per server run (resets on
  restart). Swap `SCAN_HISTORY` in `app.py` for SQLite if you want it to survive
  restarts.
- **Auth / rate limiting**: if you deploy this beyond localhost, put it behind
  auth — a scanner that anyone can point at arbitrary hosts is itself a
  liability.

## ⚠️ Responsible use

Only run the Port Scanner and Web Scanner against hosts/URLs **you own or have
explicit written permission to test**. Scanning third-party infrastructure
without authorization is illegal in most jurisdictions (e.g. under the US CFAA
or India's IT Act). This tool is intended for learning, coursework, and
authorized security assessments — the same spirit as tools like OWASP ZAP,
Nessus, or OpenVAS referenced in the original project notes.
