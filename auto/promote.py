#!/usr/bin/env python3
"""promote.py -- the ONE promotion routine, called from both exit paths.

    python promote.py --dir <ABS project> --path finish|blocker-stop [--session SID]

prep-auto-rebuild.txt Milestone 2, Phase 2.3: "ONE promotion routine, called
from BOTH the finish path and the blocker-stop path. Not two copies."

WHY THIS IS SMALLER THAN THE OLD /auto'S PROMOTION STEP: under the new
design (Milestone 1), findings are written to FINDINGS.md THE MOMENT THEY
LAND, via note.py, mid-run -- not batched up in a notes.md and promoted only
at the end. So there is no backlog of findings to walk at exit; the only
things still owed at exit are:

  1. Regenerate SPEC.md's findings block (spec_tool.py sync-findings) --
     GENERATED rung, so this can never disagree with FINDINGS.md.
  2. Release this session's row from LANES.md, if one exists (Milestone 3
     hasn't built LANES.md yet -- this is forward-compatible: a no-op with
     a printed note today, real once M3 lands).

Both steps are IDEMPOTENT: calling this twice writes nothing new the second
time (sync-findings prints "no change" when the block is already current;
releasing an already-absent LANES.md row is a no-op). This is what makes it
safe to call from BOTH the finish path and the blocker-stop path without
double-booking anything -- a run that stops on a blocker and is later
resumed to a clean finish calls this again with no ill effect.

`--path` is recorded only for the printed report; it changes no behavior.
The whole point of "one routine, not two copies" is that WHICH path called
it must not matter to what it does.
"""
from __future__ import annotations

import sys
from pathlib import Path

SPEC_TOOL_DIR = Path.home() / ".claude" / "skills" / "spec"
if str(SPEC_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(SPEC_TOOL_DIR))
import spec_tool  # noqa: E402

AUTO_SKILL_DIR = Path.home() / ".claude" / "skills" / "auto"
if str(AUTO_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(AUTO_SKILL_DIR))  # so `import lanes` resolves regardless of caller cwd


def release_lanes_row(proj: Path, session_id: str | None) -> str:
    """LANES.md is GLOBAL (~/.claude/LANES.md), not per-project -- fixed
    2026-09-10 after Milestone 3 finalized that design. This function used to
    check `proj / "LANES.md"`, a path nothing ever writes to; the fix routes
    through lanes.py's own release(), the single implementation of this
    operation, so the two milestones' tools can't drift apart again. `proj`
    is unused now but kept in the signature -- callers pass it unconditionally."""
    if session_id is None:
        return "no --session given -- cannot identify which row to release, skipped"
    try:
        import lanes  # local import: only this function needs it
    except ImportError as exc:
        return f"lanes.py not importable ({exc}) -- release skipped, non-fatal"
    removed = lanes.release(session_id)
    return (f"released session {session_id}'s row from LANES.md" if removed
            else f"session {session_id} had no row in LANES.md -- already released (idempotent)")


def promote(proj: Path, path: str, session_id: str | None = None) -> list[str]:
    """The one routine. Returns a list of report lines. Never raises past this
    function -- a promotion step must not crash the exit it is trying to close."""
    report = [f"promote.py: exit path = {path}"]
    try:
        # sync-findings prints its own line; capture it by calling the function
        # directly rather than shelling out, so failures surface as exceptions
        # we can report instead of a silent nonzero subprocess exit.
        spec = spec_tool._spec_path(str(proj))
        if not spec.is_file():
            report.append("no SPEC.md in this project -- nothing to sync (legal)")
        else:
            body = spec_tool._findings_block_body(str(proj))
            block = f"{spec_tool.SYNC_BEGIN}\n{body}\n{spec_tool.SYNC_END}"
            content = spec.read_text(encoding="utf-8")
            if spec_tool.SYNC_BEGIN in content and spec_tool.SYNC_END in content:
                start = content.index(spec_tool.SYNC_BEGIN)
                end = content.index(spec_tool.SYNC_END) + len(spec_tool.SYNC_END)
                new_content = content[:start] + block + content[end:]
            else:
                sep = "" if content.endswith("\n\n") else ("\n" if content.endswith("\n") else "\n\n")
                new_content = content + sep + "## What we learned here\n\n" + block + "\n"
            if new_content == content:
                report.append("SPEC.md findings block already current (idempotent no-op)")
            else:
                tmp = spec.with_name("SPEC.md.tmp")
                lock = spec_tool._acquire_lock(str(proj))
                try:
                    tmp.write_text(new_content, encoding="utf-8")
                    import os
                    os.replace(str(tmp), str(spec))
                finally:
                    spec_tool._release_lock(lock)
                report.append("SPEC.md findings block regenerated from FINDINGS.md")
    except OSError as exc:
        report.append(f"sync-findings step FAILED (non-fatal to the run, but LOUD): {exc}")

    report.append(release_lanes_row(proj, session_id))
    return report


def main(argv: list[str]) -> int:
    proj = None
    path = None
    session_id = None
    if "--dir" in argv:
        proj = argv[argv.index("--dir") + 1]
    if "--path" in argv:
        path = argv[argv.index("--path") + 1]
    if "--session" in argv:
        session_id = argv[argv.index("--session") + 1]
    if not proj or path not in ("finish", "blocker-stop"):
        print("usage: promote.py --dir <ABS project> --path finish|blocker-stop [--session SID]",
              file=sys.stderr)
        return 2
    proj_path = Path(proj)
    if not proj_path.is_absolute():
        print(f"promote.py failed: --dir must be ABSOLUTE, got {proj!r}", file=sys.stderr)
        return 2
    for line in promote(proj_path, path, session_id):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
