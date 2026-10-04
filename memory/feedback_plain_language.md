---
name: feedback_plain_language
description: Explain technical concepts in simple, concrete terms — short sentences, everyday analogies, no unexplained jargon
type: feedback
originSessionId: e603725b-6687-40da-af59-af62bed45597
modified: 2026-09-06T13:19:14.248Z
---
When explaining technical concepts to the user, default to plain language:

- Short sentences.
- Concrete analogies tied to physical, everyday things.
- Define any technical term the first time it appears, in one plain sentence.
- No abbreviations without expansion on first use.
- No condescension — plain does not mean dumbed-down.

**Why:** The user explicitly asked for simple terms when explaining how things work. This was a direct preference stated while designing the `prep` skill. They want to understand, not be impressed by vocabulary.

**How to apply:** Any time you walk the user through how a script, system, or concept works — especially during planning, design reviews, or code explanations — lead with an analogy or a walkthrough in plain English before any technical detail. Example: "Checkpointing means the script saves progress every few steps, like a video game saves after each level" beats "Checkpointing provides crash-consistent state persistence."

**Incident 2026-09-06 — jargon crept into live progress narration, not just "explanations".** Mid-debug status updates on an image-gen pipeline ("6 for 6 wrong", "reference-image theory", "it's anchored to one specific demo story", "dominates completely whenever there's no other character-specific image competing with it") read like one seasoned coder briefing another — fluent but not translated. The user's own words: *"its telling me a report like a seasoned coder who inherently understands this... I like to be clear and intentional."* Two gaps beyond plain-word-choice:
1. **Scope was too narrow.** These memories fired for explicit "explain X" requests; they need to also cover default progress/status narration during any live task — debugging, test batches, builds. There's no separate "reporting register" that gets to skip translation just because it's a status update instead of a requested explanation.
2. **Confirm-or-correct the user's own hypothesis explicitly.** When the user has floated a theory ("is this a reference-image problem?"), a coherent report says outright — early, in plain words — "yes, that theory looks right, here's the evidence" or "no, that's ruled out, here's why" before going further. Don't make the user extract the verdict from a narrative. **This is a distinct rule from "no jargon" — see [[feedback_user_coherence_verdict_first]] for the full writeup (word choice vs information order are two separate axes; a report can pass one and fail the other).**

**How to apply (expanded):** treat live status/progress reports the same as requested explanations — same plain-word default, same curious-adult register ([[feedback_explanation_level]]). Before adding a technical claim to a progress update, ask "would this sentence mean something to someone who didn't write the code?" If not, translate it or cut it. When the user has stated a hypothesis, open with a direct yes/no/partial verdict on it before the supporting narrative ([[feedback_user_coherence_verdict_first]]). This is the default for /explain and /debrief (renamed from /dumb 2026-09-09) specifically, and for any other skill's live reporting.
