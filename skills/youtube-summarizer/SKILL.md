---
name: youtube-summarizer
description: Summarize YouTube videos from their transcript. Use when asked to summarize a YouTube URL, extract key insights from a video, or get a quick rundown of a podcast/talk. Handles all YouTube URL formats including shorts, embeds, and youtu.be links.
---

# YouTube Summarizer

Fetch a YouTube video's transcript and produce a structured summary.

## Step 1: Fetch the transcript

```bash
~/.openclaw/venvs/youtube-summarizer/bin/python ~/.openclaw/skills/youtube-summarizer/scripts/fetch_transcript.py "<youtube_url>"
```

The script outputs the full transcript as plain text to stdout.

### First-time setup (if venv doesn't exist)

```bash
uv venv ~/.openclaw/venvs/youtube-summarizer
uv pip install --python ~/.openclaw/venvs/youtube-summarizer/bin/python youtube-transcript-api
```

### Flags

```bash
YTPY=~/.openclaw/venvs/youtube-summarizer/bin/python
YTSCRIPT=~/.openclaw/skills/youtube-summarizer/scripts/fetch_transcript.py

# Specify language preference (default: en)
$YTPY $YTSCRIPT "<url>" --lang en es fr

# Output as JSON with timestamps
$YTPY $YTSCRIPT "<url>" --json
```

## Step 2: Summarize

After fetching the transcript, produce a summary with this structure:

### Output format

```
🎬 [Video Title if available, otherwise infer from content]

📺 Source: <youtube_url>

## TL;DR
[2-3 sentence overview — what is this video about and why does it matter?]

## Key Insights
- [Insight 1] — [supporting detail or example]
- [Insight 2] — [supporting detail]
- [Continue for all major points — be thorough, 5-15 bullets typical]

## Notable Quotes
- "[Exact or near-exact quote]" — [speaker, context]
- [Include 2-4 standout quotes]

## Actionable Takeaways
- [What can the viewer apply?]
- [Specific recommendations or advice given]

## One-Line Summary
[Single punchy sentence capturing the essence — good for sharing]
```

## Quality rules

- **Be thorough over brief** — capture the full scope of the video's content
- **Use the speaker's language** — preserve their framing, don't over-paraphrase
- **Include specific numbers, names, examples** — not vague generalizations
- **Organize by theme** when the video covers multiple topics
- **Flag uncertainty** — if the transcript is auto-generated and garbled in places, note it
- **No markdown tables** — use bullet lists (Telegram-friendly)
- **Inline links** where relevant: `[text](url)`

## Length guidelines

- Short video (<10 min): 400-800 chars summary
- Medium video (10-30 min): 800-1500 chars
- Long video/podcast (30+ min): 1500-3000 chars
- Always include all sections; scale depth to video length

## Error handling

- If transcript fetch fails: try with `--lang en es` (multi-language fallback)
- If video has no transcript: say so clearly, don't make up content
- If transcript is heavily garbled (auto-generated): note quality and do your best
