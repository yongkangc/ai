#!/usr/bin/env python3
"""Collect Chamath + Sahil Bloom newsletter posts for Vicki's weekly digest."""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 20
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

SOURCES: list[dict[str, str]] = [
    {
        "id": "chamath",
        "name": "Chamath Palihapitiya",
        "feed": "https://chamath.substack.com/feed",
    },
    {
        "id": "sahil-bloom",
        "name": "Sahil Bloom",
        "feed": "https://sahilbloom.substack.com/feed",
    },
]


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def tag_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def request_bytes(url: str, timeout: int = DEFAULT_TIMEOUT) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": (
                "application/rss+xml,application/atom+xml,application/xml,text/xml,"
                "text/html;q=0.8,*/*;q=0.5"
            ),
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def request_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> Any:
    return json.loads(request_bytes(url, timeout=timeout).decode("utf-8"))


def first_child_text(node: ET.Element, names: set[str]) -> str | None:
    for child in node:
        if tag_name(child.tag) in names:
            text = (child.text or "").strip()
            if text:
                return text
    return None


def first_child(node: ET.Element, names: set[str]) -> ET.Element | None:
    for child in node:
        if tag_name(child.tag) in names:
            return child
    return None


def parse_datetime(raw: str | None) -> dt.datetime | None:
    if not raw:
        return None
    value = raw.strip()
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
    except Exception:
        pass
    variants = [value]
    if value.endswith("Z"):
        variants.append(value[:-1] + "+00:00")
    for candidate in variants:
        try:
            parsed = dt.datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
        except ValueError:
            continue
    return None


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    value = url.strip()
    if not value:
        return ""
    try:
        parts = urllib.parse.urlsplit(value)
    except ValueError:
        return value
    filtered_query = []
    for key, val in urllib.parse.parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_"):
            continue
        if lowered in {"ref", "source"}:
            continue
        filtered_query.append((key, val))
    return urllib.parse.urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urllib.parse.urlencode(filtered_query, doseq=True),
            parts.fragment,
        )
    )


def clean_excerpt(raw: str | None, max_chars: int = 300) -> str:
    if not raw:
        return ""
    text = html.unescape(raw)
    text = TAG_RE.sub(" ", text)
    text = WS_RE.sub(" ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def parse_rss_entries(root: ET.Element) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    channel = first_child(root, {"channel"})
    if channel is None:
        return entries
    for item in channel:
        if tag_name(item.tag) != "item":
            continue
        title = first_child_text(item, {"title"}) or "(untitled)"
        link = first_child_text(item, {"link"}) or first_child_text(item, {"guid"})
        summary = first_child_text(item, {"description", "summary", "encoded"})
        published_raw = first_child_text(
            item, {"pubDate", "published", "updated", "date"}
        )
        entries.append(
            {
                "title": title,
                "url": normalize_url(link),
                "summary": clean_excerpt(summary),
                "published_at": parse_datetime(published_raw),
            }
        )
    return entries


def parse_atom_entries(root: ET.Element) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in root:
        if tag_name(entry.tag) != "entry":
            continue
        title = first_child_text(entry, {"title"}) or "(untitled)"
        link = ""
        for child in entry:
            if tag_name(child.tag) != "link":
                continue
            href = (child.attrib.get("href") or "").strip()
            rel = (child.attrib.get("rel") or "alternate").strip().lower()
            if href and rel == "alternate":
                link = href
                break
            if href and not link:
                link = href
        summary = first_child_text(entry, {"summary", "content"})
        published_raw = first_child_text(
            entry, {"published", "updated", "created", "date"}
        )
        entries.append(
            {
                "title": title,
                "url": normalize_url(link),
                "summary": clean_excerpt(summary),
                "published_at": parse_datetime(published_raw),
            }
        )
    return entries


def parse_feed(xml_blob: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_blob)
    root_tag = tag_name(root.tag).lower()
    if root_tag in {"rss", "rdf"}:
        return parse_rss_entries(root)
    if root_tag == "feed":
        return parse_atom_entries(root)
    raise ValueError(f"Unsupported feed format: {root_tag}")


def load_state(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def save_state(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def prune_seen(
    observed: list[str], existing: list[str], limit: int = 2500
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for url in observed + existing:
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(url)
        if len(out) >= limit:
            break
    return out


def collect_digest(args: argparse.Namespace) -> dict[str, Any]:
    now = utc_now()
    state_path = pathlib.Path(args.state_file).expanduser()
    state = load_state(state_path)

    last_run = parse_datetime(state.get("last_run"))
    if last_run is not None:
        window_start = last_run - dt.timedelta(hours=args.grace_hours)
    else:
        window_start = now - dt.timedelta(hours=args.since_hours)

    seen_urls = set(state.get("seen_urls", []))
    observed_urls: list[str] = []
    source_results: list[dict[str, Any]] = []
    all_new_posts: list[dict[str, Any]] = []

    for source in SOURCES:
        source_result: dict[str, Any] = {
            "source_id": source["id"],
            "source_name": source["name"],
            "feed": source["feed"],
            "new_posts": [],
            "new_count": 0,
            "fetched_count": 0,
        }
        try:
            entries = parse_feed(request_bytes(source["feed"]))
            entries.sort(
                key=lambda item: item["published_at"]
                or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
                reverse=True,
            )
            source_result["fetched_count"] = len(entries)

            for entry in entries:
                url = entry.get("url") or ""
                if not url:
                    continue
                observed_urls.append(url)
                if url in seen_urls:
                    continue
                published_at: dt.datetime | None = entry.get("published_at")
                is_recent = published_at is None or published_at >= window_start
                seen_urls.add(url)
                if not is_recent:
                    continue
                if len(source_result["new_posts"]) >= args.max_posts_per_source:
                    continue

                post = {
                    "source_id": source["id"],
                    "source_name": source["name"],
                    "title": entry.get("title") or "(untitled)",
                    "url": url,
                    "published_at": (
                        published_at.isoformat() if published_at is not None else None
                    ),
                    "excerpt": entry.get("summary") or "",
                }
                source_result["new_posts"].append(post)
                all_new_posts.append(post)

            source_result["new_count"] = len(source_result["new_posts"])
        except Exception as exc:
            source_result["error"] = str(exc)

        source_results.append(source_result)

    all_new_posts.sort(
        key=lambda post: parse_datetime(post.get("published_at"))
        or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
        reverse=True,
    )

    result = {
        "generated_at": now.isoformat(),
        "window_start": window_start.isoformat(),
        "new_posts_total": len(all_new_posts),
        "new_posts": all_new_posts,
        "sources": source_results,
    }

    if not args.no_state_update:
        updated_state = {
            "last_run": now.isoformat(),
            "seen_urls": prune_seen(observed_urls, state.get("seen_urls", [])),
        }
        save_state(state_path, updated_state)

    return result


def to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    generated_at = parse_datetime(payload.get("generated_at")) or utc_now()
    lines.append(f"Vicki's Newsletter Digest ({generated_at.date().isoformat()})")
    lines.append("")

    new_posts: list[dict[str, Any]] = payload.get("new_posts", [])
    if not new_posts:
        lines.append("No new newsletter posts this period.")
    else:
        # Group by source
        by_source: dict[str, list[dict[str, Any]]] = {}
        for post in new_posts:
            sid = post.get("source_id", "unknown")
            by_source.setdefault(sid, []).append(post)

        for source_id, posts in by_source.items():
            source_name = posts[0].get("source_name", source_id)
            lines.append(f"From {source_name}:")
            for post in posts:
                lines.append(f"  - {post.get('title', '(untitled)')}")
                lines.append(f"    {post.get('url', '')}")
                excerpt = (post.get("excerpt") or "").strip()
                if excerpt:
                    lines.append(f"    {excerpt}")
            lines.append("")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect Chamath + Sahil Bloom newsletters for Vicki's digest."
    )
    parser.add_argument(
        "--state-file",
        default="~/.openclaw/state/vicki-newsletter-digest.json",
        help="Path to JSON state file.",
    )
    parser.add_argument(
        "--since-hours",
        type=float,
        default=168.0,
        help="Lookback window for first run (default: 168h = 7 days).",
    )
    parser.add_argument(
        "--grace-hours",
        type=float,
        default=4.0,
        help="Overlap from last run to catch late updates.",
    )
    parser.add_argument(
        "--max-posts-per-source",
        type=int,
        default=5,
        help="Max posts per source.",
    )
    parser.add_argument(
        "--output",
        choices=["json", "markdown"],
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--no-state-update",
        action="store_true",
        help="Do not persist state.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    payload = collect_digest(args)
    if args.output == "markdown":
        print(to_markdown(payload))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
