#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "YK AI - Installing skills"
echo "========================="

# Target directories
OPENCLAW_SKILLS_DIR="${HOME}/.openclaw/skills"
CLAUDE_SKILLS_DIR="${HOME}/.claude/skills"
AMP_SKILLS_DIR="${HOME}/.config/agents/skills"

echo ""
echo "Installing skills..."
mkdir -p "$OPENCLAW_SKILLS_DIR" "$CLAUDE_SKILLS_DIR" "$AMP_SKILLS_DIR"

for skill in "$SCRIPT_DIR"/skills/*/; do
    [ -d "$skill" ] || continue
    skill_name=$(basename "$skill")

    # Skip if no SKILL.md
    if [[ ! -f "$skill/SKILL.md" ]]; then
        echo "  SKIP $skill_name (no SKILL.md)"
        continue
    fi

    echo "  -> $skill_name"

    # OpenClaw
    rm -rf "$OPENCLAW_SKILLS_DIR/$skill_name"
    cp -r "$skill" "$OPENCLAW_SKILLS_DIR/$skill_name"

    # Claude Code
    rm -rf "$CLAUDE_SKILLS_DIR/$skill_name"
    cp -r "$skill" "$CLAUDE_SKILLS_DIR/$skill_name"

    # Amp
    rm -rf "$AMP_SKILLS_DIR/$skill_name"
    cp -r "$skill" "$AMP_SKILLS_DIR/$skill_name"
done

echo ""
echo "Installed to:"
echo "  $OPENCLAW_SKILLS_DIR"
echo "  $CLAUDE_SKILLS_DIR"
echo "  $AMP_SKILLS_DIR"
echo ""
echo "Done!"
