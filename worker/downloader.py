"""
Downloads audio from a video URL using yt-dlp.
Mirrors the logic in transcribe.py but as an importable function.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import httpx

from app.config import GRAPH_API_URL, INSTAGRAM_PAGE_ACCESS_TOKEN


def _resolve_cdn_url(url: str) -> str:
    """
    If `url` is a Meta CDN URL (lookaside.fbsbx.com), resolve it to the
    Instagram reel permalink via the Graph API. Otherwise return as-is.
    """
    if "lookaside.fbsbx.com" not in url:
        return url

    qs = parse_qs(urlparse(url).query)
    asset_ids = qs.get("asset_id", [])
    if not asset_ids:
        return url

    asset_id = asset_ids[0]
    resp = httpx.get(
        f"{GRAPH_API_URL}/{asset_id}",
        params={"fields": "permalink_url", "access_token": INSTAGRAM_PAGE_ACCESS_TOKEN},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("permalink_url", url)


def download_audio(url: str, out_dir: str) -> str:
    """
    Download audio from `url` into `out_dir` as an MP3.
    Returns the path to the downloaded file.
    Raises subprocess.CalledProcessError on yt-dlp failure.
    """
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--no-playlist",
        "--output", os.path.join(out_dir, "audio.%(ext)s"),
    ]

    cookies_txt = os.getenv("INSTAGRAM_COOKIES_TXT", "")
    if cookies_txt:
        cookies_path = os.path.join(out_dir, "cookies.txt")
        with open(cookies_path, "w") as f:
            f.write(cookies_txt)
        cmd += ["--cookies", cookies_path]

    url = _resolve_cdn_url(url)
    cmd.append(url)
    subprocess.run(cmd, check=True, capture_output=True)

    files = list(Path(out_dir).glob("audio.*"))
    if not files:
        raise RuntimeError(f"yt-dlp produced no output for URL: {url}")
    return str(files[0])
