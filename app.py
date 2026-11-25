"""Desktop control panel for the local Arduino/ESP32 YouTube Shorts automation."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, scrolledtext, simpledialog

from projects import PROJECTS, load_state

BASE_DIR = Path(__file__).parent
PROFILE_DIR = BASE_DIR / "browser_profile"
OUTPUT_DIR = BASE_DIR / "output"


class ShortsAutomationApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Zahid Bashir Young Innovator — Shorts Automation")
        self.geometry("760x580")
        self.configure(bg="#0b101d")
        self.resizable(True, True)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.running = False

        self._build_ui()
        self._refresh_status()
        self.after(100, self._drain_logs)

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg="#0b101d", padx=18, pady=14)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Arduino / ESP32 YouTube Shorts Automation",
            font=("Segoe UI", 16, "bold"),
            fg="#f5f8ff",
            bg="#0b101d",
        ).pack(anchor="w")

        self.status_lbl = tk.Label(
            header,
            text="",
            font=("Segoe UI", 10),
            fg="#00e6ff",
            bg="#0b101d",
        )
        self.status_lbl.pack(anchor="w", pady=(4, 0))

        btn_frame = tk.Frame(self, bg="#0b101d", padx=18, pady=6)
        btn_frame.pack(fill="x")

        buttons = [
            ("1. Install Dependencies", "#1f2d47", self._install_deps),
            ("2. Sign In to YouTube", "#164e63", self._sign_in),
            ("3. Preview Short (Dry Run)", "#263a5e", self._dry_run),
            ("4. Render & Upload Now", "#0f766e", self._run_live),
            ("5. Schedule Daily 8 PM", "#3b2f63", self._schedule_daily),
            ("Upload Custom Video...", "#4b5563", self._upload_custom),
            ("Open Output Folder", "#283044", self._open_output),
        ]

        for idx, (label, color, cmd) in enumerate(buttons):
            b = tk.Button(
                btn_frame,
                text=label,
                command=cmd,
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg=color,
                activebackground="#00b4d8",
                activeforeground="#0b101d",
                relief="flat",
                padx=12,
                pady=10,
                cursor="hand2",
            )
            b.grid(row=idx // 3, column=idx % 3, padx=6, pady=6, sticky="ew")
        for col in range(3):
            btn_frame.columnconfigure(col, weight=1)

        log_frame = tk.Frame(self, bg="#0b101d", padx=18, pady=10)
        log_frame.pack(fill="both", expand=True)

        tk.Label(
            log_frame,
            text="Live Output Log",
            font=("Segoe UI", 10, "bold"),
            fg="#94a3b8",
            bg="#0b101d",
        ).pack(anchor="w", pady=(0, 4))

        self.log_box = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 10),
            bg="#111827",
            fg="#e2e8f0",
            insertbackground="#ffffff",
            relief="flat",
            wrap="word",
        )
        self.log_box.pack(fill="both", expand=True)

    def _refresh_status(self) -> None:
        state = load_state()
        uploaded = set(state.get("uploaded", []))
        next_proj = next((p.title for p in PROJECTS if p.id not in uploaded), "Queue empty")
        yt_status = "Saved (browser_profile)" if PROFILE_DIR.exists() else "Not signed in yet"
        self.status_lbl.config(text=f"YouTube Session: {yt_status}   |   Next Short: {next_proj}")

    def _append_log(self, text: str) -> None:
        self.log_box.insert("end", text)
        self.log_box.see("end")

    def _drain_logs(self) -> None:
        while not self.log_queue.empty():
            self._append_log(self.log_queue.get_nowait())
        self.after(100, self._drain_logs)

    def _run_cmd(self, args: list[str], label: str) -> None:
        if self.running:
            self._append_log("\n[Busy] Wait for the current task to finish.\n")
            return
        self.running = True
        self._append_log(f"\n=== {label} ===\n")

        def worker() -> None:
            try:
                env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
                proc = subprocess.Popen(
                    args,
                    cwd=str(BASE_DIR),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    self.log_queue.put(line)
                code = proc.wait()
                self.log_queue.put(f"\n[Finished with exit code {code}]\n")
            except Exception as exc:
                self.log_queue.put(f"\n[Error] {exc}\n")
            finally:
                self.running = False
                self.after(0, self._refresh_status)

        threading.Thread(target=worker, daemon=True).start()

    def _install_deps(self) -> None:
        self._run_cmd([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], "Installing Dependencies")

    def _sign_in(self) -> None:
        self._run_cmd([sys.executable, "auth_youtube.py"], "YouTube Studio Sign-In")

    def _dry_run(self) -> None:
        self._run_cmd([sys.executable, "run_daily.py", "--dry-run"], "Rendering Short (Dry Run)")

    def _run_live(self) -> None:
        self._run_cmd([sys.executable, "run_daily.py"], "Rendering & Uploading Short")

    def _schedule_daily(self) -> None:
        self._run_cmd(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", "setup_task_scheduler.ps1"],
            "Scheduling Daily 8 PM Task",
        )

    def _upload_custom(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select MP4 Video to Upload",
            filetypes=[("Video files", "*.mp4;*.mov;*.mkv"), ("All files", "*.*")],
        )
        if not file_path:
            return
        title = simpledialog.askstring(
            "Video Title",
            "Enter YouTube title (include #shorts for Shorts):",
            initialvalue=f"{Path(file_path).stem} #shorts",
            parent=self,
        )
        if not title:
            return
        desc = simpledialog.askstring(
            "Video Description",
            "Enter description (optional):",
            initialvalue="Subscribe to Zahid Bashir Young Innovator for daily Arduino & ESP32 projects! #shorts #arduino #esp32",
            parent=self,
        ) or ""
        code = (
            "from pathlib import Path; "
            "from youtube_uploader import upload_video_file; "
            f"upload_video_file(Path({file_path!r}), {title!r}, {desc!r})"
        )
        self._run_cmd([sys.executable, "-c", code], f"Uploading Custom Video: {Path(file_path).name}")

    def _open_output(self) -> None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(OUTPUT_DIR))


if __name__ == "__main__":
    ShortsAutomationApp().mainloop()
