#!/usr/bin/env bash
# comsect1 Architecture - Claude Code AIAD Setup
# Installs rules, sub-agent, and skill to ~/.claude/
#
# Usage:
#   bash tooling/claude-code/install.sh
#
# Existing files are backed up as .bak before overwriting.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLAUDE_HOME="${HOME}/.claude"
PLACEHOLDER="{{COMSECT1_ROOT}}"

# Files to install: source (relative to SCRIPT_DIR) -> target (relative to CLAUDE_HOME)
declare -A FILES=(
  ["agents/comsect1-reviewer/AGENT.md"]="agents/comsect1-reviewer/AGENT.md"
  ["skills/comsect1-analyze/SKILL.md"]="skills/comsect1-analyze/SKILL.md"
  ["rules/comsect1.md"]="rules/comsect1.md"
)

echo "comsect1 Architecture - Claude Code AIAD Setup"
echo "================================================"
echo ""
echo "  Repo root:    $REPO_ROOT"
echo "  Claude home:  $CLAUDE_HOME"
echo ""

installed=0
backed_up=0

for src_rel in "${!FILES[@]}"; do
  tgt_rel="${FILES[$src_rel]}"
  src="$SCRIPT_DIR/$src_rel"
  tgt="$CLAUDE_HOME/$tgt_rel"
  tgt_dir="$(dirname "$tgt")"

  # Create target directory if needed
  mkdir -p "$tgt_dir"

  # Backup existing file
  if [ -f "$tgt" ]; then
    cp "$tgt" "${tgt}.bak"
    echo "  [backup]  $tgt -> ${tgt}.bak"
    backed_up=$((backed_up + 1))
  fi

  # Substitute placeholder and write
  sed "s|${PLACEHOLDER}|${REPO_ROOT}|g" "$src" > "$tgt"
  echo "  [install] $tgt"
  installed=$((installed + 1))
done

echo ""
echo "Done."
echo "  Installed: $installed file(s)"
echo "  Backed up: $backed_up file(s)"
echo ""
echo "The installed files reference: $REPO_ROOT/specs/"
echo "Run 'git pull' in the spec repo to get updates — no reinstall needed."
