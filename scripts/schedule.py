"""schedule.py — install/uninstall daily audit-log push schedule."""
from __future__ import annotations
import platform
import sys
from pathlib import Path

from rich.console import Console

from scripts.lib.config import read_toml
from scripts.lib.subprocess_safe import run as safe_run

_PLIST_LABEL = "com.devstack.audit.push"
_TASK_NAME = "DevStackAuditPush"


def _launch_agents_dir() -> Path:
    return Path.home() / "Library" / "LaunchAgents"


def render_plist(python_path: str, stack_path: str, working_dir: str, log_path: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
        ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "    <key>Label</key>\n"
        f"    <string>{_PLIST_LABEL}</string>\n"
        "    <key>ProgramArguments</key>\n"
        "    <array>\n"
        f"        <string>{python_path}</string>\n"
        "        <string>-m</string>\n"
        "        <string>scripts.update_stack</string>\n"
        "        <string>--stack</string>\n"
        f"        <string>{stack_path}</string>\n"
        "        <string>audit</string>\n"
        "        <string>push</string>\n"
        "    </array>\n"
        "    <key>WorkingDirectory</key>\n"
        f"    <string>{working_dir}</string>\n"
        "    <key>StartCalendarInterval</key>\n"
        "    <dict>\n"
        "        <key>Hour</key>\n"
        "        <integer>9</integer>\n"
        "        <key>Minute</key>\n"
        "        <integer>0</integer>\n"
        "    </dict>\n"
        "    <key>StandardOutPath</key>\n"
        f"    <string>{log_path}</string>\n"
        "    <key>StandardErrorPath</key>\n"
        f"    <string>{log_path}</string>\n"
        "</dict>\n"
        "</plist>\n"
    )


def render_xml(python_path: str, stack_path: str, working_dir: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-16"?>\n'
        '<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">\n'
        "    <Triggers>\n"
        "        <CalendarTrigger>\n"
        "            <StartBoundary>2026-01-01T09:00:00</StartBoundary>\n"
        "            <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>\n"
        "        </CalendarTrigger>\n"
        "    </Triggers>\n"
        "    <Actions>\n"
        "        <Exec>\n"
        f"            <Command>{python_path}</Command>\n"
        f'            <Arguments>-m scripts.update_stack --stack "{stack_path}" audit push</Arguments>\n'
        f"            <WorkingDirectory>{working_dir}</WorkingDirectory>\n"
        "        </Exec>\n"
        "    </Actions>\n"
        "    <RegistrationInfo>\n"
        f"        <Description>Daily dev-stack audit log push — {_TASK_NAME}</Description>\n"
        "    </RegistrationInfo>\n"
        "</Task>\n"
    )


def install_schedule(stack_path: Path, *, console: Console | None = None) -> None:
    _console = console or Console()
    os_name = platform.system()
    if os_name not in ("Darwin", "Windows"):
        raise RuntimeError(
            f"Scheduling not supported on {os_name} — use macOS or Windows"
        )

    python_path = sys.executable
    working_dir = str(stack_path.parent.resolve())

    if os_name == "Darwin":
        launch_agents = _launch_agents_dir()
        launch_agents.mkdir(parents=True, exist_ok=True)
        plist_path = launch_agents / f"{_PLIST_LABEL}.plist"
        log_path = str(Path.home() / "Library" / "Logs" / "devstack-audit.log")
        plist_path.write_text(
            render_plist(python_path, str(stack_path.resolve()), working_dir, log_path),
            encoding="utf-8",
        )
        safe_run(["launchctl", "load", str(plist_path)], capture_output=True, check=True)
        _console.print(f"Installed: {plist_path}")
    else:
        xml_path = stack_path.parent / f"{_TASK_NAME}.xml"
        xml_path.write_text(
            render_xml(python_path, str(stack_path.resolve()), working_dir),
            encoding="utf-16",
        )
        safe_run(
            ["schtasks", "/Create", "/XML", str(xml_path), "/TN", _TASK_NAME, "/F"],
            capture_output=True,
            check=True,
        )
        xml_path.unlink()
        _console.print(f"Installed: {_TASK_NAME} (Task Scheduler)")


def uninstall_schedule(*, console: Console | None = None) -> None:
    _console = console or Console()
    os_name = platform.system()

    if os_name == "Darwin":
        plist_path = _launch_agents_dir() / f"{_PLIST_LABEL}.plist"
        if not plist_path.exists():
            _console.print("Not installed.")
            return
        safe_run(["launchctl", "unload", str(plist_path)], capture_output=True, check=False)
        plist_path.unlink()
        _console.print("Uninstalled.")
    elif os_name == "Windows":
        result = safe_run(
            ["schtasks", "/Delete", "/TN", _TASK_NAME, "/F"],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            _console.print("Uninstalled.")
        else:
            _console.print("Not installed.")
    else:
        _console.print(f"Scheduling not supported on {os_name}.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage daily audit-log push schedule")
    parser.add_argument("--stack", default="stack.toml", help="Path to stack.toml")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("install", help="Install schedule (launchd on macOS, Task Scheduler on Windows)")
    sub.add_parser("uninstall", help="Remove installed schedule")
    args = parser.parse_args()

    if args.cmd == "install":
        install_schedule(Path(args.stack))
    elif args.cmd == "uninstall":
        uninstall_schedule()
    else:
        parser.print_help()
