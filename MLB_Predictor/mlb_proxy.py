"""
MLB Stats API - Local CORS Proxy
Uses only Python standard library — no pip installs needed.

Start:  python proxy.py          (Mac/Linux)
        python3 proxy.py         (if 'python' points to Python 2)
        py proxy.py              (Windows)

Test:   bash test-proxy.sh
Stop:   Ctrl+C
"""

import http.server
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PORT = 3001

ROUTES = {
    "/mlb/":    {"host": "https://statsapi.mlb.com",          "base": "/api/v1/"},
    "/stitch/": {"host": "https://bdfed.stitch.mlbinfra.com", "base": "/bdfed/"},
}

# Browser-style headers — Origin + Referer are what make the MLB API respond
BROWSER_HEADERS = {
    "Accept":           "application/json, text/plain, */*",
    "Accept-Language":  "en-US,en;q=0.9",
    "Cache-Control":    "no-cache",
    "Connection":       "keep-alive",
    "Origin":           "https://www.mlb.com",
    "Pragma":           "no-cache",
    "Referer":          "https://www.mlb.com/",
    "Sec-Fetch-Dest":   "empty",
    "Sec-Fetch-Mode":   "cors",
    "Sec-Fetch-Site":   "cross-site",
    "User-Agent":       (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept",
}

# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class ProxyHandler(http.server.BaseHTTPRequestHandler):

    # Silence the default per-request log line — we print our own
    def log_message(self, format, *args):
        pass

    def _apply_cors(self):
        for key, value in CORS_HEADERS.items():
            self.send_header(key, value)

    def _send_json_error(self, status: int, message: str):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self._apply_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight requests from the browser."""
        self.send_response(204)
        self._apply_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        pathname = parsed.path
        query    = ("?" + parsed.query) if parsed.query else ""

        # ── Health check ──────────────────────────────────────────────────
        if pathname == "/health":
            body = json.dumps({
                "status": "ok",
                "time":   datetime.now(timezone.utc).isoformat(),
                "port":   PORT,
            }).encode("utf-8")
            self.send_response(200)
            self._apply_cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # ── Proxy routes ──────────────────────────────────────────────────
        for prefix, route in ROUTES.items():
            if pathname.startswith(prefix):
                tail          = pathname[len(prefix):]
                upstream_url  = route["host"] + route["base"] + tail + query
                self._forward(upstream_url)
                return

        # ── 404 ───────────────────────────────────────────────────────────
        self._send_json_error(404, "Unknown route. Valid prefixes: /health  /mlb/  /stitch/")

    def _forward(self, upstream_url: str):
        """Fetch upstream_url with browser headers and pipe the response back."""
        req = urllib.request.Request(upstream_url, headers=BROWSER_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body   = resp.read()
                status = resp.status
                print(f"[{datetime.now(timezone.utc).isoformat()}]  {status}  {upstream_url}")
                self.send_response(status)
                self._apply_cors()
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        except urllib.error.HTTPError as err:
            print(f"[{datetime.now(timezone.utc).isoformat()}]  {err.code}  {upstream_url}")
            self._send_json_error(err.code, f"Upstream HTTP error: {err.reason}")

        except urllib.error.URLError as err:
            print(f"[{datetime.now(timezone.utc).isoformat()}]  ERR  {upstream_url}  {err.reason}")
            self._send_json_error(502, f"Upstream connection failed: {err.reason}")

        except TimeoutError:
            print(f"[{datetime.now(timezone.utc).isoformat()}]  TIMEOUT  {upstream_url}")
            self._send_json_error(504, "Upstream request timed out")

# ---------------------------------------------------------------------------
# Server startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    server = http.server.HTTPServer(("localhost", PORT), ProxyHandler)
    base   = f"http://localhost:{PORT}"

    print()
    print(f"  MLB Stats Proxy  →  {base}")
    print()
    print(f"  GET {base}/health")
    print(f"  GET {base}/mlb/<path>     →  statsapi.mlb.com/api/v1/<path>")
    print(f"  GET {base}/stitch/<path>  →  bdfed.stitch.mlbinfra.com/bdfed/<path>")
    print()
    print("  Examples:")
    print(f'    curl "{base}/health"')
    print(f'    curl "{base}/mlb/schedule?sportId=1&date=2026-04-10&hydrate=team,venue,linescore"')
    print(f'    curl "{base}/mlb/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason"')
    print(f'    curl "{base}/stitch/stats/team?stitch_env=prod&sportId=1&gameType=R&group=hitting&stats=season&season=2026&limit=30"')
    print()
    print("  Press Ctrl+C to stop.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Proxy stopped.")
        server.server_close()
        sys.exit(0)
