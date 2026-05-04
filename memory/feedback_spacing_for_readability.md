---
name: feedback_spacing_for_readability
description: Use double line breaks between items in any list or between logical blocks — user has difficulty reading dense text
type: feedback
originSessionId: e603725b-6687-40da-af59-af62bed45597
---
Use vertical spacing to help readability, but do not stack spacing mechanisms — choose blank-line separation OR a separator line (`====`), not both.

**Why:** The user has visual difficulty AND ADHD — they need strong visual anchors to keep their place, but excessive spacing makes them scroll too much. The goal is "each chunk is clearly separated" without "the message is 3x as long as it needs to be."

**How to apply:**

- **When using `====` separator lines between items:** one blank line above and below the separator is enough. Do NOT also add blank lines between every bullet on top of that — the `====` already provides the visual break.

- **When NOT using `====` separators:** keep a blank line between each item in a list, so each bullet stands alone visually.

- Between sections or sub-sections that have a heading: blank line above the new heading.

- Short TL;DR-style bullet lists (5–8 short items) can be tight (no blank line between bullets) when they follow a strong `====`-wrapped walkthrough — the walkthrough is the real content, TL;DR is the quick reference.

- Long bullet lists (more than ~8 items, or items longer than one line) always get blank lines between items.

**Rule of thumb:** one visual-break mechanism per message block, not two. Either `====` OR blank lines, not both on top of each other.

Applies to every response, not just specific skills.
