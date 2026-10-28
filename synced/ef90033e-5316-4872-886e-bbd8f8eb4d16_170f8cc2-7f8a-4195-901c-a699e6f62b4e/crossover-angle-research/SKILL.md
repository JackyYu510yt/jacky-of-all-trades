---
name: "crossover-angle-research"
description: "Research the best crossover angles for a franchise across a set of YouTube channels, pick characters per angle, and write titles in the user's four title styles."
---

# Crossover Angle Research

The user runs several YouTube channels that each passed a 3-day niche test. They pick one franchise and give each channel its own crossover angle, e.g. "Anime characters x The Boys" or "Marvel x The Boys". This skill finds the best angles with evidence, then the best characters and titles for each.

## Step 1 — Ask two questions first

Ask these before doing any research (use AskUserQuestion if available, otherwise plain text):

1. **Which franchise?** (e.g. The Boys)
2. **How many ready channels?** One channel = one angle.

Don't start research until both are answered.

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

Ask which title style(s) and how many per channel (the user has used 3 and 30). Put proven titles first, each marked with the view count of the video it's based on. Keep the numbering identical across styles so proven premises stay at the top.

### The four title styles

1. **What If (traditional)** — a short, direct question.
   - What If Omni-Man Fought Homelander?
2. **Scene Style** — [Character] [did one specific thing] — And [the consequence]. Past tense, concrete action, em dash, a payoff that often includes a time stamp ("by morning", "before dinner"). No "What If".
   - Batman Studied Homelander For A Year — And Showed Up With A Plan He Never Saw Coming
3. **Hybrid** — every title opens with "What If", then plays out scene style, ending in a question mark.
   - What If Omni-Man Landed On Vought Tower — And Homelander Realized He Wasn't The Strongest Anymore?
4. **Hybrid Full Mix** — a blend within each channel: big matchups get the Hybrid "What If" opener, story-driven premises stay pure Scene Style. Roughly 12–15 of every 30 lead with "What If".

When the user asks for a new style, show 2–6 examples for approval before writing the full set.

## Output

Write the research into a doc the user can keep and edit, with these sections:

1. **Bottom line** — the N angles in rank order and the key timing caveat.
2. **Timing check** — table of franchise events and what each means for the user.
3. **The N angles, ranked** — table: rank, angle, best YouTube proof (linked, with views), AO3 crossover works, competition, why it ranks there. Add an overlap warning.
4. **Characters and titles per angle** — table: proven picks, untested picks, title formats that worked.
5. **Top 3 titles per channel** — table with proof links.
6. **Angles considered and left out** — with reasons.
7. **Data gaps and next steps** — any source that failed, plus a scale/kill rule checklist.
8. Title lists in each requested style, one section per style, one subsection per channel.

When the user asks to "paste" something, give it in chat as a short ranked list.

## Principles

- Every ranking claim needs a number behind it (views, AO3 counts). Say plainly when a source failed or was unreachable.
- Link proof videos as https://www.youtube.com/watch?v=<video_id>.
- Keep real people (athletes, celebrities) out of title lists; a real-person meme is at most a one-off on an existing channel.