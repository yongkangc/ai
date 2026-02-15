# YK AI

Agent skills, CLI tools, and prompts for personal AI workflows.

## Setup

```bash
git clone git@github.com:yongkangc/ai.git ~/github/yongkangc/ai
cd ~/github/yongkangc/ai
./install.sh
```

## What Gets Installed

| Component | Location |
|-----------|----------|
| OpenClaw skills | `~/.openclaw/skills/` |
| Claude Code skills | `~/.claude/skills/` |
| Amp skills | `~/.config/agents/skills/` |

## Structure

```
skills/              # Agent skills (SKILL.md + scripts + references)
prompts/             # Standalone prompts and cursor rules
legacy/              # Old cursor rules (archived)
install.sh           # Install all skills
```

## Available Skills

- **daily-reading-digest** — Daily blog + HN roundup from tracked writers
- **vicki-newsletter-digest** — Weekly Chamath + Sahil Bloom digest for Vicki's FA brand

## Adding New Skills

1. Create `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`)
2. Add optional `scripts/` and `references/` dirs
3. Run `./install.sh`

## Updating

```bash
git pull && ./install.sh
```
