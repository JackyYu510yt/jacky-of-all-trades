"""SessionStart hook: surface this folder's findings without being asked.

prep-auto-rebuild.txt Milestone 1, Phase 1.1. GENERATED rung -- this derives
its output from ~/.claude/FINDINGS.md + ~/.claude/UNIVERSAL_FINDINGS.md at
every session start; nothing here is hand-maintained, so it cannot go stale.

Design rules (decided 2026-09-10, see Skills/FINDINGS.md id 7d123949 + the
prep plan's E9-E12):
  R1  Never load finding BODIES -- only ~260-byte global-index LINES.
  R2  Load THIS FOLDER AND EVERYTHING UNDER IT (downward only, never upward).
  R3  Cap at the newest 40 lines across the whole subtree, plus a tail count
      of how many older ones exist.
  R3b Floor of 2 lines per contributing subfolder inside that cap, so one
      recently-active lane cannot erase every quiet one.
  R4  Every `scope: universal` finding travels regardless of folder.

Reads the SessionStart JSON payload on stdin ({"cwd": ..., "session_id": ...,
"hook_event_name": "SessionStart", ...} -- same shape PostToolUse uses,
confirmed via auto-log-hook.py; A1 (does stdout reach context) was confirmed
directly in-session: the /watch plugin's SessionStart hook's stdout appeared
verbatim as a system-reminder in the same transcript this hook was written
in). Prints plain text; SessionStart hook stdout is injected as context.
Always exits 0 -- a findings loader must never block a session from starting.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GLOBAL_INDEX = Path.home() / ".claude" / "FINDINGS.md"
UNIVERSAL_INDEX = Path.home() / ".claude" / "UNIVERSAL_FINDINGS.md"
CAP = 40
FLOOR_PER_SUBFOLDER = 2


def _index_rows(path: Path) -> list[tuple[str, str, str, str]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("- "):
            continue
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) >= 4:
            rows.append((parts[0], parts[1], parts[2], "|".join(parts[3:])))
    return rows


def _under(cwd: Path, project: str) -> bool:
    try:
        return Path(project).resolve() == cwd or Path(project).resolve().is_relative_to(cwd)
    except (OSError, ValueError):
        return False


def _select(rows: list[tuple[str, str, str, str]]) -> tuple[list[tuple[str, str, str, str]], int]:
    """Newest 40 with a floor of 2 per project (R3/R3b). Returns (kept, dropped_count)."""
    if len(rows) <= CAP:
        return rows, 0
    # rows are file order = oldest-first (append-only); newest last.
    by_proj: dict[str, list[tuple[str, str, str, str]]] = {}
    for r in rows:
        by_proj.setdefault(r[1], []).append(r)

    guaranteed: list[tuple[str, str, str, str]] = []
    for proj, items in by_proj.items():
        guaranteed.extend(items[-FLOOR_PER_SUBFOLDER:])

    remaining_slots = CAP - len(guaranteed)
    if remaining_slots < 0:
        # More subfolders than the cap allows even at the floor -- fall back
        # to pure recency rather than going negative (KISS; a machine with
        # >20 quiet subfolders under one cwd is not the case this was sized for).
        newest = sorted(rows, key=lambda r: r[0])[-CAP:]
        return newest, len(rows) - len(newest)

    guaranteed_keys = {(r[1], r[2]) for r in guaranteed}
    pool = [r for r in rows if (r[1], r[2]) not in guaranteed_keys]
    pool_sorted = sorted(pool, key=lambda r: r[0])
    fill = pool_sorted[-remaining_slots:] if remaining_slots else []
    kept = sorted(guaranteed + fill, key=lambda r: r[0])
    return kept, len(rows) - len(kept)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    cwd_str = payload.get("cwd") or "."
    try:
        cwd = Path(cwd_str).resolve()
    except OSError:
        return 0  # never block session start over a bad cwd

    all_rows = _index_rows(GLOBAL_INDEX)
    scoped = [r for r in all_rows if _under(cwd, r[1])]
    kept, dropped = _select(scoped)

    universal_rows = _index_rows(UNIVERSAL_INDEX)
    # Never duplicate a line already surfaced by the folder scope above.
    scoped_keys = {(r[1], r[2]) for r in scoped}
    universal_only = [r for r in universal_rows if (r[1], r[2]) not in scoped_keys]

    if not kept and not universal_only:
        return 0  # nothing to say; stay silent rather than print an empty banner

    lines = [f"Findings on file for this folder ({cwd}) and its subtree:"]
    if kept:
        for ts, proj, eid, summary in kept:
            lines.append(f"  {ts}  {eid}  {summary}")
        if dropped:
            lines.append(f"  ... {dropped} older -- run: python \"%USERPROFILE%/.claude/skills/spec/note.py\" --recent \"{cwd}\"")
    else:
        lines.append("  (none in this subtree)")
    if universal_only:
        lines.append("Universal findings (apply anywhere):")
        for ts, proj, eid, summary in universal_only:
            lines.append(f"  {ts}  {eid}  {summary}")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
