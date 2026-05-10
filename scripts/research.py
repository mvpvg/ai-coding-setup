"""Research brief generation and results validation orchestration."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.config import read_toml
from scripts.validate import validate_research_results, ValidationResult

_RESULTS_SCHEMA_TEMPLATE = """{
  "schema_version": "1",
  "researched_at": "<ISO8601 timestamp — e.g. 2026-05-10T12:00:00Z>",
  "tools": [
    {
      "id": "<tool-id from list below>",
      "verified": true,
      "current_version": "<version string or null>",
      "version_source_url": "<https://... or null>",
      "install_method": "<exact install command or null>",
      "install_method_source_url": "<https://... or null>",
      "checksum_sha256": "<64-char hex or null>",
      "checksum_source_url": "<https://... or null>",
      "breaking_changes_since_pinned": [],
      "deprecation_status": "active",
      "security_advisories": [],
      "conflicts_with": [],
      "notes": ""
    }
  ]
}"""


def generate_research_brief(stack: dict[str, Any]) -> str:
    """Generate a research brief markdown string from parsed stack.toml."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        "# Research Brief — Dev Stack",
        "",
        f"**Generated:** {now}",
        "",
        "## Instructions",
        "",
        "You are researching the current state of tools in this developer's AI coding setup.",
        "For each tool below, find:",
        "- Current stable version and the URL where you confirmed it",
        "- Exact install command and the URL where you confirmed it",
        "- SHA256 checksum for any downloaded binary (null if not applicable)",
        "- Breaking changes since the pinned version (empty list if none or unknown)",
        "- Deprecation status: one of `active`, `deprecated`, `archived`",
        "- Known security advisories (empty list if none)",
        "- Known conflicts with other tools in this stack (empty list if none)",
        "",
        "## Output Format",
        "",
        "Respond with ONLY a JSON code block — no prose before or after:",
        "",
        "```json",
        _RESULTS_SCHEMA_TEMPLATE,
        "```",
        "",
        "Include one entry per tool from the list below.",
        "",
        "## Tools to Research",
        "",
    ]

    _SECTIONS = ("base_tools", "mcp_servers", "per_project")
    for section in _SECTIONS:
        section_tools = stack.get(section, {})
        if not section_tools:
            continue
        lines.append(f"### {section}")
        lines.append("")
        for tool_id, tool_cfg in section_tools.items():
            source = tool_cfg.get("source", "unknown")
            lines.append(f"**{tool_id}** (source: {source})")
            for k, v in tool_cfg.items():
                if k != "source":
                    lines.append(f"  - {k}: {v}")
            lines.append("")

    return "\n".join(lines)


def parse_research_results(path: Path) -> dict[str, Any]:
    """Read and JSON-parse a research_results.json file. Raises ValueError on bad JSON."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e


def write_validation_log(results: list[ValidationResult], output_path: Path) -> None:
    """Write list of ValidationResult to JSON at output_path. Creates parent dirs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "passed": r.passed,
            "tool": r.tool,
            "check": r.check,
            "details": r.details,
            "evidence_url": r.evidence_url,
        }
        for r in results
    ]
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_research(
    results_path: Path,
    log_path: Path,
    *,
    _transport=None,
) -> tuple[bool, list[ValidationResult]]:
    """Parse research_results.json, validate every claim, write validation_log.json.
    Returns (all_passed, results)."""
    data = parse_research_results(results_path)
    results = validate_research_results(data, _transport=_transport)
    write_validation_log(results, log_path)
    all_passed = all(r.passed for r in results)
    return all_passed, results


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Research brief generation and validation")
    sub = parser.add_subparsers(dest="cmd")

    gen_p = sub.add_parser("generate", help="Generate research brief from stack.toml")
    gen_p.add_argument("--stack", default="stack.toml", help="Path to stack.toml")
    gen_p.add_argument("--output", default="research_brief.md", help="Output path for brief")

    val_p = sub.add_parser("validate", help="Validate research_results.json")
    val_p.add_argument("--input", default="research_results.json", help="Path to results JSON")
    val_p.add_argument("--log", default="validation_log.json", help="Path for validation log")

    args = parser.parse_args()

    if args.cmd == "generate":
        stack = read_toml(Path(args.stack))
        brief = generate_research_brief(stack)
        Path(args.output).write_text(brief, encoding="utf-8")
        print(f"Research brief written to {args.output}")
    elif args.cmd == "validate":
        all_passed, results = run_research(Path(args.input), Path(args.log))
        for r in results:
            status = "✓" if r.passed else "✗"
            print(f"  {status} [{r.tool}] {r.check}: {r.details}")
        if all_passed:
            print("\nAll validations passed.")
        else:
            failed = sum(1 for r in results if not r.passed)
            print(f"\n{failed} validation(s) failed. See {args.log} for details.")
            sys.exit(1)
    else:
        parser.print_help()
