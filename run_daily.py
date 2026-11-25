"""Daily automation runner: render Arduino/ESP32 Short and upload to YouTube."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from gist_publisher import publish_gist
from projects import get_next_project, mark_project_uploaded
from render_short import render_short_video
from youtube_uploader import upload_short

OUTPUT_DIR = Path(__file__).parent / "output"


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily Arduino/ESP32 YouTube Shorts Automation")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the MP4 locally without uploading to YouTube or updating state.json.",
    )
    args = parser.parse_args()

    project = get_next_project()
    print(f"Selected project: {project.title} ({project.id})")

    gist_url = publish_gist(project)
    print(f"Code & wiring URL: {gist_url}")

    video_path = render_short_video(project, OUTPUT_DIR)
    print(f"Rendered video: {video_path}")

    if args.dry_run:
        print("Dry-run mode enabled: skipping YouTube upload.")
        return

    video_id = upload_short(video_path, project, gist_url)
    mark_project_uploaded(project.id, video_id, gist_url)
    print("Done! State updated in state.json.")


if __name__ == "__main__":
    main()
