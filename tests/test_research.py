import json
import pytest
from pathlib import Path
from scripts.research import generate_research_brief, parse_research_results


# --- generate_research_brief ---

def test_brief_includes_base_tools():
    stack = {
        "base_tools": {"superpowers": {"source": "marketplace", "id": "superpowers@claude-plugins-official"}},
        "mcp_servers": {},
        "per_project": {},
    }
    brief = generate_research_brief(stack)
    assert "superpowers" in brief
    assert "marketplace" in brief

def test_brief_includes_mcp_tools():
    stack = {
        "base_tools": {},
        "mcp_servers": {"context7": {"source": "npm", "package": "@upstash/context7-mcp"}},
        "per_project": {},
    }
    brief = generate_research_brief(stack)
    assert "context7" in brief
    assert "@upstash/context7-mcp" in brief

def test_brief_includes_output_schema():
    brief = generate_research_brief({})
    assert "schema_version" in brief
    assert '"tools"' in brief
    assert "researched_at" in brief

def test_brief_includes_section_headers():
    stack = {
        "base_tools": {"tool_a": {"source": "npm", "package": "tool-a"}},
        "mcp_servers": {"tool_b": {"source": "pypi", "package": "tool-b"}},
        "per_project": {"tool_c": {"source": "github", "repo": "org/tool-c"}},
    }
    brief = generate_research_brief(stack)
    assert "base_tools" in brief
    assert "mcp_servers" in brief
    assert "per_project" in brief

def test_brief_empty_stack_returns_string():
    brief = generate_research_brief({})
    assert isinstance(brief, str)
    assert "Research Brief" in brief

def test_brief_contains_instructions():
    brief = generate_research_brief({})
    assert "Instructions" in brief
    assert "version" in brief.lower()


# --- parse_research_results ---

def test_parse_results_valid(tmp_path):
    data = {"schema_version": "1", "researched_at": "2026-05-10T00:00:00Z", "tools": []}
    f = tmp_path / "results.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    result = parse_research_results(f)
    assert result["schema_version"] == "1"
    assert result["tools"] == []

def test_parse_results_invalid_json(tmp_path):
    f = tmp_path / "results.json"
    f.write_text("not json {{{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_research_results(f)

def test_parse_results_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_research_results(tmp_path / "nonexistent.json")
