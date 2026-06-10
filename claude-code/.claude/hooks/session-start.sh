#!/bin/bash
# SessionStart hook — runs at the start of every Claude Code session.
# Surfaces PROJECT.md, ccc index health, and git status.

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

echo "=== Session Start ==="
echo ""

# 1. PROJECT.md — the living context doc
if [ -f "$PROJECT_DIR/PROJECT.md" ]; then
    echo "--- PROJECT.md ---"
    cat "$PROJECT_DIR/PROJECT.md"
    echo ""
else
    echo "ℹ️  No PROJECT.md found. Create one from the template if this is a real project."
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
