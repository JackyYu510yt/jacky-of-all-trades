"""PostToolUse hook: point-of-need findings lookup.

prep-auto-rebuild.txt Milestone 1, Phase 1.2. Enforces the standing global
CLAUDE.md rule ("before diagnosing ANY misbehaving file, run note.py --for
<path>") mechanically instead of leaving it PROMISED-only. CHECKED rung: a
non-blocking notice, not a gate -- see Phase 1.2's own rung tag.

On the FIRST Edit/Write to a given file in this session, if that file is
named in any live finding (project record or cross-folder index -- same
lookup note.py --for does), print one line naming the finding ids. Silent
on every later touch of the same file this session (a per-session marker
under auto-runs/.findings-notified-<session_id> tracks what has already
fired, one basename per line).

Payload shape (probed via existing hooks before writing this, per Phase 1.2
Step 3 / prep-auto-rebuild.txt): PostToolUse JSON on stdin carries
tool_name, tool_input.file_path, cwd, session_id -- confirmed against
auto-log-hook.py and spec-collect.py, both already live on this box.

Always exits 0 -- a findings notice must never block an edit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

NOTE_PY_DIR = Path.home() / ".claude" / "skills" / "spec"
sys.path.insert(0, str(NOTE_PY_DIR))
import note  # noqa: E402  (path must be set first)

EDIT_TOOLS = {"Edit", "Write"}
MARKER_DIR = Path.home() / ".claude" / "hooks" / "_findings_notified"


def _already_notified(session_id: str, basename: str) -> bool:
    marker = MARKER_DIR / f"{session_id}.txt"
    if not marker.is_file():
        return False
    seen = set(marker.read_text(encoding="utf-8", errors="replace").splitlines())
    return basename in seen


def _mark_notified(session_id: str, basename: str) -> None:
    MARKER_DIR.mkdir(parents=True, exist_ok=True)
    marker = MARKER_DIR / f"{session_id}.txt"
    with open(marker, "a", encoding="utf-8") as f:
        f.write(basename + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_name = payload.get("tool_name") or ""
    if tool_name not in EDIT_TOOLS:
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        return 0

    session_id = payload.get("session_id") or "unknown-session"
    target = Path(file_path)
    if not target.is_absolute():
        return 0  # note.py's own lookup refuses relative paths for the same reason

    basename = target.name
    if _already_notified(session_id, basename):
        return 0
    _mark_notified(session_id, basename)  # mark FIRST -- a lookup error must not re-fire every edit

    try:
        target_r = target.resolve()
    except OSError:
        return 0
    project = note._project_for(target_r)
    if project is None:
        return 0
    try:
        entries = note._read_entries(note._findings_path(project))
    except OSError:
        return 0  # unreadable record: stay silent, never block the edit over it
    needle = basename.lower()
    hits = [e for e in entries
            if not e["retracted_by"] and needle in "\n".join(e["body"]).lower()]
    if not hits:
        return 0

    ids = ", ".join(e["id"] for e in hits[-5:])
    more = f" (+{len(hits) - 5} more)" if len(hits) > 5 else ""
    print(f"[findings] {basename} has {len(hits)} recorded finding(s){more}: {ids} "
          f"-- note.py --for \"{target_r}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
