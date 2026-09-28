"""Run: python test_scanners.py   (offline; uses a local test server)"""
import threading, http.server, socketserver
from scanners.target import normalize_url, normalize_host, TargetError
from scanners import web_scanner

# ---- URL normalisation ----
good = {
    "httos /voters.eci.gov.in":      "https://voters.eci.gov.in/",   # the reported input
    "httos://voters.eci.gov.in":     "https://voters.eci.gov.in/",
    "htps:/example.com":             "https://example.com/",
    "htttp://example.com/a?b=1":     "http://example.com/a?b=1",
    "https //example.com":           "https://example.com/",
    "  https://Example.com/  ":      "https://example.com/",
    "example.com/login":             "https://example.com/login",
    "localhost:8080":                "https://localhost:8080/",
    "http://127.0.0.1:5000":         "http://127.0.0.1:5000/",
    "voters.eci.gov.in":             "https://voters.eci.gov.in/",
}
for raw, want in good.items():
    got = normalize_url(raw).url
    assert got == want, (raw, got, want)
for bad in ["", "ftp://example.com", "javascript:alert(1)", "my site.com", "https://", "http://exa mple.com", "http://a..b"]:
    try:
        normalize_url(bad); raise SystemExit(f"should have failed: {bad!r}")
    except TargetError as e:
        print("rejected:", repr(bad), "->", e)
assert normalize_host("https://scanme.nmap.org:80/x") == "scanme.nmap.org"
assert normalize_host("::1") == "::1"
print("normalisation OK")

# ---- detection accuracy against a local server ----
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/.env":            # real .env
            body, ct = b"DB_PASSWORD=hunter2\nAPI_KEY=abc\n", "text/plain"
        elif self.path == "/backup.zip":    # soft-404 style: 200 + HTML  (must NOT be flagged)
            body, ct = b"<!doctype html><html><body>Not found</body></html>", "text/html"
        elif self.path == "/.git/config":   # SPA soft-404 (must NOT be flagged)
            body, ct = b"<html><body>app</body></html>", "text/html"
        elif self.path.startswith("/sub/"):
            body, ct = b"<html><body><form method=post><input type=password name=p></form></body></html>", "text/html"
        else:
            body, ct = b"<html><body>hi</body></html>", "text/html"
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Set-Cookie", "sid=1; Path=/")
        self.send_header("Server", "nginx/1.18.0")
        self.end_headers(); self.wfile.write(body)

srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), H); srv.daemon_threads = True
threading.Thread(target=srv.serve_forever, daemon=True).start()
port = srv.server_address[1]

r = web_scanner.run_scan(f"http://127.0.0.1:{port}/sub/page")   # nested page: paths must still hit site root
titles = [f["title"] for f in r["findings"]]
print(*titles, sep="\n")
assert "Exposed file: /.env" in titles
assert not any("backup.zip" in t or ".git/config" in t for t in titles), "soft-404 false positive"
assert any("Cookie 'sid' missing HttpOnly" in t for t in titles)
assert any("no SameSite" in t for t in titles)
assert not any("Strict-Transport-Security" in t for t in titles), "HSTS shouldn't be required on http"
assert any("Server header discloses" in t and "nginx/1.18.0" in t for t in titles)

# friendly errors
for bad, frag in [("httos /no-such-host-xyz.invalid", "Could not resolve"),
                  (f"http://127.0.0.1:1", "refused")]:
    try:
        web_scanner.run_scan(bad); raise SystemExit("expected failure")
    except TargetError as e:
        assert frag.lower() in str(e).lower(), str(e); print("error OK:", e)
print("ALL TESTS PASSED")
