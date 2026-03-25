#!/usr/bin/env python3
"""
Transcribe a URL or local audio/video file using faster-whisper.
Audio is downloaded to a temp directory and cleaned up automatically.

Usage:
    python transcribe.py <URL or file path> [--model small] [--language en] [--output file.txt]
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel


def download_audio(url: str, out_dir: str) -> str:
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--output", os.path.join(out_dir, "audio.%(ext)s"),
        url,
    ]
    subprocess.run(cmd, check=True)
    files = list(Path(out_dir).glob("audio.*"))
    if not files:
        raise RuntimeError("yt-dlp did not produce an output file")
    return str(files[0])


def transcribe(path: str, model_size: str, language: str | None, output: str | None):
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(path, language=language)
    print(f"# Detected language: {info.language}", file=sys.stderr)

    lines = []
    for s in segments:
        line = f"[{s.start:.2f} -> {s.end:.2f}] {s.text.strip()}"
        lines.append(line)
        print(line)

    if output:
        Path(output).write_text("\n".join(lines) + "\n")
        print(f"\n# Saved to {output}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe a URL or local file with faster-whisper"
    )
    parser.add_argument("url_or_path", help="URL or local file path")
    parser.add_argument("--model", default="small", help="Whisper model size (default: small)")
    parser.add_argument("--language", default=None, help="Language code, e.g. en, zh (auto-detect if omitted)")
    parser.add_argument("--output", default=None, help="Write transcript to this file")
    args = parser.parse_args()

    is_url = args.url_or_path.startswith("http")

    if is_url:
        with tempfile.TemporaryDirectory() as tmp:
            print(f"# Downloading audio to temp dir...", file=sys.stderr)
            audio_path = download_audio(args.url_or_path, tmp)
            print(f"# Transcribing...", file=sys.stderr)
            transcribe(audio_path, args.model, args.language, args.output)
        # TemporaryDirectory context manager deletes tmp on exit
    else:
        transcribe(args.url_or_path, args.model, args.language, args.output)


if __name__ == "__main__":
    main()
