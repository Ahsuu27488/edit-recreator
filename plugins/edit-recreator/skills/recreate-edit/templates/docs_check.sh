#!/usr/bin/env bash
# Claude Code Stop hook: if source files changed after HANDOFF.md, block the end of the reply ONCE and ask
# for the handoff docs to be updated, so the next session can continue without re-discovering everything.
# Install in .claude/settings.json:
#   {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR/docs_check.sh\""}]}]}}
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[ -f HANDOFF.md ] || exit 0
changed=$(find remotion/src remotion/scripts scripts media -type f -newer HANDOFF.md 2>/dev/null | grep -v '/node_modules/' | head -20)
[ -z "$changed" ] && exit 0
input=$(cat)
echo "$input" | grep -q '"stop_hook_active": *true' && exit 0
{
  echo "Project files changed after HANDOFF.md was last updated:"
  echo "$changed" | sed 's/^/  - /'
  echo "Before finishing: update HANDOFF.md (scene status / what changed), TODO.md and DECISIONS.md."
} >&2
exit 2
