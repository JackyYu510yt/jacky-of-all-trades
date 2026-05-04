---
name: feedback_rainbow_top_separator
description: Every response from Claude must begin with a rainbow-square row so the user can scroll back through chat history and find where each answer started
type: feedback
originSessionId: e603725b-6687-40da-af59-af62bed45597
---
Start every response with this exact rainbow row as the very first line (before any other content):

```
🟥🟧🟨🟩🟦🟪🟥🟧🟨🟩🟦🟪🟥🟧🟨🟩🟦🟪🟥🟧🟨🟩🟦🟪
```

That's 24 colored squares cycling red→orange→yellow→green→blue→purple, four times.

**Why:** The user has ADHD and visual difficulty, and the chat can become a long text wall. Scrolling back to find where past responses began is hard when every block looks similar. The rainbow row is a unique visual landmark that's instantly findable — no other content in the conversation uses those emojis together.

**How to apply:**

- Place the rainbow row as the very first line of every response. Before any text, headings, or other separators.

- Use ONLY at the top of a response. Never in the middle. Never in a TL;DR. Never between steps.

- The rest of the response uses plain `====` separators as normal (between walkthrough steps, wrapping TL;DR blocks, etc.).

- Applies to every response, not just `/explain` output or any specific skill.

- Single-sentence quick replies still get the rainbow row at the top — consistency matters more than brevity here.
