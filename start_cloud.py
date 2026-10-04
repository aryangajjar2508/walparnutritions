"""
Walpar OCR — Automated Cloudflare Launcher
==========================================
Run this INSTEAD of run.py to get:
  1. Cloudflare tunnel auto-started
  2. New URL auto-detected & saved
  3. Uvicorn server auto-started
  4. Clean banner with both URLs
"""

import subprocess
import threading
import time
import sys
import re
import os
import socket
import webbrowser
from pathlib import Path

# ──────────────────────────────────────────────
#  Paths
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
CLOUDFLARED  = PROJECT_ROOT / "cloudflared.exe"
URL_FILE     = PROJECT_ROOT / "app" / "data" / "cloudflare_url.txt"
PORT         = 8001

PYTHON       = sys.executable   # same python that's running this script

# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────
def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_free_port(start: int = PORT) -> int:
    for p in range(start, start + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", p))
                return p
        except OSError:
            continue
    return start


def print_banner(local_url: str, cf_url: str | None):
    lines = [
        "",
        "  " + "=" * 62,
        "    WALPAR FORMULA OCR & SCIENTIFIC EVALUATION PLATFORM",
        "  " + "=" * 62,
        f"    ✅  Computer Browser : {local_url}",
        f"    📱  Mobile (Wi-Fi)   : http://{get_local_ip()}:{PORT}",
    ]
    if cf_url:
        lines.append(f"    🌐  Cloudflare HTTPS : {cf_url}")
    else:
        lines.append("    ⚠️   Cloudflare      : Not connected (check cloudflared.exe)")
    lines += [
        "  " + "=" * 62,
        "",
    ]
    print("\n".join(lines))


# ──────────────────────────────────────────────
#  Step 1 — Start cloudflared tunnel
# ──────────────────────────────────────────────
def start_cloudflare_tunnel(port: int) -> str | None:
    """
    Launch cloudflared as a background process.
    Block until the tunnel URL is found in its output or 30 s timeout.
    Returns the HTTPS URL string, or None on failure.
    """
    if not CLOUDFLARED.exists():
        print("[Walpar] cloudflared.exe not found — skipping Cloudflare tunnel.")
        return None

    print(f"[Walpar] Starting Cloudflare tunnel → http://127.0.0.1:{port} …")

    proc = subprocess.Popen(
        [str(CLOUDFLARED), "tunnel", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,    # merge stderr into stdout
        text=True,
        bufsize=1,
    )

    url_found: list[str] = []
    timeout = 45          # seconds to wait
    deadline = time.time() + timeout

    URL_PATTERN = re.compile(r"https://[\w-]+\.trycloudflare\.com")

    def reader():
        for line in proc.stdout:
            line = line.rstrip()
            if os.getenv("CF_DEBUG"):          # optional verbose mode
                print("  [cf]", line)
            m = URL_PATTERN.search(line)
            if m:
                url_found.append(m.group())
                break

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if url_found:
        cf_url = url_found[0]
        # Save to file so the web UI picks it up
        URL_FILE.parent.mkdir(parents=True, exist_ok=True)
        URL_FILE.write_text(cf_url, encoding="utf-8")
        print(f"[Walpar] Cloudflare URL: {cf_url}")
        print(f"[Walpar] Saved → {URL_FILE}")
        return cf_url
    else:
        print("[Walpar] Warning: Cloudflare URL not detected within timeout.")
        # Clear stale URL so the UI falls back to local IP
        if URL_FILE.exists():
            URL_FILE.write_text("", encoding="utf-8")
        return None


# ──────────────────────────────────────────────
#  Step 2 — Start Uvicorn server
# ──────────────────────────────────────────────
def start_server(port: int):
    """Start the FastAPI app via uvicorn in the foreground (blocks until Ctrl+C)."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────
def main():
    port = find_free_port(PORT)

    # 1. Start Cloudflare tunnel (non-blocking background thread)
    cf_url = start_cloudflare_tunnel(port)

    # 2. Print banner
    local_url = f"http://127.0.0.1:{port}"
    print_banner(local_url, cf_url)

    # 3. Open browser
    try:
        webbrowser.open(local_url)
    except Exception:
        pass

    # 4. Start server (blocks here until user presses Ctrl+C)
    start_server(port)


if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)          # ensure relative imports work
    main()
