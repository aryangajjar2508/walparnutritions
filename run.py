import os
import sys
import socket
import webbrowser
import threading
import time

# ── Force UTF-8 output on Windows (prevents charmap errors from OCR special chars) ──
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
# Also set env var so subprocesses (Tesseract) use UTF-8
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_free_port(preferred_port=8000):
    for port in [preferred_port, 8001, 8080, 8081, 8501]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    return 8001

def open_browser(port):
    time.sleep(1.8)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[Walpar OCR] Opening web dashboard in browser: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

if __name__ == "__main__":
    env_port = os.environ.get("PORT")
    if env_port:
        port = int(env_port)
    else:
        port = find_free_port(8000)

    local_ip = get_local_ip()
    banner = f"""
  ==============================================================
    WALPAR FORMULA OCR & SCIENTIFIC EVALUATION PLATFORM
  ==============================================================
    * Listening Port   : {port}
    * Local URL        : http://127.0.0.1:{port}
    * Network URL      : http://{local_ip}:{port}
  ==============================================================
    """
    print(banner)

    # Spawn browser in separate thread only in local desktop environment
    if not os.environ.get("PORT") and not os.environ.get("RENDER"):
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Launch uvicorn listening on all network interfaces
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


