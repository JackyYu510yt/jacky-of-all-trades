
## 2026-10-16 10:15  id: 2b00b9fa
big_lesson: A skill that points at a canonical brief "by heading" instead of carrying it breaks silently when the target file is rewritten; verify the pointer resolves before relying on it, and keep the brief where the dispatch happens.
change: TRAP 2026-10-16: ~/.claude/skills/prep/SKILL.md Phase 7 (line ~747) says the canonical RED-TEAM brief lives in ~/.claude/skills/audit/SKILL.md under "The brief handed to the RED-TEAM". As of 2026-10-16 that heading does not exist there (grep -i "red-team" on audit/SKILL.md returns nothing). The only surviving description is ~/.claude/skills/memory/feedback_redteam_scenario_attack.md (10 categories C1-C10, verdicts HANDLED/DEGRADES/BREAKS/UNKNOWN). spec/SKILL.md:324 has the same dangling pointer.
why: the audit skill was rewritten into a single YES/NO AUDITOR design; the RED-TEAM brief went with it and the referencing skills were not updated.
context: found during /prep for Crossover v2 (Claude Code Generation V2/Prep/prep-crossover-v2.txt).
before: "/prep and /spec can read the RED-TEAM brief from audit/SKILL.md at dispatch time".
after: the brief must be rebuilt from the memory note until the skills are fixed.

## 2026-10-24 19:58  id: a4435d90
big_lesson: A skill that points at another skill's section by heading name breaks silently when that section is rewritten; keep shared briefs in their own file, or check the pointer resolves when the target skill changes.
change: TRAP 2026-10-24 20:00 PDT. prep/SKILL.md (Phase 7) and memory/feedback_redteam_scenario_attack.md say the canonical RED-TEAM brief lives in ~/.claude/skills/audit/SKILL.md under the heading "The brief handed to the RED-TEAM". grep finds no "RED-TEAM" text in audit/SKILL.md at all now; the heading only survives in old auto/SKILL.md.bak-* copies.
why: audit/SKILL.md was rewritten (now a YES/NO single-answer review) and the brief was dropped; nothing checks cross-skill pointers.
context: /prep Phase 7 on Prep/prep-gemini-reader-fix.txt (Jacky's Production Factory). The brief was rebuilt from the 10-category list in memory/feedback_redteam_scenario_attack.md for this run.
before: Belief: the RED-TEAM brief can be read from audit/SKILL.md at dispatch time.
after: It cannot. /prep, /auto, /spec readers must fall back to the 10-category list in feedback_redteam_scenario_attack.md until the brief is restored somewhere stable.
