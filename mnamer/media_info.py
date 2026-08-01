"""Inspect local media files for technical metadata."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

PROBE_TIMEOUT_SECONDS = 5


def resolution_label(width: int | None, height: int | None) -> str | None:
    """
    Map pixel dimensions to a common label like 1080p.

    Uses width-or-height thresholds so cropped widescreen encodes (e.g. 1920x800)
    still count as 1080p.
    """
    w = width or 0
    h = height or 0
    if w <= 0 and h <= 0:
        return None
    if w >= 3800 or h >= 2100:
        return "2160p"
    if w >= 2500 or h >= 1400:
        return "1440p"
    if w >= 1900 or h >= 1000:
        return "1080p"
    if w >= 1200 or h >= 700:
        return "720p"
    if w >= 1000 or h >= 560:
        return "576p"
    if w >= 700 or h >= 460:
        return "480p"
    if h > 0:
        return f"{h}p"
    return f"{w}p"


def probe_resolution(path: Path | str) -> str | None:
    """
    Detect video resolution from the file via ffprobe.

    Assumes ``path`` already refers to a media file discovered by the crawler.
    Returns None when ffprobe is unavailable or probing fails.
    """
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        completed = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    try:
        payload = json.loads(completed.stdout)
        stream = (payload.get("streams") or [{}])[0]
        width = int(stream["width"]) if stream.get("width") else None
        height = int(stream["height"]) if stream.get("height") else None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return resolution_label(width, height)


def normalize_resolution_token(value: str | None) -> str | None:
    """Normalize guessit screen_size values into the same labels as probing."""
    if not value:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text in {"4k", "uhd", "2160p"}:
        return "2160p"
    match = re.fullmatch(r"(\d{3,4})p", text)
    if match:
        return resolution_label(None, int(match.group(1)))
    return text
