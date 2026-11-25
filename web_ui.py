"""Lightweight Web Dashboard for Hostinger KVM 2 (zero extra dependencies)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from projects import PROJECTS, load_state

BASE_DIR = Path(__file__).parent
PROFILE_DIR = BASE_DIR / "browser_profile"

LOG_LOCK = threading.Lock()
LOGS: list[str] = []
IS_RUNNING = False

HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Zahid Shorts Automation</title>
  <style>
    body{font-family:system-ui,sans-serif;background:#0b101d;color:#f5f8ff;margin:0;padding:24px}
    .wrap{max-width:840px;margin:auto}
    .card{background:#111827;border:1px solid #24324d;border-radius:14px;padding:18px;margin-bottom:16px}
    button{background:#0f766e;color:#fff;border:0;border-radius:10px;padding:12px 18px;font-weight:600;cursor:pointer;margin-right:8px}
    button.sec{background:#263a5e}
    pre{background:#070b14;padding:14px;border-radius:10px;height:340px;overflow:auto;font-size:13px;color:#cbd5e1}
  </style>
</head>
<body>
  <div class="wrap">
    <h2>Arduino / ESP32 YouTube Shorts Automation</h2>
    <div class="card">
      <div id="status">Loading...</div><br>
      <button onclick="runTask('live')">Render & Upload Now</button>
      <button class="sec" onclick="runTask('dry')">Preview Short (Dry Run)</button>
    </div>
    <div class="card">
      <strong>Live Logs</strong>
      <pre id="logs"></pre>
    </div>
  </div>
  <script>
    async function refresh(){
      const r = await fetch('/api/status'); const d = await r.json();
      document.getElementById('status').innerText =
        `YouTube Session: ${d.yt} | Next Short: ${d.next} | Busy: ${d.running}`;
      const pre = document.getElementById('logs');
      pre.textContent = d.logs; pre.scrollTop = pre.scrollHeight;
    }
    async function runTask(mode){
      await fetch('/api/run?mode=' + mode, {method:'POST'});
      refresh();
    }
    setInterval(refresh, 1500); refresh();
  </script>
</body>
</html>"""


def _append(line: str) -> None:
    with LOG_LOCK:
        LOGS.append(line)
        if len(LOGS) > 400:
            del LOGS[:100]


def _start_job(args: list[str], label: str) -> bool:
    global IS_RUNNING
    if IS_RUNNING:
        return False
    IS_RUNNING = True
    _append(f"\n=== {label} ===\n")

    def worker() -> None:
        global IS_RUNNING
        try:
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            proc = subprocess.Popen(
                args, cwd=str(BASE_DIR), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                _append(line)
            _append(f"\n[Finished with exit code {proc.wait()}]\n")
        except Exception as exc:
            _append(f"\n[Error] {exc}\n")
        finally:
            IS_RUNNING = False

    threading.Thread(target=worker, daemon=True).start()
    return True


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/status":
            state = load_state()
            done = set(state.get("uploaded", []))
            nxt = next((p.title for p in PROJECTS if p.id not in done), "Queue empty")
            payload = {
                "yt": "Saved" if PROFILE_DIR.exists() else "Not signed in",
                "next": nxt,
                "running": IS_RUNNING,
                "logs": "".join(LOGS),
            }
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))

    def do_POST(self) -> None:
        if self.path.startswith("/api/run"):
            dry = "mode=dry" in self.path
            args = [sys.executable, "run_daily.py"] + (["--dry-run"] if dry else [])
            ok = _start_job(args, "Dry Run" if dry else "Render & Upload")
            self.send_response(200 if ok else 409)
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"Web UI running at http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
