
## 2026-10-27 09:31  id: 7b6f6e96
big_lesson: A skill that points to another skill's section by name breaks silently when that other skill is rewritten; a cross-skill pointer needs either a copy or a check that the target text still exists.
change: TRAP 2026-10-27: ~/.claude/skills/prep/SKILL.md (Phase 7) says the canonical RED-TEAM brief lives in ~/.claude/skills/audit/SKILL.md under "The brief handed to the RED-TEAM". grep finds no "RED-TEAM" at all in audit/SKILL.md on 2026-10-27. This session wrote the brief from the 10 categories listed in prep's own text.
why: Found while running /prep for the cloner multi-account split.
context: Copies of the RED-TEAM idea still exist in ~/.claude/skills/memory/feedback_redteam_scenario_attack.md.
before: prep/SKILL.md treats audit/SKILL.md as holding the RED-TEAM brief.
after: It does not (as of 2026-10-27); fix the pointer or restore the brief.

## 2026-10-27 17:28  id: 1f9f463c
big_lesson: when a skill points to a canonical text "living in" another file, check that it still exists at dispatch time. A pointer to a removed section quietly turns a mandatory step into improvisation.
change: TRAP 2026-10-27. ~/.claude/skills/prep/SKILL.md (Phase 7, line ~747) says the canonical RED-TEAM brief lives in ~/.claude/skills/audit/SKILL.md under "The brief handed to the RED-TEAM". As of 2026-10-27 audit/SKILL.md has NO occurrence of "RED-TEAM" at all; the text survives only in auto/SKILL.md.bak-* backups and auto/check_exit.py.
why: /prep's RED-TEAM dispatch has no canonical brief to read, so each run re-writes one from the 10-category summary in prep/SKILL.md.
context: /prep run for the stagger Star priority button (stagger-dashboard/Prep/prep-star-priority.txt). The brief was rebuilt from prep's own one-paragraph summary.
before: prep/SKILL.md says the RED-TEAM brief is in audit/SKILL.md.
after: it isn't there. Restore it to audit/SKILL.md, or re-point prep/SKILL.md to the text it inlines.

## 2026-10-28 04:10  id: 8519c37c
big_lesson: A skill that points to a section in another skill by heading name breaks silently when that section is moved, so cross-skill pointers need a check or a copy, not a name.
change: TRAP 2026-10-28 ~04:30 PDT. ~/.claude/skills/prep/SKILL.md Phase 7 says the canonical RED-TEAM brief lives in ~/.claude/skills/audit/SKILL.md under "The brief handed to the RED-TEAM". That heading is not in audit/SKILL.md (grep for "RED-TEAM" finds 0 matches). The only copies are old auto/SKILL.md.bak-* files and skills/memory/feedback_redteam_scenario_attack.md.
why: A /prep run needs the RED-TEAM brief at dispatch time.
context: This run used the 10 attack categories listed in prep/SKILL.md itself as the brief.
before: The prep skill trusted that pointer.
after: Until the pointer is fixed, build the RED-TEAM brief from prep/SKILL.md's own 10 categories (or skills/memory/feedback_redteam_scenario_attack.md).

## 2026-10-30 02:42  id: d59e1d4d
big_lesson: A skill that points to another file's section "for the canonical text" breaks silently when that section is edited away; check the pointer resolves before relying on it, and keep a short fallback inline.
change: TRAP 2026-10-30. prep/SKILL.md Phase 7 says the canonical RED-TEAM brief lives in ~/.claude/skills/audit/SKILL.md under "The brief handed to the RED-TEAM". As of 2026-10-30 that file has NO RED-TEAM text at all (grep -i "red-team" -> 0 hits). The 10 attack categories listed in prep/SKILL.md itself were used as the brief instead (chess-modal prep).
why: measured by grep on 2026-10-30.
context: /prep for Chess Video Generator V1 Modal lane, Phase 7 dispatch.
before: belief: audit/SKILL.md holds the canonical RED-TEAM brief.
after: it does not; prep's own category list is the only surviving copy.

## 2026-11-05 17:05  id: 87236e94
big_lesson: A skill that says "the canonical brief lives in <other skill> under heading X" is a dangling pointer the moment that other skill is rewritten; check the pointer resolves before relying on it, and keep the canonical text where the caller can find it.
change: TRAP 2026-11-05 ~16:55 PST. FINDING (read the files): ~/.claude/skills/prep/SKILL.md Phase 7 says the RED-TEAM brief lives in ~/.claude/skills/audit/SKILL.md under "The brief handed to the RED-TEAM". The live audit/SKILL.md (rebuilt) contains no RED-TEAM text at all (grep -i red-team: 0 hits). The brief survives only in ~/.claude/skills/_backups/audit-2026-09-10/SKILL.md, which this run used.
why: /prep requires the RED-TEAM in parallel with the AUDITOR; a missing brief means each run improvises it.
context: Synapse Fast Finder Part 2 /prep + /auto run, auto-runs/fast-finder-part2-1646.
before: /prep assumed audit/SKILL.md still holds the canonical RED-TEAM brief.
after: Brief found only in the 2026-09-10 backup; fix = restore it to audit/SKILL.md or move it into prep/SKILL.md (not done by this run: out of its scope).

## 2026-11-06 09:25  id: 9c750aae
big_lesson: A skill's frontmatter model:/effort: is a safe way to pin a skill to a stronger model; it applies only while the skill runs and does not leak into the rest of the session.
change: FINDING 2026-11-06 (owner observed it in the status line): /prep with frontmatter "model: claude-opus-5-5" + "effort: xhigh" ran at xhigh, then the session went back to its normal model/effort afterward.
why: The owner wanted /prep always on Opus 5.5 xhigh, and wanted to know whether the pin switches back after the skill finishes.
context: Edited ~/.claude/skills/prep/SKILL.md 2026-11-06 (backup SKILL.md.bak-pre-model-pin-20261106). Also added a first-message reminder line naming the pin so the owner knows to bump it when a newer model ships, and told Agent dispatches to pass model opus + effort xhigh.
before: Unverified. My earlier answer, that the pin "probably reverts after the skill", was INFERENCE from memory.
after: Confirmed by the owner watching the status line: the pin applies during /prep and resets afterward.
