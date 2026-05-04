---
name: feedback_no_mid_reasoning_pivots
description: Never print early hypotheses that later get overturned — user reads the first part and starts acting on it, then gets whiplash from the correction
type: feedback
originSessionId: e603725b-6687-40da-af59-af62bed45597
---
Do not emit mid-reasoning pivots, "plot twist" moments, or "wait — actually it's the opposite" corrections in visible output. Think silently, then present only the final, correct answer.

**Why:** The user explicitly stated they read the first part of a message and start acting on it. If the message later says "wait, actually X was wrong," by the time they read it they've already moved on bad information and it throws them off. The visible answer must be the settled answer.

**How to apply:**
- Do all investigation, ruling-out, and hypothesis-revision silently (in thinking, or via sequential tool calls without narrating false leads).
- When presenting the result, write as if you always knew it — no "first I thought X, then I realized Y".
- If you want to note that an earlier assumption was wrong, do it briefly at the end ("earlier guess about prompts being filterable was wrong — the image is the issue") rather than leading with it.
- Never use phrases like "wait —", "plot twist", "actually, the opposite", "scratch that" at the top of a response.
- Applies to every response, not just specific skills.
