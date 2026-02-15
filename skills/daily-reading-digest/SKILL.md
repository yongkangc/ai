---
name: daily-reading-digest
description: Create a daily Telegram reading roundup from tracked SWE/AI/entrepreneurship writers (Paul Graham, Vitalik, Chamath, Dwarkesh, Peter Steinberger) plus Hacker News top 10. Use when asked for daily readings, blog digests, HN one-liners, or cron-based morning briefing automation.
---

# Daily Reading Digest

Produce one clean Telegram-ready digest with:
1. New posts since the last run from tracked writers
2. Clear one-line summaries for each new post
3. Hacker News top 10 as concise one-liners

## Run the collector script

```bash
python3 ~/.openclaw/skills/daily-reading-digest/scripts/collect_digest.py --output json
```

Useful flags:

```bash
# Preview without touching state
python3 ~/.openclaw/skills/daily-reading-digest/scripts/collect_digest.py --output markdown --no-state-update

# Reset lookback window for first run / testing
python3 ~/.openclaw/skills/daily-reading-digest/scripts/collect_digest.py --since-hours 72 --output json
```

The script maintains state at:
- `~/.openclaw/state/daily-reading-digest.json`

If state is corrupted or stale, remove it and rerun.

## Digest workflow

1. Run the script and parse JSON.
2. For each `new_posts[]` item:
   - Keep the title and URL.
   - Use the feed excerpt directly if it is clear.
   - If excerpt is weak, fetch the URL and write a better one-line summary.
3. Format HN top stories from `hn_top[]` — each entry MUST include:
   - The rank number
   - Title + short "why it matters" phrase
   - The **full clickable URL** from the `url` field (NOT just the domain)
4. Keep tone factual and compact.
5. Send one Telegram message only (no markdown tables).

## Output format

Use this exact high-level structure:

- `📚 Daily Readings (YYYY-MM-DD)`
- `New posts` section
- `⚡ HN Top 10` section
- `Today’s pick` (one short sentence)

## Length and quality constraints

- Target 1200-2500 characters total (longer is fine to fit all 10 HN links).
- **Every HN story and every new post MUST have its full URL on its own line.** No bare domains.
- If there are no new tracked posts, explicitly say: `No new posts from tracked writers today.`
- Never invent article content. If unsure, mark as `title-only summary`.

## Source maintenance

When feeds or people change, read and update:
- `references/sources.md`
- `scripts/collect_digest.py`
