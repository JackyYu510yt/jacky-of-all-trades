---
name: Response format — ADHD + visual reading
description: User has ADHD and visual difficulty; every response uses rainbow top separator, bold headlines, double-spaced items, and chunked structure
type: feedback
---

**Why this exists:** the user has ADHD and visual difficulty reading dense text. Reading pattern is: scans first, reads second; loses place easily; struggles with long unbroken paragraphs and tight lists; benefits from strong visual anchors and consistent chunk structure so the eye can re-find its spot after a distraction.

Every response must follow all four rules below — they work together.

---

## 1. Rainbow row at the top — every response, no exceptions

Start every response with this exact 24-square row as the very first line, before any other content:

```
🟥🟧🟨🟩🟦🟪🟥🟧🟨🟩🟦🟪🟥🟧🟨🟩🟦🟪🟥🟧🟨🟩🟦🟪
```

(Red → orange → yellow → green → blue → purple, four cycles.)

**Why:** chat history becomes a long text wall. The rainbow is a unique visual landmark — no other content uses those emojis together — so the user can scroll back and instantly find where each answer started.

**How to apply:**

- First line of every response, always — before any text, heading, or other separator.

- Only at the top. Never in the middle of a response. Never in a TL;DR. Never between steps.

- Applies to every response, not just `/explain` or any specific skill.

- Even single-sentence quick replies get it. Consistency over brevity.

- The rest of the response uses plain `====` separators as normal between walkthrough steps, etc.

---

## 2. Headline-then-detail — every block leads with a bold one-liner

Every section, verdict, checkpoint, or status block opens with a one-line bold headline that carries the takeaway by itself. The reader should be able to act on just that line if they don't read further.

**Why:** ADHD attention is bursty — the first line gets read; later lines may not. Burying the conclusion under context means the user acts on incomplete info. (Confirmed when the user picked Variant A's `**PARTIAL — needs your call on one rule**` over a four-field block: the headline carried the decision; the body just supported it.)

**How to apply:**

- Verdicts: `**STATE — what's true or needed.**`

- Section headers carry the takeaway, not just the topic. (`**Render not yet re-run with new timeout**` beats `**Status**`.)

- Avoid headers that are just labels (`Pending`, `Note`) unless they introduce a list whose items are the real signal.

- Place the most important takeaway first, supporting detail after. If the user stops reading partway, they still have the point.

- Don't bury answers inside long paragraphs — surface them.

---

## 3. Spacing — one mechanism per block, never two stacked

Use vertical spacing for visual anchors, but don't stack mechanisms. Choose blank-line-between-items OR `====` separators, not both on top of each other.

**Why:** the user needs strong visual anchors AND short scrolling. Stacking mechanisms triples the message length without adding clarity; skipping them blurs chunks together.

**How to apply:**

- **With `====` separator lines between items:** one blank line above and below the separator is enough. Do NOT also blank-line every bullet on top of that.

- **Without `====` separators:** keep a blank line between each item in a list, so each bullet stands alone visually.

- Between sections / sub-sections that have a heading: blank line above the new heading.

- Short TL;DR-style bullet lists (5–8 short items) can be tight (no blank line between bullets) when they follow a strong `====`-wrapped walkthrough — the walkthrough is the real content, TL;DR is the quick reference.

- Long bullet lists (>8 items, or items longer than one line) always get blank lines between items.

**Rule of thumb:** one visual-break mechanism per block, not two.

---

## 4. Chunked structure — small, scannable, bold-first

Every chunk follows the same shape: **bold headline → one or two short follow-up sentences → stop.** Same info always lives in the same position within each chunk so the eye knows where to look.

**How to apply:**

- Bold the anchor/headline of each chunk so the user can scan by skimming bold text only.

- Keep the first few words of each chunk information-dense so scanning still delivers meaning.

- Use explicit `====` separators between chunks when walking through multi-step content (workflow, logic, reasoning) — gives the eye a clear anchor to return to.

- Keep each chunk small. One headline, one or two follow-ups, stop.
