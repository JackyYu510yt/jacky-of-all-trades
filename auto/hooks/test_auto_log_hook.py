#!/usr/bin/env python3
"""Test for the F3 fix (prep-auto-rebuild.txt Phase 4.3): a tool call in a
folder that contains OLD run folders must never be appended to any of them
when the firing session has no marker of its own.

    python test_auto_log_hook.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "auto-log-hook.py"
FAILURES: list[str] = []


def expect(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
    else:
        FAILURES.append(f"{label} :: {detail}")
        print(f"[FAIL] {label} :: {detail}")


def _fire(cwd: Path, session_id: str | None, tool_name: str = "Bash") -> None:
    payload = {
        "session_id": session_id,
        "cwd": str(cwd),
        "tool_name": tool_name,
        "tool_input": {"command": "echo hi"},
    }
    subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                   text=True, capture_output=True, check=False)


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="hook_test_"))
    try:
        # Simulate the exact F3 incident: an OLD run folder that closed
        # long ago, sitting in ./auto-runs/, no session marker for THIS call.
        old_run = scratch / "auto-runs" / "some-old-run-105129"
        old_run.mkdir(parents=True)
        (old_run / "RUN.md").write_text("RUN -- old\n\nGoal: old\n", encoding="utf-8")
        (old_run / "log.txt").write_text("[old content that must not grow]\n", encoding="utf-8")
        before = (old_run / "log.txt").read_text(encoding="utf-8")

        _fire(scratch, session_id=None)          # no session_id at all
        _fire(scratch, session_id="totally-unrelated-session")  # a session with no marker

        after = (old_run / "log.txt").read_text(encoding="utf-8")
        expect("F3: old run folder's log.txt is untouched with no session marker",
               before == after, f"before={before!r} after={after!r}")

        # Positive control: WITH a matching marker + RUN.md, logging DOES fire.
        new_run = scratch / "auto-runs" / "current-run-999999"
        new_run.mkdir(parents=True)
        (new_run / "RUN.md").write_text("RUN -- current\n\nGoal: current\n", encoding="utf-8")
        marker = scratch / "auto-runs" / ".session-real-session-id"
        marker.write_text("current-run-999999\n", encoding="utf-8")

        _fire(scratch, session_id="real-session-id")
        log_path = new_run / "log.txt"
        expect("positive control: a real session marker + RUN.md DOES get a log line",
               log_path.is_file() and log_path.read_text(encoding="utf-8").strip() != "",
               f"log_path.is_file()={log_path.is_file()}")

        # The old run folder must STILL be untouched even after the positive
        # control fired (proves the fix routes by marker, not by "any run exists").
        after2 = (old_run / "log.txt").read_text(encoding="utf-8")
        expect("old run folder remains untouched even once a DIFFERENT session logs",
               before == after2, f"before={before!r} after2={after2!r}")

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
