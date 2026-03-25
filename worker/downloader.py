"""
Downloads audio from a video URL using yt-dlp.
Mirrors the logic in transcribe.py but as an importable function.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


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
        url,
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    files = list(Path(out_dir).glob("audio.*"))
    if not files:
        raise RuntimeError(f"yt-dlp produced no output for URL: {url}")
    return str(files[0])
