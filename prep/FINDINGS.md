
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
