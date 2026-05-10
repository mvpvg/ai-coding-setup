#!/usr/bin/env bash
# PostToolUse hook — logs tool result to ~/.claude/audit.log
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
    'event': 'tool_result',
    'tool': data.get('tool_name', ''),
    'exit_code': int(data.get('exit_code', 0)),
}
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(entry, separators=(',', ':')) + chr(10))
" 2>/dev/null || true
exit 0
