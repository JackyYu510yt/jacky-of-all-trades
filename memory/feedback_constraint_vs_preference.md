---
name: feedback_constraint_vs_preference
description: "a deadline/window is a filter, not a vote for the slowest option that fits; among options meeting the constraint, faster/better still wins"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 80768123-2dc3-4564-9983-7c9f470d67e4
---

When a goal states a limit ("overnight", "under 5 GB", "by Friday"), treat it as a **constraint to satisfy**, never as a preference to maximize toward. Do NOT reason "the deadline is loose, so the slow option is fine, so recommend the slow one." The right logic is two steps: (1) filter out options that won't fit the limit, then (2) among the survivors, recommend the one that best serves everything else (speed, machine freed sooner, hands-off, quality).

Example that triggered this: goal = "render reels overnight, hands-off." Skill recommended CPU (libx264, ~3 hrs) because "overnight = time isn't tight." User rejected — GPU (~20 min) also fits overnight AND frees the machine by morning. Fastest-that-still-fits wins.

**Why:** confusing a limit with a target produces lazy, wrong recommendations — picking the slowest/worst option that technically satisfies the constraint instead of the best one.

**How to apply:** classify every goal word as a **limit** (a window/ceiling → filter, then maximize the rest inside it) or a **target** (the thing to maximize). When recommending an option (e.g. AskUserQuestion "(Recommended)"), trace the pick through both steps. Relevant to the mental-model / decision-picker skill being designed and to any goal-driven recommendation. Links [[feedback_pick_from_options]], [[feedback_keep_end_goal_in_sight]].
