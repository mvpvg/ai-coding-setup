#!/usr/bin/env bash
# PreToolUse hook — logs tool call to ~/.claude/audit.log
# Claude Code pipes hook data as JSON on stdin.
python3 -c "
import json, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

log_path = Path.home() / '.claude' / 'audit.log'
log_path.parent.mkdir(parents=True, exist_ok=True)
entry = {
    'ts': datetime.now(timezone.utc).isoformat(),
    'event': 'tool_use',
    'tool': data.get('tool_name', ''),
    'command': str(data.get('tool_input', {}).get('command', '')),
    'cwd': str(data.get('cwd', '')),
}
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(entry, separators=(',', ':')) + chr(10))
" 2>/dev/null || true
exit 0
