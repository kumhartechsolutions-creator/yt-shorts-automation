"""One-time browser login for YouTube Studio using a persistent local profile (Windows Edge / Linux Chromium)."""

from __future__ import annotations

import platform
from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).parent / "browser_profile"


def launch_browser_context(p, headless: bool = False):
    """Launch persistent browser context using Edge on Windows or Chromium on Linux."""
    kwargs = {
        "user_data_dir": str(PROFILE_DIR),
        "headless": headless,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    }
    if platform.system() == "Windows":
        kwargs["channel"] = "msedge"
    return p.chromium.launch_persistent_context(**kwargs)


def ensure_youtube_login() -> None:
    """Open YouTube Studio so the user can sign in once; session persists in browser_profile."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = launch_browser_context(p, headless=False)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://studio.youtube.com", wait_until="domcontentloaded")
        print("\nSign in to your YouTube account in the browser window that opened.")
        print("Waiting until YouTube Studio loads...")
        page.wait_for_url("**/channel/**", timeout=300_000)
        print("YouTube Studio login saved! Future runs will reuse this session automatically.")
        context.close()


if __name__ == "__main__":
    ensure_youtube_login()
