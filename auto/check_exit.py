#!/usr/bin/env python3
"""check_exit.py -- the gate a run must pass before it may print DONE or STOPPED.

    check_exit.py <ABS project> <path to RUN.md>

Exit 0 = every check passed, the run may report its verdict.
Exit 1 = at least one check failed; stdout lists which, by name, with the
         fix needed -- never a traceback.

prep-auto-rebuild.txt Milestone 2, Phase 2.1. This is the CHECKED half of
the GENERATED/CHECKED/PROMISED ladder: a script refuses the report until the
obligations below are actually met, instead of a skill-file sentence hoping
they will be.

THE RUN.md SCHEMA this checker reads (frozen here since Milestone 4, which
makes /auto actually WRITE this file, has not run yet -- Milestone 2 needs a
format to check against, so this run defines it):

    RUN -- <slug>

    Goal: <one sentence>
    Plan: <path> (sha256: <hex>)

    ## Criteria
    - [ ] <criterion text> | evidence: <pasted proof, or blank/"assumed">
    - [x] <criterion text> | evidence: <pasted proof>
    ...

    ## Findings
    <note.py-shaped entries, or a line starting "no findings --">

    ## Big Lesson
    <ONE sentence -- the same big_lesson: field the global CLAUDE.md capture
    rule already asks note.py findings to lead with (the generalized
    principle a FUTURE, DIFFERENT run would apply -- not this run's specific
    change:, its generalized shadow). This IS that field, just given a home
    in RUN.md before the run ends -- when it's real, it becomes the
    big_lesson: line of whatever finding gets filed, verbatim, not
    re-derived. Write "none this run" when nothing rose to that level.>

    ## Verdict
    Status: RUNNING | DONE | STOPPED

A checkbox is "met" when the line starts `- [x]` (case-insensitive x).
`evidence:` is required text after that marker on the SAME line; blank or
the literal word "assumed" (any case) does not count as evidence.

THE SEVEN CHECKS (each named, each printed by name on failure):

  C1  every criterion marked met (`- [x]`) has a non-empty evidence field
  C2  a criterion whose evidence field says "assumed" is not marked met
  C3  the Findings section is non-empty, OR carries an explicit
      "no findings -- <reason>" line
  C4  this session's row in LANES.md is gone (if LANES.md does not exist at
      all, this check is SKIPPED with a note, never silently passed as if
      verified)
  C5  SPEC.md's generated findings block (spec_tool.py sync-findings, from
      Milestone 1) matches what regenerating it right now would produce --
      i.e. sync-findings actually ran before the verdict was written
  C6  the plan file named in RUN.md's header still exists and its hash
      still matches the hash recorded at the header -- nobody swapped the
      plan file mid-run
  C7  the Big Lesson section exists and is not blank -- either a real
      one-line lesson (the same big_lesson: field, just written in RUN.md
      first), or the explicit "none this run" line. Added 2026-09-10 (user
      directive): a run's single most generalizable lesson is exactly the
      thing that gets lost when only the granular Findings list survives
      -- this makes leaving it out a loud failure, not a
      silent gap.

Each check is independently unit-testable against a deliberately-broken
RUN.md fixture -- see test_check_exit.py in this same folder.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

_AUTO_SKILL_DIR = Path(__file__).resolve().parent
if str(_AUTO_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_AUTO_SKILL_DIR))  # so `import lanes` resolves regardless of caller cwd

CRITERION_RE = re.compile(r"^-\s*\[( |x|X)\]\s*(.+?)\s*\|\s*evidence:\s*(.*)$")
PLAN_LINE_RE = re.compile(r"^Plan:\s*(.+?)\s*\(sha256:\s*([0-9a-f]{8,64})\)\s*$",
                          re.IGNORECASE)
ASSUMED_WORD_RE = re.compile(r"^\s*assumed\s*\.?\s*$", re.IGNORECASE)


class CheckFailure(Exception):
    """One check's failure, carrying its name and the fix needed."""

    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason
        super().__init__(f"{name}: {reason}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_criteria(text: str) -> list[tuple[bool, str, str]]:
    """Return [(met, criterion_text, evidence), ...] from the ## Criteria section."""
    lines = text.splitlines()
    out = []
    in_section = False
    for ln in lines:
        if ln.strip().lower().startswith("## criteria"):
            in_section = True
            continue
        if in_section and ln.strip().startswith("## "):
            break
        if not in_section:
            continue
        m = CRITERION_RE.match(ln.strip())
        if m:
            met = m.group(1).lower() == "x"
            out.append((met, m.group(2), m.group(3)))
    return out


def _findings_section(text: str) -> str:
    lines = text.splitlines()
    out = []
    in_section = False
    for ln in lines:
        if ln.strip().lower().startswith("## findings"):
            in_section = True
            continue
        if in_section and ln.strip().startswith("## "):
            break
        if in_section:
            out.append(ln)
    return "\n".join(out).strip()


def check_c1_c2(criteria: list[tuple[bool, str, str]]) -> None:
    for met, crit, evidence in criteria:
        stripped = evidence.strip()
        if met and not stripped:
            raise CheckFailure("C1", f"criterion marked met with no evidence: {crit!r}")
        if met and ASSUMED_WORD_RE.match(stripped):
            raise CheckFailure("C2", f"criterion marked met on ASSUMED evidence: {crit!r}")


def check_c3(run_text: str) -> None:
    body = _findings_section(run_text)
    if not body:
        raise CheckFailure("C3", "## Findings section is empty -- add findings or a "
                            "'no findings -- <reason>' line")
    if body.strip().lower().startswith("no findings"):
        # explicit reason required after the dash
        if "--" not in body and "-" * 2 not in body:
            raise CheckFailure("C3", "'no findings' line has no reason after it")
        return
    # non-empty and not the explicit no-findings line -- fine, findings are present


def _big_lesson_section(text: str) -> str:
    """The ## Big Lesson section -- same field as note.py's big_lesson:, just
    given a home in RUN.md before the run ends (see the schema docstring)."""
    lines = text.splitlines()
    out = []
    in_section = False
    for ln in lines:
        if ln.strip().lower().startswith("## big lesson"):
            in_section = True
            continue
        if in_section and ln.strip().startswith("## "):
            break
        if in_section:
            out.append(ln)
    return "\n".join(out).strip()


NONE_THIS_RUN_RE = re.compile(r"^\s*none\s+this\s+run\s*\.?\s*$", re.IGNORECASE)


def check_c7(run_text: str) -> None:
    if "## big lesson" not in run_text.lower():
        raise CheckFailure("C7", "RUN.md has no ## Big Lesson section at all -- "
                            "add one sentence, or 'none this run'")
    body = _big_lesson_section(run_text)
    if not body:
        raise CheckFailure("C7", "## Big Lesson section is blank -- write the one "
                            "generalized lesson, or the literal line 'none this run'")
    # "none this run" is legal ONLY as the section's whole content, not buried in
    # a longer line -- that would let a real lesson slip past unwritten.
    if NONE_THIS_RUN_RE.match(body) or body.strip().lower() == "none this run":
        return


def check_c4(proj: Path, session_id: str | None) -> str:
    """Returns a one-line status string; never raises when LANES.md doesn't
    exist at all -- but the caller must print the note, never treat the skip
    as a verified pass.

    FIXED 2026-09-10 (same class of bug as promote.py's release_lanes_row,
    found the same session): this originally checked `proj / "LANES.md"`, a
    per-project path, written before Milestone 3 pinned LANES.md as a GLOBAL
    file (~/.claude/LANES.md, replacing ACTIVE-LANES.md). Routes through
    lanes.py's own read() now, the one place that path is decided."""
    if session_id is None:
        return "C4 SKIPPED -- no session_id supplied to check against"
    try:
        import lanes  # local import: only this check needs it
    except ImportError as exc:
        return f"C4 SKIPPED -- lanes.py not importable ({exc})"
    if not lanes.LANES_PATH.is_file():
        return "C4 SKIPPED -- LANES.md does not exist yet"
    rows = lanes.read(gc=False)  # a check must never mutate state as a side effect
    if any(r[1] == session_id for r in rows):
        raise CheckFailure("C4", f"session {session_id} still has a row in LANES.md")
    return "C4 PASS -- session row absent from LANES.md"


def check_c5(proj: Path) -> str:
    spec = proj / "SPEC.md"
    if not spec.is_file():
        return "C5 SKIPPED -- no SPEC.md in this project"
    spec_tool_dir = Path.home() / ".claude" / "skills" / "spec"
    if str(spec_tool_dir) not in sys.path:
        sys.path.insert(0, str(spec_tool_dir))
    import spec_tool  # local import: only this check needs it

    current = spec_tool._findings_block_body(str(proj))
    content = _read(spec)
    if spec_tool.SYNC_BEGIN not in content or spec_tool.SYNC_END not in content:
        raise CheckFailure("C5", "SPEC.md has no generated findings block at all -- "
                            "run `spec_tool.py sync-findings` before reporting")
    start = content.index(spec_tool.SYNC_BEGIN) + len(spec_tool.SYNC_BEGIN)
    end = content.index(spec_tool.SYNC_END)
    existing = content[start:end].strip("\n")
    if existing != current:
        raise CheckFailure("C5", "SPEC.md's findings block is STALE -- FINDINGS.md has "
                            "changed since the last sync-findings; run it again before "
                            "reporting the verdict")
    return "C5 PASS -- SPEC.md's findings block matches FINDINGS.md right now"


def check_c6(run_text: str) -> str:
    plan_match = None
    for ln in run_text.splitlines():
        m = PLAN_LINE_RE.match(ln.strip())
        if m:
            plan_match = m
            break
    if plan_match is None:
        raise CheckFailure("C6", "RUN.md has no parseable 'Plan: <path> (sha256: <hash>)' line")
    plan_path = Path(plan_match.group(1))
    recorded_hash = plan_match.group(2).lower()
    if not plan_path.is_file():
        raise CheckFailure("C6", f"plan file no longer exists: {plan_path}")
    actual_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    if not actual_hash.startswith(recorded_hash) and recorded_hash != actual_hash[:len(recorded_hash)]:
        raise CheckFailure("C6", f"plan file {plan_path} changed since the run started "
                            f"(recorded {recorded_hash[:12]}..., now {actual_hash[:12]}...)")
    return f"C6 PASS -- plan file unchanged ({plan_path.name})"


def run_all(proj: Path, run_md: Path, session_id: str | None = None) -> tuple[bool, list[str]]:
    """Runs every check. Returns (all_passed, report_lines). Never raises."""
    lines: list[str] = []
    ok = True
    if not run_md.is_file():
        return False, [f"FAIL: cannot check -- RUN.md not found at {run_md}"]
    text = _read(run_md)

    try:
        criteria = _parse_criteria(text)
        check_c1_c2(criteria)
        lines.append(f"C1/C2 PASS -- {sum(1 for m,_,_ in criteria if m)}/{len(criteria)} "
                     f"criteria met, all evidenced, none assumed")
    except CheckFailure as e:
        ok = False
        lines.append(f"FAIL {e.name}: {e.reason}")

    try:
        check_c3(text)
        lines.append("C3 PASS -- findings section present or explicitly empty-with-reason")
    except CheckFailure as e:
        ok = False
        lines.append(f"FAIL {e.name}: {e.reason}")

    try:
        lines.append(check_c4(proj, session_id))
    except CheckFailure as e:
        ok = False
        lines.append(f"FAIL {e.name}: {e.reason}")

    try:
        lines.append(check_c5(proj))
    except CheckFailure as e:
        ok = False
        lines.append(f"FAIL {e.name}: {e.reason}")

    try:
        lines.append(check_c6(text))
    except CheckFailure as e:
        ok = False
        lines.append(f"FAIL {e.name}: {e.reason}")

    try:
        check_c7(text)
        lines.append("C7 PASS -- Big Lesson section present (a lesson, or 'none this run')")
    except CheckFailure as e:
        ok = False
        lines.append(f"FAIL {e.name}: {e.reason}")

    return ok, lines


def _stamp_path(run_md: Path) -> Path:
    return run_md.with_name(run_md.name + ".check_exit_passed")


def write_stamp(run_md: Path, run_text: str) -> Path:
    """Phase 2.2 -- the wiring artifact. Records that check_exit passed against
    THIS EXACT content of RUN.md (content hash, not mtime -- mtime lies across
    filesystems and clock skew). A later reader (a person, or a future check)
    can confirm the verdict was printed only after a matching stamp exists.

    This does NOT make the gate unbypassable -- see the RED-TEAM finding in
    this run's log for why a hard Stop-hook block was considered and rejected.
    It makes the bypass CHEAPLY DETECTABLE after the fact instead of invisible.
    """
    h = hashlib.sha256(run_text.encode("utf-8")).hexdigest()
    stamp = _stamp_path(run_md)
    stamp.write_text(f"sha256: {h}\n", encoding="utf-8")
    return stamp


def stamp_matches(run_md: Path) -> bool:
    stamp = _stamp_path(run_md)
    if not stamp.is_file() or not run_md.is_file():
        return False
    recorded = ""
    for ln in _read(stamp).splitlines():
        if ln.startswith("sha256:"):
            recorded = ln.split(":", 1)[1].strip()
            break
    actual = hashlib.sha256(_read(run_md).encode("utf-8")).hexdigest()
    return recorded == actual


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: check_exit.py <ABS project> <path to RUN.md> [session_id] [--stamp]",
              file=sys.stderr)
        return 2
    do_stamp = "--stamp" in argv
    positional = [a for a in argv if a != "--stamp"]
    proj = Path(positional[0])
    run_md = Path(positional[1])
    session_id = positional[2] if len(positional) > 2 else None
    if not proj.is_absolute():
        print(f"check_exit failed: project path must be ABSOLUTE, got {positional[0]!r}",
              file=sys.stderr)
        return 2
    ok, lines = run_all(proj, run_md, session_id)
    print("\n".join(lines))
    if ok:
        print("\ncheck_exit: ALL CHECKS PASSED -- the verdict may be printed")
        if do_stamp:
            stamp = write_stamp(run_md, _read(run_md))
            print(f"check_exit: stamp written -> {stamp}")
        return 0
    print("\ncheck_exit: REFUSED -- fix the FAIL lines above, then re-run")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
