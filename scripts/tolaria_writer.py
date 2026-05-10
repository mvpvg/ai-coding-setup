"""Write decision notes to Tolaria vault."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path


def write_decision_note(
    vault_path: Path,
    tool_id: str,
    new_version: str,
    reason: str,
    previous_version: str | None = None,
    details: str = "",
) -> Path:
    """Write a tool-update decision note to {vault_path}/decisions/{date}-{tool_id}.md.
    Returns the path written."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    decisions_dir = vault_path / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    note_path = decisions_dir / f"{today}-{tool_id}.md"

    prev_line = f"**Previous version:** {previous_version}  \n" if previous_version is not None else ""
    details_block = f"\n{details}\n" if details else ""

    content = (
        f"---\n"
        f"date: {today}\n"
        f"type: tool-update\n"
        f"tool: {tool_id}\n"
        f"---\n"
        f"\n"
        f"# Tool Update: {tool_id} → {new_version}\n"
        f"\n"
        f"{prev_line}"
        f"**New version:** {new_version}  \n"
        f"**Reason:** {reason}\n"
        f"{details_block}"
    )

    note_path.write_text(content, encoding="utf-8")
    return note_path
