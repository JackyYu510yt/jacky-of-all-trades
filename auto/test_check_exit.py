#!/usr/bin/env python3
"""Unit tests for check_exit.py -- each check driven by a DELIBERATELY BROKEN
RUN.md fixture (prep-auto-rebuild.txt Phase 2.1: "Each check gets its own unit
test driven by a deliberately broken RUN.md"), plus one all-green fixture that
must pass everything. Run:

    python test_check_exit.py

Exits 0 iff every case behaved as expected; prints which case failed otherwise.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "spec"))
import check_exit  # noqa: E402
import spec_tool    # noqa: E402
import note         # noqa: E402
import lanes        # noqa: E402


def _plan_line(plan_path: Path) -> str:
    h = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    return f"Plan: {plan_path} (sha256: {h})"


def _write_run_md(path: Path, criteria_block: str, findings_block: str, plan_line: str,
                   big_lesson: str = "none this run") -> None:
    path.write_text(
        "RUN -- test-slug\n\n"
        "Goal: test goal\n"
        f"{plan_line}\n\n"
        "## Criteria\n"
        f"{criteria_block}\n\n"
        "## Findings\n"
        f"{findings_block}\n\n"
        "## Big Lesson\n"
        f"{big_lesson}\n\n"
        "## Verdict\n"
        "Status: RUNNING\n",
        encoding="utf-8",
    )


def _fresh_project() -> Path:
    d = Path(tempfile.mkdtemp(prefix="check_exit_test_"))
    return d


FAILURES: list[str] = []


def expect(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
    else:
        FAILURES.append(f"{label} :: {detail}")
        print(f"[FAIL] {label} :: {detail}")


def test_all_green():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: exit code 0, ran `x` on 2026-09-10\n"
            "- [ ] optional thing | evidence:",
            "no findings -- nothing new learned this run",
            _plan_line(plan),
        )
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("all_green: passes with no SPEC.md (C5 SKIPPED)", ok, "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c1_broken_no_evidence():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence:",
            "no findings -- n/a",
            _plan_line(plan),
        )
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C1: met-with-no-evidence is REFUSED", not ok and any("C1" in l for l in lines),
               "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c2_broken_assumed():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: assumed",
            "no findings -- n/a",
            _plan_line(plan),
        )
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C2: met-on-assumed-evidence is REFUSED", not ok and any("C2" in l for l in lines),
               "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c3_broken_empty_findings():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: ran it, exit 0",
            "",
            _plan_line(plan),
        )
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C3: empty findings section with no reason is REFUSED",
               not ok and any("C3" in l for l in lines), "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c4_broken_lanes_row_still_present():
    """C4 reads the GLOBAL lanes.LANES_PATH (fixed 2026-09-10 -- see check_exit.py's
    check_c4 docstring), so this test monkeypatches that path rather than writing a
    per-project LANES.md, the same technique test_lanes.py uses."""
    proj = _fresh_project()
    scratch_lanes = Path(tempfile.mkdtemp(prefix="c4_lanes_"))
    original_path = lanes.LANES_PATH
    try:
        lanes.LANES_PATH = scratch_lanes / "LANES.md"
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        lanes.LANES_PATH.write_text(
            lanes.HEADER + "\n- 2026-09-10T17:00:00 | sess-1 | some/folder | some/files\n",
            encoding="utf-8",
        )
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: ran it",
            "no findings -- n/a",
            _plan_line(plan),
        )
        ok, lines_out = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C4: session row still in LANES.md is REFUSED",
               not ok and any("C4" in l for l in lines_out), "\n".join(lines_out))
    finally:
        lanes.LANES_PATH = original_path
        shutil.rmtree(proj, ignore_errors=True)
        shutil.rmtree(scratch_lanes, ignore_errors=True)


def test_c4_skipped_no_lanes_file():
    proj = _fresh_project()
    scratch_lanes = Path(tempfile.mkdtemp(prefix="c4_lanes_"))
    original_path = lanes.LANES_PATH
    try:
        lanes.LANES_PATH = scratch_lanes / "LANES.md"  # deliberately never created
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: ran it",
            "no findings -- n/a",
            _plan_line(plan),
        )
        ok, lines_out = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C4: no LANES.md at all -- SKIPPED, not silently passed as verified",
               any("C4 SKIPPED" in l for l in lines_out), "\n".join(lines_out))
    finally:
        lanes.LANES_PATH = original_path
        shutil.rmtree(proj, ignore_errors=True)
        shutil.rmtree(scratch_lanes, ignore_errors=True)


def test_c5_broken_stale_spec_block():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        # Write a SPEC.md with a stale (hand-edited) findings block
        spec = proj / "SPEC.md"
        spec.write_text(
            "# SPEC\n\n## What we learned here\n\n"
            f"{spec_tool.SYNC_BEGIN}\nSTALE CONTENT NOT MATCHING SOURCE\n{spec_tool.SYNC_END}\n",
            encoding="utf-8",
        )
        # Give the project a real finding so the live block would differ
        scratch = Path(tempfile.mkdtemp(prefix="finding_src_"))
        try:
            f = scratch / "f.txt"
            f.write_text("change: FINDING: test finding for c5\nwhy: testing\ncontext: test\n"
                         "before: x\nafter: y\n", encoding="utf-8")
            note.cmd_note(str(proj), str(f))
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: ran it",
            "no findings -- n/a",
            _plan_line(plan),
        )
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C5: stale SPEC.md findings block is REFUSED",
               not ok and any("C5" in l for l in lines), "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c6_broken_plan_changed():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the ORIGINAL plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: ran it",
            "no findings -- n/a",
            _plan_line(plan),
        )
        plan.write_text("the plan was SWAPPED mid-run", encoding="utf-8")
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C6: plan file changed after hash was recorded is REFUSED",
               not ok and any("C6" in l for l in lines), "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c6_broken_plan_missing():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: ran it",
            "no findings -- n/a",
            _plan_line(plan),
        )
        plan.unlink()
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C6: plan file deleted after hash was recorded is REFUSED",
               not ok and any("C6" in l for l in lines), "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c7_broken_missing_section():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        # Write RUN.md WITHOUT a ## Big Lesson section at all (older shape).
        run_md.write_text(
            "RUN -- test-slug\n\nGoal: test goal\n"
            f"{_plan_line(plan)}\n\n"
            "## Criteria\n- [x] thing works | evidence: ran it\n\n"
            "## Findings\nno findings -- n/a\n\n"
            "## Verdict\nStatus: RUNNING\n",
            encoding="utf-8",
        )
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C7: RUN.md with no Big Lesson section at all is REFUSED",
               not ok and any("C7" in l for l in lines), "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c7_broken_blank_section():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: ran it",
            "no findings -- n/a",
            _plan_line(plan),
            big_lesson="",
        )
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C7: a blank Big Lesson section is REFUSED",
               not ok and any("C7" in l for l in lines), "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c7_passes_none_this_run():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: ran it",
            "no findings -- n/a",
            _plan_line(plan),
            big_lesson="none this run",
        )
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C7: the literal 'none this run' line PASSES",
               ok and any("C7 PASS" in l for l in lines), "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_c7_passes_real_lesson():
    proj = _fresh_project()
    try:
        plan = proj / "plan.txt"
        plan.write_text("the plan", encoding="utf-8")
        run_md = proj / "RUN.md"
        _write_run_md(
            run_md,
            "- [x] thing works | evidence: ran it",
            "no findings -- n/a",
            _plan_line(plan),
            big_lesson="Any script that reads a per-project path for a file that is "
                        "actually global will pass its own tests and still be wrong.",
        )
        ok, lines = check_exit.run_all(proj, run_md, session_id="sess-1")
        expect("C7: a real one-sentence lesson PASSES",
               ok and any("C7 PASS" in l for l in lines), "\n".join(lines))
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def main() -> int:
    test_all_green()
    test_c1_broken_no_evidence()
    test_c2_broken_assumed()
    test_c3_broken_empty_findings()
    test_c4_broken_lanes_row_still_present()
    test_c4_skipped_no_lanes_file()
    test_c5_broken_stale_spec_block()
    test_c6_broken_plan_changed()
    test_c6_broken_plan_missing()
    test_c7_broken_missing_section()
    test_c7_broken_blank_section()
    test_c7_passes_none_this_run()
    test_c7_passes_real_lesson()
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nALL CASES BEHAVED AS EXPECTED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
