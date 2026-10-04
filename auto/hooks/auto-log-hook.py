"""PostToolUse hook: auto-append every tool call to ./auto-runs/<slug>/log.txt.

Fires after every tool invocation in claude code. If the chat's CWD has an
active /auto run (a session marker naming a slug whose RUN.md exists), append
a one-line event to that run's log file.

All of /auto's artifacts live under a single per-run folder
./auto-runs/<slug>/ — RUN.md + log.txt, nothing else (prep-auto-rebuild.txt
Milestone 4 / "THE FIVE FILES" — the old GOAL.md/BOARD.md/notes.md/
APPROACHES.md/DIGEST.md/PROGRESS.md/runbook.txt/RUNBOOK.md set is retired).
The only marker outside a slug folder is ./auto-runs/.session-<id> at the
root, which the hook reads to learn the slug.

FIXED 2026-09-10 (finding e36e80bf, "F3" in the rebuild charter): this hook
used to fall back to "the most recently modified runbook in ./auto-runs/"
whenever no session marker existed. That fallback is DELETED. It was found
appending an unrelated session's tool calls into a run folder that had
closed 11 days earlier (50,837 bytes of contamination, invisible in source,
obvious in `ls -la`). The fix is structural, not a narrower fallback:

    NO SESSION MARKER => NO LOG LINE. Full stop.

A tool call with nothing to attribute it to is silence, not a guess. This is
the harness-level half of what makes log-appending reliable — the model's
own /auto-time steps still write RUN.md; this hook only ever appends to the
log of the run THIS session's own marker names.

Read-only tools (Read, Glob, Grep, ToolSearch, TodoWrite, Skill, Agent,
WebFetch, WebSearch) are skipped to keep the log focused on state-changing
actions. Reads the PostToolUse JSON payload on stdin. Always exits 0 (never
blocks a tool call over a logging failure).
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


def find_log_path(cwd: Path, session_id: str | None) -> Path | None:
    """Return the log path for THIS session's active run, or None.

    The ONLY path: a session marker (./auto-runs/.session-<session_id>) must
    exist and name a slug whose ./auto-runs/<slug>/RUN.md exists. Anything
    else — no marker, an empty marker, a slug with no RUN.md yet — returns
    None, and the caller logs nothing. There is no scan-and-guess fallback;
    that was the defect (see module docstring, finding e36e80bf).
    """
    if not session_id or not cwd.is_dir():
        return None
    marker = cwd / "auto-runs" / f".session-{session_id}"
    if not marker.is_file():
        return None
    try:
        slug = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not slug:
        return None
    run_dir = cwd / "auto-runs" / slug
    if not (run_dir / "RUN.md").is_file():
        return None
    return run_dir / "log.txt"


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

    session_id = payload.get("session_id")
    log_path = find_log_path(cwd, session_id)
    if log_path is None:
        return 0

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
