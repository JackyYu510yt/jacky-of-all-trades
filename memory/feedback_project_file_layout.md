---
name: feedback_project_file_layout
description: "Standing folder-structure convention for every project — active/stages, Tests and Probing, Support Scripts and Functions, Spec, Prep"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 904d6fbd-3f0e-4703-b771-ff5dc8290dd6
  modified: 2026-09-17T12:35:33.976Z
---

Every project folder uses a fixed five-way layout, codified 2026-09-17 in
`~/.claude/CLAUDE.md` ("Project file layout convention") and wired as a
one-line pointer into `/auto`, `/prep`, `/deep-audit`, `/error-recon`,
`/optimize`, `/repair`:

- **Active folder (project root)** — ONLY main/active pipeline scripts, split
  into numbered stages (`stage_1_<name>.py`, `stage_2_<name>.py`, ...), one
  file per stage. Modeled on the Jacky Rush tool's 8-stage layout. Never one
  monolith file.
- **`Tests and Probing/`** — every test/probe gets its OWN timestamped
  subfolder, named `M-D-YY H:MM AM/PM Probing <description>`
  (e.g. `9-17-26 4:56 AM Probing xyz`). Nothing loose directly in this folder.
- **`Support Scripts and Functions/`** — supplemental/helper scripts (e.g. an
  account fleet warmer). Flat, no subfolders.
- **`Spec/`** — `SPEC.md`, `FINDINGS.md`, satellite/sub-project spec files,
  and lesson dumps all live together here now. RESOLVED 2026-09-17: this used
  to be blocked because `~/.claude/skills/spec/note.py`, `spec_digest.py`,
  `spec_tool.py`, and the `spec-collect`/`spec-guard` hooks all hardcoded
  `<project_root>/SPEC.md` and `<project_root>/FINDINGS.md`. Per user
  direction ("modify it to work with the new structure," not "leave the
  files at root"), those five files were patched to check
  `<project_root>/Spec/` first and fall back to the legacy root location —
  so old, not-yet-reorganized projects keep working untouched. Full
  regression suite passed before and after
  (`test_spec_system.py` 17/17, `tests/test_note_*.py` 8+14+900/900).
  Pre-patch copies: `~/.claude/skills/_backups/spec-folder-support-20260917/`.
- **`Prep/`** — `/prep` planning artifacts (prep plan files, interview notes)
  before a design becomes real stage files.

**Why:** the user wants the main pipeline kept as inspectable, individually
modifiable puzzle pieces, and wants every probe/test timestamped so probes
never mix with each other, the main scripts, or planning/findings material.

**How to apply:** when creating any new file in a project, place it by what
it IS (main stage vs. probe/test vs. support script vs. spec/finding vs.
prep artifact), not by which skill happens to be running. Don't ask the user
where to put a file that clearly fits one of these categories — just place
it there. See [[project_fnreview_auto_upgrade]] and [[project_auto_runs_folder_layout]]
for related /auto file-bookkeeping conventions (auto-runs/ stays separate,
untouched by this rule).
