#!/usr/bin/env python3
"""Fetch YouTube video transcript. Outputs plain text or JSON with timestamps."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    # Use [a-zA-Z0-9_-]{11} to match exactly an 11-char video ID
    # instead of greedy [^&\n?#]+ which can capture trailing path segments.
    _ID = r"([a-zA-Z0-9_-]{11})"
    patterns = [
        rf"(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v={_ID}",
        rf"(?:https?://)?(?:www\.)?youtube\.com/embed/{_ID}",
        rf"(?:https?://)?(?:www\.)?youtube\.com/v/{_ID}",
        rf"(?:https?://)?(?:www\.)?youtube\.com/shorts/{_ID}",
        rf"(?:https?://)?(?:www\.)?youtube\.com/live/{_ID}",
        rf"(?:https?://)?youtu\.be/{_ID}",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    # Maybe it's just a bare video ID
    stripped = url.strip().rstrip("/")
    if re.match(r"^[a-zA-Z0-9_-]{11}$", stripped):
        return stripped
    return None


def fetch_video_title(video_id: str) -> str | None:
    """Fetch video title via YouTube oEmbed (no API key needed)."""
    import urllib.request

    url = (
        f"https://www.youtube.com/oembed"
        f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("title")
    except Exception:
        return None


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS or MM:SS."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def fetch_transcript(
    video_id: str, languages: list[str]
) -> dict[str, Any]:
    """Fetch transcript for a YouTube video."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return {
            "success": False,
            "error": (
                "youtube-transcript-api not installed. "
                "Run: pip install youtube-transcript-api"
            ),
        }

    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=languages)
        entries = fetched.to_raw_data()

        segments = []
        for entry in entries:
            segments.append(
                {
                    "text": entry.get("text", ""),
                    "start": entry.get("start", 0),
                    "duration": entry.get("duration", 0),
                }
            )

        total_duration = 0
        if segments:
            last = segments[-1]
            total_duration = last["start"] + last["duration"]

        return {
            "success": True,
            "video_id": video_id,
            "total_segments": len(segments),
            "total_duration_secs": round(total_duration),
            "segments": segments,
        }
    except KeyboardInterrupt:
        raise
    except (OSError, ValueError, RuntimeError) as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        # Catch API-specific exceptions we can't import ahead of time
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube video transcript."
    )
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument(
        "--lang",
        nargs="+",
        default=["en"],
        help="Preferred languages (default: en)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output JSON with timestamps instead of plain text",
    )
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"Error: Could not extract video ID from: {args.url}", file=sys.stderr)
        sys.exit(1)

    result = fetch_transcript(video_id, args.lang)

    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    title = fetch_video_title(video_id)

    if args.output_json:
        output = {
            "video_id": result["video_id"],
            "video_url": f"https://www.youtube.com/watch?v={result['video_id']}",
            "title": title,
            "total_segments": result["total_segments"],
            "total_duration": format_timestamp(result["total_duration_secs"]),
            "total_duration_secs": result["total_duration_secs"],
            "segments": [
                {
                    "timestamp": format_timestamp(s["start"]),
                    "start_secs": round(s["start"], 1),
                    "text": s["text"],
                }
                for s in result["segments"]
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        # Plain text: title header + transcript
        if title:
            print(f"# {title}\n")
        for segment in result["segments"]:
            print(segment["text"])


if __name__ == "__main__":
    main()
