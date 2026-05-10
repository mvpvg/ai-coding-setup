import json
import pytest
import httpx
from pathlib import Path
from scripts.research import generate_research_brief, parse_research_results, write_validation_log, run_research
from scripts.validate import ValidationResult


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


# --- write_validation_log ---

def test_write_validation_log_creates_file(tmp_path):
    results = [
        ValidationResult(passed=True, tool="react", check="npm_package_exists", details="ok", evidence_url="https://registry.npmjs.org/react"),
        ValidationResult(passed=False, tool="bad", check="url_reachable", details="404", evidence_url="https://github.com/bad"),
    ]
    log_path = tmp_path / "logs" / "validation_log.json"
    write_validation_log(results, log_path)

    assert log_path.exists()
    data = json.loads(log_path.read_text())
    assert len(data) == 2
    assert data[0]["passed"] is True
    assert data[0]["tool"] == "react"
    assert data[1]["passed"] is False

def test_write_validation_log_creates_parent_dirs(tmp_path):
    log_path = tmp_path / "deep" / "nested" / "validation_log.json"
    write_validation_log([], log_path)
    assert log_path.exists()

def test_write_validation_log_empty(tmp_path):
    log_path = tmp_path / "validation_log.json"
    write_validation_log([], log_path)
    data = json.loads(log_path.read_text())
    assert data == []


# --- run_research ---

def _make_results_file(tmp_path, urls=None):
    """Helper: write a minimal valid research_results.json."""
    tool = {
        "id": "mytool",
        "verified": True,
        "current_version": "1.0.0",
        "version_source_url": urls[0] if urls else None,
        "install_method": "npm install mytool",
        "install_method_source_url": urls[1] if urls and len(urls) > 1 else None,
        "checksum_sha256": None,
        "checksum_source_url": None,
        "breaking_changes_since_pinned": [],
        "deprecation_status": "active",
        "security_advisories": [],
        "conflicts_with": [],
        "notes": "",
    }
    data = {"schema_version": "1", "researched_at": "2026-05-10T00:00:00Z", "tools": [tool]}
    f = tmp_path / "research_results.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f

def test_run_research_all_pass(tmp_path):
    def handler(req):
        return httpx.Response(200)

    results_path = _make_results_file(
        tmp_path,
        urls=["https://github.com/owner/repo", "https://github.com/owner/repo#readme"],
    )
    log_path = tmp_path / "validation_log.json"

    all_passed, results = run_research(results_path, log_path, _transport=httpx.MockTransport(handler))

    assert all_passed is True
    assert log_path.exists()
    assert len(results) >= 1

def test_run_research_writes_log_on_url_failure(tmp_path):
    def handler(req):
        return httpx.Response(404)

    results_path = _make_results_file(
        tmp_path,
        urls=["https://github.com/owner/repo", "https://github.com/owner/repo#readme"],
    )
    log_path = tmp_path / "validation_log.json"

    all_passed, results = run_research(results_path, log_path, _transport=httpx.MockTransport(handler))

    assert all_passed is False
    assert log_path.exists()
    log_data = json.loads(log_path.read_text())
    assert any(not entry["passed"] for entry in log_data)

def test_run_research_null_urls_pass(tmp_path):
    results_path = _make_results_file(tmp_path, urls=None)
    log_path = tmp_path / "validation_log.json"

    all_passed, results = run_research(results_path, log_path)

    assert all_passed is True

def test_run_research_invalid_json_raises(tmp_path):
    bad_file = tmp_path / "research_results.json"
    bad_file.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        run_research(bad_file, tmp_path / "log.json")

def test_run_research_wrong_schema_version(tmp_path):
    data = {"schema_version": "99", "tools": []}
    f = tmp_path / "research_results.json"
    f.write_text(json.dumps(data), encoding="utf-8")

    all_passed, results = run_research(f, tmp_path / "log.json")

    assert all_passed is False
    assert any("schema_version" in r.check for r in results)
