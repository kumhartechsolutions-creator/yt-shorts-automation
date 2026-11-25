"""Upload locally rendered Shorts directly to YouTube Studio via saved local browser session."""

from __future__ import annotations

import os
import platform
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from auth_youtube import PROFILE_DIR, launch_browser_context
from projects import ShortProject


def upload_video_file(video_path: Path, title: str, description: str) -> str:
    """Upload any local MP4 file to YouTube Studio using the persistent browser_profile session."""
    if not PROFILE_DIR.exists():
        raise RuntimeError("Not signed in yet. Run `python auth_youtube.py` first.")

    headless = platform.system() != "Windows" and not os.getenv("DISPLAY")

    with sync_playwright() as p:
        context = launch_browser_context(p, headless=headless)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded")
        page.wait_for_url("**/channel/**", timeout=60_000)

        # Attach MP4 file (YouTube /upload opens the upload dialog directly; fallback to Create button if needed)
        file_input = page.locator("input[type='file']").first
        try:
            file_input.wait_for(state="attached", timeout=10_000)
        except Exception:
            create_btn = page.locator(
                "#upload-icon, #create-icon, ytcp-button#create-icon, button[aria-label='Create']"
            ).first
            create_btn.click()
            upload_item = page.get_by_text("Upload videos", exact=True)
            if upload_item.count() > 0:
                upload_item.first.click()
            file_input.wait_for(state="attached", timeout=20_000)

        file_input.set_input_files(str(video_path.resolve()))

        # Wait for Details step & fill Title + Description
        title_box = page.locator("#textbox[aria-label*='title' i], #title-textarea #textbox").first
        title_box.wait_for(state="visible", timeout=60_000)
        title_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.type(title[:100])

        desc_box = page.locator("#description-textarea #textbox").first
        desc_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.type(description[:5000])

        # Audience: Not made for kids
        page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").click()

        # Next -> Video elements -> Checks -> Visibility
        for _ in range(3):
            page.locator("#next-button").click()
            page.wait_for_timeout(1000)

        # Select Public & Publish
        page.locator("tp-yt-paper-radio-button[name='PUBLIC']").click()
        page.locator("#done-button").click()

        # Wait for publish confirmation & extract video URL/ID
        link_el = page.locator("a[href*='youtu.be/'], a[href*='youtube.com/shorts/']").first
        link_el.wait_for(state="visible", timeout=120_000)
        href = link_el.get_attribute("href") or ""
        match = re.search(r"(?:youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", href)
        video_id = match.group(1) if match else href
        print(f"Uploaded Short: https://youtube.com/shorts/{video_id}")

        context.close()
        return video_id


def upload_short(video_path: Path, project: ShortProject, gist_url: str) -> str:
    """Upload a queued ShortProject MP4 to YouTube Studio."""
    description = project.description.format(gist_url=gist_url)
    return upload_video_file(video_path, project.title, description)
