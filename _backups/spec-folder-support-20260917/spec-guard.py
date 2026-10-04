#!/usr/bin/env python3
"""Stop exit-guard for the SPEC.md system.

Blocks a chat from ending while it has unlogged in-project file edits, so the
reasoning behind each change lands in SPEC.md before context is lost. Mirrors
auto-stop-block.py: exit 2 + stderr blocks; any error fails OPEN (exit 0).

Detection (audit-hardened):
- ./.spec/pending-<sid>.jsonl  append-only fact trail (from spec-collect.py).
- ./.spec/logged-<sid>         durable marker = LINE COUNT consumed so far
                               (monotonic -- no timestamp ambiguity).
- "Unlogged" = any in-project (path under SPEC.md dir, slash/case-safe) EDIT
  fact on a line beyond the marker.

Block message is SELF-SUFFICIENT (never relies on another Stop hook's stderr
surviving). If an /auto run is genuinely active (session marker resolves to a
NON-terminal runbook), the nudge says "log, then continue the runbook".

Deadlock-proof:
- payload stop_hook_active -> release (harness-native loop brake).
- persisted streak counter (~/.claude/state/spec-guard-streak-<sid>.json),
  incremented on block, reset on progress/skip -> auto-release after 3.
- /spec skip marker -> release once.  /exit always works.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

NUDGE_TAG = "[⚙ SPEC-GUARD → Claude · internal nudge, NOT a message to you]"
TERMINAL = re.compile(
    r"(?im)^\s*(?:Status|FINAL\s+VERDICT)\s*:\s*(DONE|STUCK|PARTIAL)\b(.*)$"
)


def _emit(msg: str) -> None:
    """Write to stderr as UTF-8 bytes so the non-ASCII nudge tag can never
    raise UnicodeEncodeError on a cp1252 Windows console (which would crash the
    hook and turn a clean exit-2 block into a stray exit-1)."""
    try:
        sys.stderr.buffer.write(msg.encode("utf-8", "replace"))
        sys.stderr.buffer.flush()
    except Exception:
        try:
            _emit(msg.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def _norm(p: str) -> str:
    try:
        return os.path.normcase(os.path.realpath(p))
    except (OSError, ValueError):
        return os.path.normcase(os.path.abspath(p))


def _in_project(path: str, proj: str) -> bool:
    """True if normalized `path` is under normalized `proj`. The prefix needs a
    trailing separator so C:\\proj does not match C:\\proj-backup."""
    if not path:
        return False
    base = proj if proj.endswith(os.sep) else proj + os.sep
    return path == proj or path.startswith(base)


def _streak_path(session_id: str) -> Path:
    return Path(os.path.expanduser("~")) / ".claude" / "state" / f"spec-guard-streak-{session_id}.json"


def _read_streak(session_id: str) -> int:
    try:
        with open(_streak_path(session_id), encoding="utf-8") as f:
            return int(json.load(f).get("count", 0))
    except Exception:
        return 0


def _write_streak(session_id: str, count: int) -> None:
    try:
        p = _streak_path(session_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"count": count}, f)
    except OSError:
        pass


def _auto_active(cwd: Path, session_id: str) -> bool:
    """True only if an /auto run is genuinely active: the session marker
    resolves to a runbook with NO terminal verdict. A leftover marker alone is
    not 'active' (audit C1)."""
    marker = cwd / "auto-runs" / f".session-{session_id}"
    if not marker.is_file():
        return False
    try:
        slug = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    if not slug:
        return False
    run_dir = cwd / "auto-runs" / slug
    for name in ("RUNBOOK.md", "runbook.txt"):
        rb = run_dir / name
        if rb.is_file():
            try:
                content = rb.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return False
            for m in TERMINAL.finditer(content):
                if "|" not in m.group(2):  # skip template lines listing options
                    return False  # terminal verdict -> not active
            return True  # runbook present, no terminal verdict -> active
    return False  # marker but no runbook yet


def _unlogged_count(cwd: Path, session_id: str) -> int:
    spec_dir = cwd / ".spec"
    trail = spec_dir / f"pending-{session_id}.jsonl"
    if not trail.is_file():
        return 0
    try:
        marker = int((spec_dir / f"logged-{session_id}").read_text(encoding="utf-8").strip())
    except Exception:
        marker = 0
    proj = _norm(str(cwd))
    count = 0
    try:
        with open(trail, encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                if i <= marker:
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    fact = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if fact.get("kind") == "edit" and _in_project(fact.get("target", ""), proj):
                    count += 1
    except OSError:
        return 0
    return count


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    session_id = payload.get("session_id")
    if not session_id:
        return 0

    cwd = payload.get("cwd")
    if not cwd:
        return 0
    try:
        cwd_path = Path(cwd)
    except (OSError, ValueError):
        return 0

    if not (cwd_path / "SPEC.md").is_file():
        return 0  # project hasn't opted in

    skip = cwd_path / ".spec" / f"skip-{session_id}"
    if skip.is_file():
        try:
            skip.unlink()
        except OSError:
            pass
        _write_streak(session_id, 0)
        return 0

    unlogged = _unlogged_count(cwd_path, session_id)
    if unlogged == 0:
        _write_streak(session_id, 0)
        return 0

    streak = _read_streak(session_id) + 1
    if payload.get("stop_hook_active") or streak >= 3:
        _write_streak(session_id, 0)
        _emit(
            f"{NUDGE_TAG}\n"
            f"{unlogged} edit(s) still unlogged, but releasing to avoid trapping "
            f"the chat. Run /spec log when you can to capture the reasoning.\n"
        )
        return 0

    _write_streak(session_id, streak)
    if _auto_active(cwd_path, session_id):
        _emit(
            f"{NUDGE_TAG}\n"
            f"{unlogged} unlogged edit(s); /auto runbook still active.\n"
            f"Run /spec log for the work so far, THEN continue the runbook's next step.\n"
        )
    else:
        _emit(
            f"{NUDGE_TAG}\n"
            f"{unlogged} unlogged edit(s) this session. Run /spec log before ending.\n"
            f"Throwaway session? Run /spec skip to bypass.\n"
        )
    return 2


if __name__ == "__main__":
    sys.exit(main())
