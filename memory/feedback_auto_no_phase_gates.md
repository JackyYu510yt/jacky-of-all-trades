---
name: /auto has no phase gates
description: Under /auto, skill phase boundaries (e.g. /prep's Phase 8 build boundary) are NOT user-confirmation gates — only DONE or STUCK ends the loop
type: feedback
originSessionId: f5c7a80c-8f89-442c-b700-37f79c208fb5
---
Under /auto, the only valid stop conditions are **DONE** (success verified against an explicit checklist) or **STUCK** (genuinely blocked, with a named reason). Skill-internal phase boundaries — /prep's "Phase 8 build" boundary, /repair's "ready to apply patch" boundary, etc. — are NOT user-confirmation gates. Drive straight through them.

**Why:** On 2026-05-05 the user invoked `/auto /prep` to diagnose+fix Gemini empty-200 failures. I ran /prep, wrote the plan, did the auto-review, integrated fixes — then asked "build / tweak / stop". The user pushed back: "obviously do whatever is needed to diagnose and fix the issue right? thats the whole point of auto. why are u asking me." Asking permission at a phase boundary defeats the entire point of /auto.

**How to apply:**

- When the user invokes /auto (alone or in combination with /prep, /repair, /optimize, etc.), drive end-to-end through every internal phase of the chained skill without asking permission.

- Treat skill phase boundaries as transitions, not gates. Plan → build → run → verify → report is one continuous flow.

- Stop ONLY on DONE (every success-condition checkbox ticked) or STUCK (a specific blocker I can name).

- If the user's /auto invocation didn't include explicit DONE/STUCK conditions, infer them from the stated goal in 1-2 sentences and state them at the start, then drive against them. Don't ask the user to author the conditions for me unless the goal itself is ambiguous.

- Asking "build / tweak / stop" or "should I proceed" mid-flow under /auto is a violation. The invocation was the authorization.

- The only mid-flow user contact allowed under /auto is reporting STUCK with a specific reason and proposed next experiment — never a generic "should I continue?".
