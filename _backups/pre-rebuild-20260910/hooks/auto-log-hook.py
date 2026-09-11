"""PostToolUse hook: auto-append every tool call to ./auto-runs/<slug>/log.txt.

Fires after every tool invocation in claude code. If the chat's CWD has an
active /auto run, append a one-line event to the run's log file.

All of /auto's artifacts live under a single per-run folder
./auto-runs/<slug>/ — runbook, log, notes, and (Pattern 3) the full state
set. The only marker outside a slug folder is ./auto-runs/.session-<id> at
the root, which the hook reads to learn the slug.

Resolution priority (so parallel chats in the same dir do not trample each
other's logs):

1. Session-scoped marker — ./auto-runs/.session-<session_id> exists and
   contains the slug for THIS chat. Hook routes the log line to that slug.
2. Legacy fallback — most recently modified ./auto-runs/*/RUNBOOK.md or
   ./auto-runs/*/runbook.txt in the CWD. Only used when no session marker
   exists.

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


def _paths_for_slug(cwd: Path, slug: str) -> tuple[Path, Path] | None:
    """Resolve (log_path, runbook_path) for an explicit slug.

    Everything lives under ./auto-runs/<slug>/. Tries Pattern 3 layout first
    (RUNBOOK.md → logs/run.log), then Pattern 1/2 (runbook.txt → log.txt).
    Returns None if neither runbook file exists (slug supplied but run hasn't
    written its runbook yet).
    """
    run_dir = cwd / "auto-runs" / slug

    pattern3_runbook = run_dir / "RUNBOOK.md"
    if pattern3_runbook.is_file():
        log_dir = run_dir / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None
        return (log_dir / "run.log", pattern3_runbook)

    pattern12_runbook = run_dir / "runbook.txt"
    if pattern12_runbook.is_file():
        return (run_dir / "log.txt", pattern12_runbook)

    return None


def find_runbook(cwd: Path, session_id: str | None) -> tuple[Path, Path] | None:
    """Return (log_path, runbook_path) if an active /auto run exists, else None.

    Priority:
    1. Session marker ./auto-runs/.session-<session_id> — contains the slug
       for THIS chat. Guarantees a parallel chat in the same dir cannot
       trample this run's log.
    2. Legacy fallback — most recently modified runbook under ./auto-runs/.
       Only fires when no session marker exists.
    """
    if not cwd.is_dir():
        return None

    # Path 1 — session-scoped marker
    if session_id:
        marker = cwd / "auto-runs" / f".session-{session_id}"
        if marker.is_file():
            try:
                slug = marker.read_text(encoding="utf-8").strip()
            except OSError:
                slug = ""
            if slug:
                resolved = _paths_for_slug(cwd, slug)
                if resolved is not None:
                    return resolved
                # Marker exists but the runbook isn't on disk yet — skip
                # logging this call rather than fall back to the legacy
                # scan, which could route to a parallel chat's runbook.
                return None

    # Path 2 — legacy fallback (no session marker found): scan ./auto-runs/
    candidates: list[tuple[Path, Path]] = []  # (runbook, log)

    runs_root = cwd / "auto-runs"
    if not runs_root.is_dir():
        return None

    for run_dir in runs_root.iterdir():
        if not run_dir.is_dir():
            continue
        # Pattern 3 — auto-runs/<slug>/RUNBOOK.md
        p3 = run_dir / "RUNBOOK.md"
        if p3.is_file():
            log_dir = run_dir / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            candidates.append((p3, log_dir / "run.log"))
            continue
        # Pattern 1/2 — auto-runs/<slug>/runbook.txt
        p12 = run_dir / "runbook.txt"
        if p12.is_file():
            candidates.append((p12, run_dir / "log.txt"))

    if not candidates:
        return None

    # Pick the most recently modified runbook
    runbook, log = max(candidates, key=lambda c: c[0].stat().st_mtime)
    return (log, runbook)


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
    paths = find_runbook(cwd, session_id)
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
