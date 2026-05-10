import re
from pathlib import Path
from scripts.tolaria_writer import write_decision_note


def test_write_note_creates_file(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "routine update")
    assert path.exists()
    assert path.suffix == ".md"


def test_write_note_in_decisions_subdir(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "routine update")
    assert path.parent.name == "decisions"


def test_write_note_filename_contains_tool_id(tmp_path):
    path = write_decision_note(tmp_path, "context7", "1.0.0", "initial add")
    assert "context7" in path.name


def test_write_note_filename_contains_date(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "update")
    # Format: YYYY-MM-DD-react.md
    assert re.match(r"\d{4}-\d{2}-\d{2}-react\.md", path.name)


def test_write_note_frontmatter(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "update")
    content = path.read_text()
    assert content.startswith("---")
    assert "type: tool-update" in content
    assert "tool: react" in content


def test_write_note_contains_new_version(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "update")
    assert "18.3.0" in path.read_text()


def test_write_note_contains_previous_version(tmp_path):
    path = write_decision_note(
        tmp_path, "react", "18.3.0", "update", previous_version="18.0.0"
    )
    content = path.read_text()
    assert "18.0.0" in content
    assert "18.3.0" in content


def test_write_note_no_previous_version(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "initial add")
    content = path.read_text()
    assert "Previous version" not in content


def test_write_note_contains_reason(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "security patch")
    assert "security patch" in path.read_text()


def test_write_note_contains_details(tmp_path):
    path = write_decision_note(
        tmp_path, "react", "18.3.0", "update", details="Includes concurrent features."
    )
    assert "Includes concurrent features." in path.read_text()


def test_write_note_creates_parent_dirs(tmp_path):
    vault = tmp_path / "deep" / "nested" / "vault"
    path = write_decision_note(vault, "tool", "1.0.0", "test")
    assert path.exists()


def test_write_note_returns_path(tmp_path):
    result = write_decision_note(tmp_path, "tool", "1.0.0", "test")
    assert isinstance(result, Path)
