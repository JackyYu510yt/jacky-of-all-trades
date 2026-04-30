"""PostToolUse hook: auto-append every tool call to ./auto-log.txt.

Fires after every tool invocation in claude code. If the chat's CWD has an
active /auto run (./auto-runbook.txt OR ./auto/RUNBOOK.md), append a one-line
event to ./auto-log.txt (or ./auto/logs/run.log for Pattern 3).

This converts log-appending from "model discipline" into a harness guarantee.
Even if the assistant forgets to write a log line, this hook captures the
tool call.

Read-only tools (Read, Glob, Grep, ToolSearch, TodoWrite, Skill) are skipped
to keep the log focused on state-changing actions.

Reads the PostToolUse JSON payload on stdin. Always exits 0 (never blocks).
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

# Tools that mutate state — these get logged.
LOGGED_TOOLS = {
    "Bash",
    "Edit",
    "Write",
    "NotebookEdit",
    "PowerShell",
}

# Tools that are read-only or internal — skipped.
SKIPPED_TOOLS = {
    "Read",
    "Glob",
    "Grep",
    "ToolSearch",
    "TodoWrite",
    "Skill",
    "Agent",
    "WebFetch",
    "WebSearch",
}


def find_runbook(cwd: Path) -> tuple[Path, Path] | None:
    """Return (log_path, runbook_path) if an active /auto run exists, else None.

    Pattern 1/2: ./auto-runbook.txt + ./auto-log.txt
    Pattern 3:   ./auto/RUNBOOK.md + ./auto/logs/run.log
    """
    p3_runbook = cwd / "auto" / "RUNBOOK.md"
    if p3_runbook.is_file():
        log_dir = cwd / "auto" / "logs"
        log_dir.mkdir(exist_ok=True)
        return (log_dir / "run.log", p3_runbook)

    p12_runbook = cwd / "auto-runbook.txt"
    if p12_runbook.is_file():
        return (cwd / "auto-log.txt", p12_runbook)

    return None


def summarize_bash(tool_input: dict) -> str:
    cmd = tool_input.get("command", "").strip()
    preview = cmd.replace("\n", " ")
    if len(preview) > 80:
        preview = preview[:77] + "..."
    return f"[Bash] {preview}"


def summarize_edit(tool_input: dict) -> str:
    path = tool_input.get("file_path", "<unknown>")
    return f"[Edit] {path}"


def summarize_write(tool_input: dict) -> str:
    path = tool_input.get("file_path", "<unknown>")
    content = tool_input.get("content", "")
    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    return f"[Write] {path} ({line_count} lines)"


def summarize_notebook_edit(tool_input: dict) -> str:
    path = tool_input.get("notebook_path", "<unknown>")
    return f"[NotebookEdit] {path}"


def summarize_powershell(tool_input: dict) -> str:
    cmd = tool_input.get("command", "").strip()
    preview = cmd.replace("\n", " ")
    if len(preview) > 80:
        preview = preview[:77] + "..."
    return f"[PowerShell] {preview}"


SUMMARIZERS = {
    "Bash": summarize_bash,
    "Edit": summarize_edit,
    "Write": summarize_write,
    "NotebookEdit": summarize_notebook_edit,
    "PowerShell": summarize_powershell,
}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name") or ""
    if not tool_name or tool_name in SKIPPED_TOOLS or tool_name not in LOGGED_TOOLS:
        return 0

    cwd_str = payload.get("cwd") or os.getcwd()
    try:
        cwd = Path(cwd_str).resolve()
    except (OSError, ValueError):
        return 0

    paths = find_runbook(cwd)
    if paths is None:
        return 0

    log_path, _runbook = paths

    tool_input = payload.get("tool_input") or {}
    summarizer = SUMMARIZERS.get(tool_name)
    summary = summarizer(tool_input) if summarizer else f"[{tool_name}]"

    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{timestamp}] [tool] {summary}\n"

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
