---
name: vicki-newsletter-digest
description: Weekly newsletter digest for Vicki — a Singapore-based financial advisor growing her brand. Pulls Chamath Palihapitiya and Sahil Bloom newsletters, extracts key insights, and reframes them as content angles Vicki can share with her audience. Use when asked for Vicki's digest, newsletter ideas, or content inspiration from thought leaders.
---

# Vicki Newsletter Digest

Produce a Telegram-ready digest for Vicki, a financial advisor in Singapore building her personal brand and adding value to her followers.

## Run the collector script

```bash
python3 ~/.openclaw/skills/vicki-newsletter-digest/scripts/collect_vicki_digest.py --output json
```

Useful flags:

```bash
# Preview without touching state
python3 ~/.openclaw/skills/vicki-newsletter-digest/scripts/collect_vicki_digest.py --output markdown --no-state-update

# Wider lookback for first run / testing
python3 ~/.openclaw/skills/vicki-newsletter-digest/scripts/collect_vicki_digest.py --since-hours 168 --output json
```

State file: `~/.openclaw/state/vicki-newsletter-digest.json`

## Digest workflow

1. Run the script and parse JSON output.
2. For each new post:
   - Read the title and excerpt.
   - If the excerpt is weak or missing, fetch the full URL and write a better summary.
   - Extract 1-2 **key takeaways** relevant to personal finance / wealth building / mindset.
   - Suggest a **content angle** — how Vicki could reframe this for her Singapore audience.
3. Format into one clean Telegram message.

## Output format

```
💡 Vicki's Weekly Digest (YYYY-MM-DD)

📬 New from Chamath
- [Title] — [1-2 sentence summary of the key insight]
  🎯 Content angle: [How Vicki could use this for her audience]
  🔗 [URL]

📬 New from Sahil Bloom
- [Title] — [1-2 sentence summary]
  🎯 Content angle: [Suggestion]
  🔗 [URL]

🇸🇬 Singapore Spin
[1-2 sentences connecting the week's themes to Singapore context — CPF, property, cost of living, local market conditions, etc.]

💬 This Week's Best Quote
"[Standout quote from any of the posts]"
```

## Tone & framing

- Vicki's audience = everyday Singaporeans who want to be smarter with money
- Avoid jargon-heavy VC/tech framing — translate to practical personal finance
- Chamath posts tend toward macro/tech/policy → frame as "what this means for your money"
- Sahil Bloom posts tend toward mental models/habits/growth → frame as "actionable life/money tips"
- Always include a Singapore-specific angle (CPF, HDB, SGD, local investing context)

## Length constraints

- Target 800-1500 characters
- Keep it punchy — Vicki should be able to screenshot and share
- No markdown tables (Telegram)

## Source maintenance

When feeds or sources change, update:
- `references/sources.md`
- `scripts/collect_vicki_digest.py`
