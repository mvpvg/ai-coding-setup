import pytest
from scripts.update_stack import ToolDiff, classify_tier, compute_diff


# --- classify_tier ---

def test_classify_tier_breaking_on_breaking_changes():
    tool = {"breaking_changes_since_pinned": ["Removed X"], "deprecation_status": "active",
            "security_advisories": [], "notes": ""}
    assert classify_tier(tool) == "breaking"


def test_classify_tier_breaking_on_deprecated():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "deprecated",
            "security_advisories": [], "notes": ""}
    assert classify_tier(tool) == "breaking"


def test_classify_tier_breaking_on_archived():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "archived",
            "security_advisories": [], "notes": ""}
    assert classify_tier(tool) == "breaking"


def test_classify_tier_breaking_on_security_advisories():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "active",
            "security_advisories": ["CVE-2026-0001"], "notes": ""}
    assert classify_tier(tool) == "breaking"


def test_classify_tier_review_on_notes():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "active",
            "security_advisories": [], "notes": "API changed slightly"}
    assert classify_tier(tool) == "review"


def test_classify_tier_safe_by_default():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "active",
            "security_advisories": [], "notes": ""}
    assert classify_tier(tool) == "safe"


def test_classify_tier_breaking_takes_priority_over_notes():
    tool = {"breaking_changes_since_pinned": ["Removed X"], "deprecation_status": "active",
            "security_advisories": [], "notes": "Some notes too"}
    assert classify_tier(tool) == "breaking"


# --- compute_diff ---

def _make_stack(section="base_tools", pinned_version=None):
    cfg = {"source": "npm", "package": "pkg"}
    if pinned_version is not None:
        cfg["pinned_version"] = pinned_version
    return {section: {"mytool": cfg}, "mcp_servers": {}, "per_project": {}}


def _make_research(tool_id="mytool", version="1.0.0", breaking=None, status="active",
                   advisories=None, notes=""):
    return {
        "tools": [{
            "id": tool_id,
            "current_version": version,
            "breaking_changes_since_pinned": breaking or [],
            "deprecation_status": status,
            "security_advisories": advisories or [],
            "notes": notes,
        }]
    }


def test_compute_diff_new_pinning():
    stack = _make_stack(pinned_version=None)
    research = _make_research(version="1.0.0")
    diffs = compute_diff(stack, research)
    assert len(diffs) == 1
    d = diffs[0]
    assert d.tool_id == "mytool"
    assert d.current_version is None
    assert d.new_version == "1.0.0"
    assert d.section == "base_tools"
    assert d.source == "npm"
    assert d.tier == "safe"


def test_compute_diff_version_change():
    stack = _make_stack(pinned_version="0.9.0")
    research = _make_research(version="1.0.0")
    diffs = compute_diff(stack, research)
    assert len(diffs) == 1
    assert diffs[0].current_version == "0.9.0"
    assert diffs[0].new_version == "1.0.0"


def test_compute_diff_no_change_excluded():
    stack = _make_stack(pinned_version="1.0.0")
    research = _make_research(version="1.0.0")
    assert compute_diff(stack, research) == []


def test_compute_diff_null_version_excluded():
    stack = _make_stack(pinned_version=None)
    research = _make_research(version=None)
    assert compute_diff(stack, research) == []


def test_compute_diff_tool_not_in_stack_excluded():
    stack = {"base_tools": {}, "mcp_servers": {}, "per_project": {}}
    research = _make_research(tool_id="unknown_tool", version="1.0.0")
    assert compute_diff(stack, research) == []


def test_compute_diff_sets_correct_section():
    stack = {"base_tools": {}, "mcp_servers": {"mytool": {"source": "pypi"}}, "per_project": {}}
    research = _make_research(version="1.0.0")
    diffs = compute_diff(stack, research)
    assert diffs[0].section == "mcp_servers"


def test_compute_diff_tier_propagated():
    stack = _make_stack()
    research = _make_research(version="2.0.0", breaking=["Removed X"])
    diffs = compute_diff(stack, research)
    assert diffs[0].tier == "breaking"
    assert diffs[0].breaking_changes == ["Removed X"]


def test_compute_diff_empty_stack_returns_empty():
    assert compute_diff({}, _make_research()) == []


def test_compute_diff_empty_research_returns_empty():
    stack = _make_stack()
    assert compute_diff(stack, {"tools": []}) == []
