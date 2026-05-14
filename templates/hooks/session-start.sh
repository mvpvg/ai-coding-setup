#!/bin/bash
# SessionStart hook — runs at the start of every Claude Code session.
# Surfaces PROJECT.md, ccc index health, and git status.

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

echo "=== Session Start ==="
echo ""

# Detect setup workspace (setup_helpers.py present = ai-coding-setup folder).
# Skip PROJECT.md display there — it contains stale state from previous setup runs.
IS_SETUP_WORKSPACE=false
if [ -f "$PROJECT_DIR/setup_helpers.py" ]; then
    IS_SETUP_WORKSPACE=true
    echo "ℹ️  Setup workspace detected — skipping PROJECT.md (stale setup state)."
    echo ""
fi

# 1. PROJECT.md (skip in setup workspace)
if [ "$IS_SETUP_WORKSPACE" = "false" ] && [ -f "$PROJECT_DIR/PROJECT.md" ]; then
    echo "--- PROJECT.md ---"
    cat "$PROJECT_DIR/PROJECT.md"
    echo ""
fi

# 2. ccc status
if command -v ccc >/dev/null 2>&1; then
    echo "--- ccc status ---"
    ccc status 2>/dev/null || echo "ccc: no index — run 'ccc index .' before first search"
    echo ""
fi

# 3. Git status
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "--- git status ---"
    git -C "$PROJECT_DIR" status --short
    echo ""
fi

echo "=== End Session Start ==="
