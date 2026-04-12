"""
IceEdge NHL Proxy Server
========================
Place this file in the SAME FOLDER as index.html.

SETUP (one time — run in VS Code terminal):
    pip install flask flask-cors requests

RUN (every time you want to use the app):
    python proxy.py

Then open http://localhost:5001 in your browser — it will
serve index.html automatically. No need to open the file manually.
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
import sys
import os

app = Flask(__name__)

# Allow ALL origins so the browser can call this from any context
CORS(app, resources={r"/*": {"origins": "*"}})

NHL_BASE = "https://api-web.nhle.com/v1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.nhl.com/",
    "Origin":          "https://www.nhl.com",
}

# ── Serve index.html at the root so you just go to http://localhost:5001 ──────
@app.route("/")
def serve_app():
    """Serve index.html from the same directory as this script."""
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        return send_file(index_path)
    return (
        "<h2 style='font-family:sans-serif;color:#c0392b'>index.html not found</h2>"
        "<p style='font-family:sans-serif'>Make sure index.html is in the same folder as proxy.py</p>"
        f"<p style='font-family:sans-serif;color:#888'>Looking in: {os.path.dirname(os.path.abspath(__file__))}</p>",
        404,
    )


# ── Health check — the app pings this to confirm the proxy is alive ───────────
@app.route("/health")
def health():
    return jsonify({
        "status":    "ok",
        "proxy":     "IceEdge NHL Proxy",
        "nhl_base":  NHL_BASE,
        "index_html": os.path.exists(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
        ),
    })


# ── Forward any /v1/* request straight to the NHL API ─────────────────────────
@app.route("/v1/<path:path>")
def proxy_nhl(path):
    url    = f"{NHL_BASE}/{path}"
    params = dict(request.args)

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        return jsonify(data)

    except requests.exceptions.Timeout:
        print(f"  [TIMEOUT]  {path}")
        return jsonify({"error": "NHL API timed out", "path": path}), 504

    except requests.exceptions.HTTPError as e:
        print(f"  [HTTP ERR] {path} -> {e}")
        return jsonify({"error": str(e), "path": path}), resp.status_code

    except Exception as e:
        print(f"  [ERROR]    {path} -> {e}")
        return jsonify({"error": str(e), "path": path}), 500


# ── Startup ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PORT = 5001

    # Check that index.html is present in the same directory
    here       = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(here, "index.html")
    has_index  = os.path.exists(index_path)

    print()
    print("=" * 60)
    print("  IceEdge NHL Proxy Server")
    print("=" * 60)
    print(f"  Folder:        {here}")
    print(f"  index.html:    {'OK Found' if has_index else 'NOT FOUND - put index.html here!'}")
    print(f"  NHL API:       {NHL_BASE}")
    print()
    print(f"  Open your browser and go to:")
    print(f"    http://localhost:{PORT}")
    print()
    print("  Keep this terminal open while using the app.")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 60)
    print()

    if not has_index:
        print("  WARNING: index.html not found in the same folder.")
        print(f"  Expected location: {index_path}")
        print("  The proxy will still work but you must open index.html manually.")
        print()

    try:
        app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e) or "10048" in str(e):
            print(f"\n  ERROR: Port {PORT} is already in use.")
            print(f"  Another copy of proxy.py may already be running.")
            print(f"  Close it and try again, or kill the process with:")
            print(f"\n  Windows:  netstat -ano | findstr :{PORT}")
            print(f"            Then: taskkill /PID <number> /F")
            print(f"\n  Mac/Linux: lsof -ti:{PORT} | xargs kill")
        else:
            print(f"\n  ERROR: {e}")
        sys.exit(1)
