#!/usr/bin/env python3
"""Smoke test for auto-stop-block.py — runs the REAL hook against crafted
runbooks and asserts exit codes. 0 = allow stop, 2 = keep running."""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto-stop-block.py")
SESSION = "smoketest-session"
SLUG = "smoke-fix-000000"


def run_case(name, runbook_text, expect_exit, *, write_marker=True, write_runbook=True):
    with tempfile.TemporaryDirectory() as d:
        runs_root = os.path.join(d, "auto-runs")
        run_dir = os.path.join(runs_root, SLUG)
        os.makedirs(run_dir, exist_ok=True)
        if write_marker:
            with open(os.path.join(runs_root, f".session-{SESSION}"), "w", encoding="utf-8") as f:
                f.write(SLUG)
        if write_runbook:
            with open(os.path.join(run_dir, "runbook.txt"), "w", encoding="utf-8") as f:
                f.write(runbook_text)
        payload = json.dumps({"cwd": d, "session_id": SESSION})
        proc = subprocess.run([sys.executable, HOOK], input=payload,
                              capture_output=True, text=True)
        ok = proc.returncode == expect_exit
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: "
              f"got exit {proc.returncode}, expected {expect_exit}")
        return ok


ACTIVE = """RUNBOOK — smoke-fix-000000
Goal:    do the thing
Success: thing exists
Steps:
  1. [IN PROGRESS] do it
        verify: file exists
Status:
  Current step:      1
  Approaches tried:  0
  Refuter:           n/a
"""

DONE_CLEAN = "Status: DONE\nRefuter: clean\n"
DONE_PENDING = "Status: DONE\nRefuter: pending\n"
DONE_NA = "Status: DONE\nRefuter: n/a\n"
DONE_NOFIELD = "Status: DONE\n"
DONE_BLOCKERS = "Status: DONE\nRefuter: 2 BLOCKERs\n"
PARTIAL = "Status: PARTIAL\n"
STUCK = "Status: STUCK\n"
TEMPLATE_ONLY = "Status: DONE | PARTIAL | STUCK\nCurrent step: 1\n"

results = []
# Fix 2 — refuter gate on DONE
results.append(run_case("DONE + Refuter clean -> allow", DONE_CLEAN, 0))
results.append(run_case("DONE + Refuter pending -> BLOCK", DONE_PENDING, 2))
results.append(run_case("DONE + Refuter n/a (machine) -> allow", DONE_NA, 0))
results.append(run_case("DONE + Refuter 2 BLOCKERs -> BLOCK", DONE_BLOCKERS, 2))
results.append(run_case("DONE + no Refuter field -> allow (fail-open)", DONE_NOFIELD, 0))
# Fix 1 — PARTIAL is terminal
results.append(run_case("PARTIAL -> allow (no freeze)", PARTIAL, 0))
# Regressions — existing behavior must still hold
results.append(run_case("STUCK -> allow", STUCK, 0))
results.append(run_case("active runbook -> BLOCK", ACTIVE, 2))
results.append(run_case("no session marker -> allow", ACTIVE, 0, write_marker=False))
# False-positive guard — template line is not a real verdict
results.append(run_case("template-only line -> BLOCK (not a verdict)", TEMPLATE_ONLY, 2))

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
