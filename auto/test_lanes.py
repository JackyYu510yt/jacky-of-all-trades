#!/usr/bin/env python3
"""Unit tests for lanes.py -- claim/release/read + the self-expiry rule.

Monkeypatches lanes.LANES_PATH to a scratch file for the whole run, so this
never touches the real ~/.claude/LANES.md (which does not exist yet -- M4
hasn't wired /auto to use it).

    python test_lanes.py
"""
from __future__ import annotations

import datetime
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lanes  # noqa: E402

FAILURES: list[str] = []


def expect(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
    else:
        FAILURES.append(f"{label} :: {detail}")
        print(f"[FAIL] {label} :: {detail}")


def _make_marker(folder: Path, session_id: str) -> None:
    (folder / "auto-runs").mkdir(parents=True, exist_ok=True)
    (folder / "auto-runs" / f".session-{session_id}").write_text("slug\n", encoding="utf-8")


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="lanes_test_"))
    lanes.LANES_PATH = scratch / "LANES.md"
    try:
        folder_a = scratch / "project-a"
        folder_b = scratch / "project-b"
        folder_a.mkdir()
        folder_b.mkdir()

        # --- claim + read ---
        _make_marker(folder_a, "sess-a")
        lanes.claim(str(folder_a), "files A", "sess-a")
        rows = lanes.read(gc=True)
        expect("claim: one row appears", len(rows) == 1, str(rows))
        expect("claim: fields in order", rows and rows[0][1] == "sess-a" and
               rows[0][2] == str(folder_a) and rows[0][3] == "files A", str(rows))

        # --- second claim, different session, both survive ---
        _make_marker(folder_b, "sess-b")
        lanes.claim(str(folder_b), "files B", "sess-b")
        rows = lanes.read(gc=True)
        expect("claim #2: both rows survive (no marker expired yet)", len(rows) == 2, str(rows))

        # --- release ---
        removed = lanes.release("sess-a")
        rows = lanes.read(gc=False)
        expect("release: row actually removed", removed and len(rows) == 1, str(rows))
        removed_again = lanes.release("sess-a")
        expect("release: releasing an already-gone row is a legal no-op",
               removed_again is False, str(removed_again))

        # --- self-expiry: marker gone ---
        marker_b = folder_b / "auto-runs" / f".session-sess-b"
        marker_b.unlink()
        rows_before = lanes.read(gc=False)
        expect("pre-check: sess-b row still present before GC", len(rows_before) == 1,
               str(rows_before))
        rows_after = lanes.read(gc=True)
        expect("self-expiry: row with a missing session marker is dropped on read",
               len(rows_after) == 0, str(rows_after))

        # --- self-expiry: aged >24h (marker present, but old timestamp) ---
        folder_c = scratch / "project-c"
        folder_c.mkdir()
        _make_marker(folder_c, "sess-c")
        old_ts = (datetime.datetime.now() - datetime.timedelta(hours=25)).strftime(
            "%Y-%m-%dT%H:%M:%S")
        lanes.LANES_PATH.write_text(
            lanes.HEADER + f"\n- {old_ts} | sess-c | {folder_c} | files C\n", encoding="utf-8")
        rows = lanes.read(gc=True)
        expect("self-expiry: a >24h-old row is dropped even with a live marker",
               len(rows) == 0, str(rows))

        # --- a FRESH row with a live marker survives GC ---
        _make_marker(folder_c, "sess-c2")
        lanes.claim(str(folder_c), "files C2", "sess-c2")
        rows = lanes.read(gc=True)
        expect("a fresh row with a live marker survives self-expiry",
               len(rows) == 1 and rows[0][1] == "sess-c2", str(rows))

        # --- one row per session: claiming twice for the same session replaces, not duplicates ---
        lanes.claim(str(folder_c), "files C2 updated", "sess-c2")
        rows = lanes.read(gc=True)
        expect("re-claiming the same session replaces its row, never duplicates",
               len(rows) == 1 and rows[0][3] == "files C2 updated", str(rows))

    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nALL CASES BEHAVED AS EXPECTED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
