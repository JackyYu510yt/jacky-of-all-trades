---
name: "crossover-research-upfront"
description: "Use instead of crossover-angle-research: same crossover angle research, but asks franchise, channel count, title style and title count all at the start, with an option to decide titles after research."
---

# Crossover Angle Research (questions upfront)

The user runs several YouTube channels that each passed a 3-day niche test. They pick one franchise and give each channel its own crossover angle, e.g. "Anime characters x The Boys" or "Marvel x The Boys". This skill finds the best angles with evidence, then the best characters and titles for each.

## Step 1 — Ask all four questions first

Ask all of these in one go before doing any research (use AskUserQuestion if available, otherwise plain text). If the user already answered any of them in their message, don't ask those again.

1. **Which franchise?** (e.g. The Boys)
2. **How many ready channels?** One channel = one angle.
3. **Which title style(s)?** Options: What If, Scene Style, Hybrid, Hybrid Full Mix (multi-select), plus **"Decide after research"**.
4. **How many titles per channel?** Options: 3, 30, plus **"Decide after research"**. (The user can type another number.)

Don't start research until questions 1 and 2 are answered.

If the user answers questions 3 and 4, carry those answers through and do not ask about titles again in Step 6; the run should finish without stopping. If either is "Decide after research" (or left unanswered), ask that question at Step 6 after the research is written up.

## Step 2 — Timing check

Web-search the franchise's current status: latest season or release date, whether the main show has ended, and upcoming spinoffs, seasons or films with dates. Also note the franchise's anchor character — the one who shows up as the opponent in most crossover videos (for The Boys it was Homelander). Every angle should be built around that anchor.

Flag it plainly if the franchise is past its peak, and name the next spikes the user can plan around.

## Step 3 — Research candidate angles

Cast wide first (8–12 candidate universes: anime, Marvel, DC, video games, childhood cartoons, related shows from the same studio, etc.), then narrow to the requested number.

Sources, in order of weight:

1. **YouTube (most important).**
   - Algrow `youtube_search` with `sort_by: view_count`, `type: video`. Run queries like "[anchor] vs", "in [franchise] universe", "if they were in [franchise]", "[anchor] vs [character]", and Shorts-only versions (`duration: short`, `upload_date: year` or `month`).
   - Try Algrow `search_viral_videos` (shorts and longform) for outlier scores. It has returned 500 errors before; if it fails twice, fall back to `youtube_search` view counts and say so in the report.
   - Note how many different channels already cover each angle (competition).
2. **AO3.** WebFetch `https://archiveofourown.org/tags/<Franchise Tag>/works`. The "Include Fandoms" filter sidebar lists the top crossover fandoms with work counts. The crossover-only filter URL has returned 525 errors; the plain works page is enough.
3. **FanFiction.net** crossover counts if reachable (it often isn't — note it as a gap).
4. **Google / Google Trends** as a tiebreaker if available.

Also search for release timing of the top candidate universes (e.g. Invincible Season 5), since an upcoming release boosts an angle.

## Step 4 — Rank the angles

Score each candidate on:

- **Demand:** biggest crossover videos found, plus AO3 crossover work count.
- **Competition:** how many channels already own it. A medium-demand angle nobody owns can beat a crowded one.
- **Distinctness:** each angle must pull a different fanbase so channels don't compete. Flag overlapping pairs (e.g. Marvel and DC) and say which to swap if one stalls.

Drop high-signal angles that don't fit crossover battle content and explain why (e.g. a romance-driven AO3 crossover like Supernatural x The Boys, or a same-universe spinoff like Gen V).

## Step 5 — Characters per angle

For each angle, list:

- **Proven picks:** characters with an existing crossover video that got real traction (mostly 100K+), with view counts.
- **Untested picks:** popular characters with a strong conflict hook against the anchor or the franchise's world, but no proof yet.

Pick characters by matchup (power level vs the anchor, moral clash, "how would they survive this world"), not popularity alone.

## Step 6 — Titles

Use the title style(s) and count from Step 1. Only if the user chose "Decide after research" (or didn't answer) for either, ask that question now, after the research sections are written.

Keep the numbering identical across styles so the same premise sits at the same number in every style.

### The four title styles

1. **What If (traditional)** — a short, direct question.
   - What If Omni-Man Fought Homelander?
2. **Scene Style** — [Character] [did one specific thing] — And [the consequence]. Past tense, concrete action, em dash, a payoff that often includes a time stamp ("by morning", "before dinner"). No "What If".
   - Batman Studied Homelander For A Year — And Showed Up With A Plan He Never Saw Coming
3. **Hybrid** — every title opens with "What If", then plays out scene style, ending in a question mark.
   - What If Omni-Man Landed On Vought Tower — And Homelander Realized He Wasn't The Strongest Anymore?
4. **Hybrid Full Mix** — a blend within each channel: big matchups get the Hybrid "What If" opener, story-driven premises stay pure Scene Style. Roughly 12–15 of every 30 lead with "What If".

When the user asks for a new style (not one of the four), show 2–6 examples for approval before writing the full set. This is the one check that can still happen mid-run.

### Title output formats

Print every requested style in both formats below, Format A first, then Format B.

**Format A — Numbered List**

One master list covering all channels, numbered 1 to (channels × titles per channel). Ordering rules:

- **Best titles first** — highest-confidence predicted performers (proven premises with real view counts) go to the top so they get early traction.
- **Variety between consecutive titles** — no two back-to-back titles share the same secondary character/subject, emotional trigger, or premise format. This applies both to neighbours in the master list and to each channel's consecutive days in Format B.
- **Experiments toward the end** — lower-confidence or unproven concept titles go later in the list.

Because each channel has its own angle, build the master list so that Format B deals each channel only its own titles: position k belongs to channel ((k − 1) mod N) + 1, where N is the channel count. In practice, rank each channel's titles best-first, then interleave them round-robin (channel 1's #1, channel 2's #1, … channel N's #1, channel 1's #2, …).

Just the titles, numbered, no reasoning, no headers, no annotations, no view counts. Designed for pasting into a spreadsheet or posting tool. One title per line:

```
1. [Title]
2. [Title]
3. [Title]
```

**Format B — Setlist (grouped by channel)**

Take the Numbered List in exact order and deal the titles out sequentially across channels: title 1 to Channel 1, title 2 to Channel 2, … title N to Channel N, then title N+1 back to Channel 1, and so on. No re-shuffling — the numbered list already handles ordering and variety. Each channel's Day number = its nth title (Day = ceil(k / N)), and each title keeps its master-list number.

CRITICAL: Each title MUST be on its own separate line, with a line break after every title. Never put multiple titles on the same line. Each title gets its day label inline. Channel headers are plain uppercase lines (CHANNEL 1, CHANNEL 2, …), with no other annotations.

Example with 10 channels:

```
CHANNEL 1
(Day 1) 1. Warhammer 40K What If: Horus Was RESURRECTED And Redeemed | What If To Sleep To
(Day 2) 11. Warhammer 40K What If: EVERY Primarch Returned At Once | What If To Sleep To
(Day 3) 21. Warhammer 40K What If: The Emperor Forgave Horus | What If To Sleep To
CHANNEL 2
(Day 1) 2. Warhammer 40K What If: The Emperor NEVER Created The Primarchs | What If To Sleep To
(Day 2) 12. Warhammer 40K What If: The Tyranids ATE A Chaos God | What If To Sleep To
(Day 3) 22. Warhammer 40K What If: Lorgar Was REDEEMED | What If To Sleep To
```

Put both formats inside code blocks (in the doc and in chat) so line breaks survive copying.

## Output

Write the research into a doc the user can keep and edit, with these sections:

1. **Bottom line** — the N angles in rank order and the key timing caveat.
2. **Timing check** — table of franchise events and what each means for the user.
3. **The N angles, ranked** — table: rank, angle, best YouTube proof (linked, with views), AO3 crossover works, competition, why it ranks there. Add an overlap warning.
4. **Characters and titles per angle** — table: proven picks, untested picks, title formats that worked.
5. **Top 3 titles per channel** — table with proof links and view counts (this is where title evidence lives, since the title lists themselves carry no annotations).
6. **Angles considered and left out** — with reasons.
7. **Data gaps and next steps** — any source that failed, plus a scale/kill rule checklist.
8. **Titles** — one section per requested style, each containing Format A (Numbered List) then Format B (Setlist), exactly as specified above.

When the user asks to "paste" something, give it in chat in Format A and/or Format B inside a code block.

## Principles

- Every ranking claim needs a number behind it (views, AO3 counts). Say plainly when a source failed or was unreachable.
- Link proof videos as https://www.youtube.com/watch?v=<video_id>.
- Keep real people (athletes, celebrities) out of title lists; a real-person meme is at most a one-off on an existing channel.