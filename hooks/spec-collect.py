#!/usr/bin/env python3
"""PostToolUse note-taker for the SPEC.md system.

Fires after every tool call. If the chat's project dir (payload `cwd`) has a
SPEC.md, append one fact line to ./.spec/pending-<session_id>.jsonl recording
what changed. Does nothing in projects without a SPEC.md (zero footprint).

The trail is APPEND-ONLY and NEVER erased here. /spec advances a separate
line-count marker (./.spec/logged-<sid>); the Stop guard compares against it.
See prep-spec-system.txt.

Edit tools (Edit/Write/NotebookEdit) -> kind="edit" with the NORMALIZED
absolute path (so the guard's in-project check is slash/case/junction-safe).
Shell tools (Bash/PowerShell) -> kind="context" (never force a log; file edits
do). Everything else is ignored.

Reads PostToolUse JSON on stdin. Always exits 0 (never blocks the chain).
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit"}
CONTEXT_TOOLS = {"Bash", "PowerShell"}


def _norm(p: str) -> str:
    try:
        return os.path.normcase(os.path.realpath(p))
    except (OSError, ValueError):
        return os.path.normcase(os.path.abspath(p))


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_name = payload.get("tool_name") or ""
    if tool_name in EDIT_TOOLS:
        kind = "edit"
    elif tool_name in CONTEXT_TOOLS:
        kind = "context"
    else:
        return 0  # read-only / internal tool -> ignore

    session_id = payload.get("session_id")
    if not session_id:
        return 0  # cannot scope safely

    cwd = payload.get("cwd")
    if not cwd:
        return 0  # D9 -- no payload cwd, don't invent one
    try:
        cwd_path = Path(cwd)
    except (OSError, ValueError):
        return 0

    if not (cwd_path / "SPEC.md").is_file():
        return 0  # project hasn't opted in

    tool_input = payload.get("tool_input") or {}
    if kind == "edit":
        target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        target = _norm(target) if target else ""
    else:
        cmd = (tool_input.get("command") or "").replace("\n", " ").strip()
        target = cmd[:120]

    fact = {
        "ts": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": tool_name,
        "kind": kind,
        "target": target,
    }

    try:
        spec_dir = cwd_path / ".spec"
        spec_dir.mkdir(parents=True, exist_ok=True)
        with open(spec_dir / f"pending-{session_id}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(fact, ensure_ascii=False) + "\n")
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
