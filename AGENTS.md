# AGENTS.md

## Structure

- `skills/` - Agent skills with SKILL.md + optional scripts + references
- `legacy/` - Archived cursor rules and old configs (kept for reference)
- `install.sh` - Install all skills to OpenClaw, Claude Code, and Amp

## Commands

```bash
./install.sh    # Install all skills
git pull && ./install.sh  # Update
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `daily-reading-digest` | Daily blog roundup from tracked SWE/AI writers + HN top 10 |
| `vicki-newsletter-digest` | Weekly Chamath + Sahil Bloom digest for Vicki's FA brand (Singapore) |
| `publish-chart` | Publish HTML chart/visualization to www.ksgabrieltan.com/charts |

## Adding New Skills

1. Create `skills/<name>/SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: my-skill
   description: What this skill does and when to use it.
   ---
   ```
2. Add `scripts/` for automation, `references/` for docs
3. Run `./install.sh`
4. Commit and push

## Style

- Skills follow the OpenClaw/ClawHub format (SKILL.md frontmatter is required)
- Scripts should be self-contained (no external deps beyond Python stdlib where possible)
- State files go in `~/.openclaw/state/<skill-name>.json`
