#!/usr/bin/env python3
"""
/auto Stop hook — blocks the model from returning control to the user while
THIS chat's /auto runbook is still active.

Behavior:
- Reads JSON from stdin. Uses `cwd` (falls back to os.getcwd()) and
  `session_id` to scope the check to THIS chat's run.
- Looks up ./auto-runs/.session-<session_id> in cwd. The file contains the
  slug for this chat's /auto run. (All /auto artifacts live under
  ./auto-runs/<slug>/; the session marker sits at the auto-runs/ root.)
- If no session marker → exit 0 (allow stop). This chat is not in /auto
  mode; a parallel chat's runbook must not block it.
- If the marker resolves to ./auto-runs/<slug>/runbook.txt OR
  ./auto-runs/<slug>/RUNBOOK.md, check that one runbook only.
- Terminal if the runbook contains Status / FINAL VERDICT: DONE | STUCK,
  or (Pattern 3) a sibling VERDICT_DONE / VERDICT_STUCK file exists →
  exit 0.
- Non-terminal → exit 2 with stderr reason. Model continues from the next
  pending step of ITS OWN runbook.

Escape hatches (no deadlock risk):
- Model can write Status: STUCK to release.
- User can `rm ./auto-runs/.session-<session_id>` to release.
- User can /exit — Stop hooks do not block process exit.

Fails open: any unexpected error → exit 0 (allow stop) so a broken hook
never traps the user.
"""
from __future__ import annotations
import json
import os
import re
import sys


# A real terminal verdict line: "Status: DONE" / "FINAL VERDICT: STUCK" / etc.
# Captures the verdict and the rest of the line so template/placeholder lines
# that list the options with a pipe ("Status: DONE | PARTIAL | STUCK") can be
# skipped — those are not a real verdict.
STATUS_LINE = re.compile(
    r"(?im)^\s*(?:Status|FINAL\s+VERDICT)\s*:\s*(DONE|STUCK|PARTIAL)\b(.*)$"
)
# The runbook's Refuter field — only its first token matters
# (clean | n/a | pending | <n> | round ...).
REFUTER_LINE = re.compile(r"(?im)^\s*Refuter\s*:\s*([A-Za-z0-9/]+)")


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()
    session_id = payload.get("session_id")

    if not session_id:
        return 0  # No session ID → cannot scope safely; allow stop.

    marker = os.path.join(cwd, "auto-runs", f".session-{session_id}")
    if not os.path.isfile(marker):
        return 0  # This chat is not in /auto mode. Allow stop.

    try:
        with open(marker, encoding="utf-8") as f:
            slug = f.read().strip()
    except Exception:
        return 0  # Broken marker → fail open.

    if not slug:
        return 0

    runbook = _resolve_runbook(cwd, slug)
    if runbook is None:
        return 0  # Marker exists but runbook is not yet on disk. Allow stop.

    if _is_terminal(runbook, cwd):
        return 0  # This chat's run is DONE or STUCK.

    step = _current_step(runbook)
    sys.stderr.write(
        f"/auto runbook still active for this chat:\n"
        f"  - {os.path.relpath(runbook, cwd)} (current step {step})\n\n"
        "Continue the autonomous run: re-read the runbook, execute its "
        "next non-DONE non-PARKED step, verify the check, advance. Do NOT "
        "return control to the user until this runbook's Status reads "
        "DONE or STUCK (or, for Pattern 3, the matching "
        "auto-runs/<slug>/VERDICT_DONE | VERDICT_STUCK file exists). "
        "The /auto skill's 'Auto Does NOT Waive' invariants still apply.\n"
    )
    return 2


def _resolve_runbook(cwd: str, slug: str) -> str | None:
    """Return the runbook path for an explicit slug, or None if neither
    Pattern-3 nor Pattern-1/2 file exists yet."""
    run_dir = os.path.join(cwd, "auto-runs", slug)
    pattern3 = os.path.join(run_dir, "RUNBOOK.md")
    if os.path.isfile(pattern3):
        return pattern3
    pattern12 = os.path.join(run_dir, "runbook.txt")
    if os.path.isfile(pattern12):
        return pattern12
    return None


def _is_terminal(runbook_path: str, cwd: str) -> bool:
    """A runbook is terminal if (a) for Pattern 3, the sibling auto-<slug>/
    folder has a VERDICT_DONE/VERDICT_STUCK file, or (b) its Status /
    FINAL VERDICT line reads DONE, STUCK, or PARTIAL — with one guard:
    a DONE verdict is only honored once the Refuter field reads clean/n/a
    (a judgment-based goal must clear the Terminal Refuter Gate before DONE
    can stop the run). STUCK and PARTIAL are honest stops and need no gate."""
    # Pattern-3 marker check: VERDICT files live next to RUNBOOK.md
    parent = os.path.dirname(runbook_path)
    if parent and parent != cwd:
        if os.path.isfile(os.path.join(parent, "VERDICT_DONE")) or \
           os.path.isfile(os.path.join(parent, "VERDICT_STUCK")):
            return True

    try:
        with open(runbook_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        # Can't read → treat as terminal so a broken file doesn't deadlock.
        return True

    verdict = _terminal_verdict(content)
    if verdict is None:
        return False  # no real verdict line yet → run still active
    if verdict == "DONE" and not _refuter_clear(content):
        return False  # DONE written but refuter not clear → keep running
    return True


def _terminal_verdict(content: str) -> str | None:
    """Return DONE/STUCK/PARTIAL from a real verdict line, skipping template
    lines that list the options with a pipe (e.g. 'Status: DONE | PARTIAL')."""
    for m in STATUS_LINE.finditer(content):
        verdict, rest = m.group(1).upper(), m.group(2)
        if "|" in rest:
            continue  # placeholder/template line, not a real verdict
        return verdict
    return None


def _refuter_clear(content: str) -> bool:
    """A DONE verdict is honored only if the Refuter field reads clean or n/a.
    Absent field → cannot enforce, fail open (allow). Any other value
    (pending / a BLOCKER count / round marker) → not clear, keep running."""
    m = REFUTER_LINE.search(content)
    if not m:
        return True  # field not present → cannot enforce; allow stop
    return m.group(1).strip().lower() in ("clean", "n/a")


def _current_step(runbook_path: str) -> str:
    try:
        with open(runbook_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return "?"
    m = re.search(r"Current step:\s*(\d+)", content)
    return m.group(1) if m else "?"


if __name__ == "__main__":
    sys.exit(main())
