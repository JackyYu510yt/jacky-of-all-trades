---
name: feedback-prep-stage-files
description: "/prep builds pipelines as separate stage_N_<name>.py files, never one script with many functions; additions to an existing staged pipeline use decimal stage numbers in a subfolder"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 77e47bbf-5d92-4b1b-9ee4-3aff66708764
  modified: 2026-09-23T04:11:43.751Z
---

`/prep` never builds a single monolithic script with many functions inside it. Every pipeline is broken into STAGES, one file per stage: `stage_1_<name>.py`, `stage_2_<name>.py`, ... — each independently inspectable/editable, mirroring the Jacky Rush tool (`stage_1_timestamp.py` ... `stage_8_rendering.py`). A thin orchestrator composes them. This is the default build shape for every fresh `/prep` run, not just the eventual "promoted to active folder" destination — codified in `~/.claude/skills/prep/SKILL.md` (Phase 4 stage list, Phase 8 build, Hard NOs) 2026-09-22.

**Extending an EXISTING staged pipeline:** don't renumber existing stage files to insert new work. Use decimal stage numbers for the insertion point — inserting after `stage_2_plan.py` and before `stage_3_sourcer.py` is `stage_2.1_<name>.py` (a second insertion in the same gap: `stage_2.2_<name>.py`). These decimal-numbered files live in their own subfolder (not loose in the active folder), so it's visually obvious "this is an addition" vs. "this is the pipeline." Existing stage files are left untouched unless the addition genuinely changes their handoff contract.

**Why:** the user wants each stage as an inspectable, independently-editable puzzle piece — easier to follow the workflow numerically, and to edit one stage without touching the others. Extending in place without renumbering avoids churn/risk to working stage files just to make room for new ones.

**How to apply:** relevant to `/prep` (already wired into its SKILL.md) and to any ad hoc pipeline-building work in this user's projects generally — default to stage-file decomposition over a single script, and use the decimal+subfolder convention when bolting onto an existing staged tool. See [[feedback_project_file_layout]] for the broader per-project folder convention this fits inside.
