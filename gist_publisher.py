"""Optional GitHub Gist publisher for Arduino/ESP32 project code & wiring."""

from __future__ import annotations

import os
from typing import Optional

import requests

from projects import ShortProject


def publish_gist(project: ShortProject) -> str:
    """Create a public GitHub Gist if GITHUB_TOKEN is set; otherwise reuse/fallback."""
    if project.gist_url:
        return project.gist_url

    token: Optional[str] = os.getenv("GITHUB_TOKEN")
    if not token:
        return "https://github.com/kumhartechsolutions-creator"

    resp = requests.post(
        "https://api.github.com/gists",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        json={
            "description": f"{project.title} | Zahid Bashir Young Innovator",
            "public": True,
            "files": {
                project.code_filename: {"content": project.full_code},
                "WIRING_GUIDE.md": {"content": project.wiring_md},
            },
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["html_url"]
