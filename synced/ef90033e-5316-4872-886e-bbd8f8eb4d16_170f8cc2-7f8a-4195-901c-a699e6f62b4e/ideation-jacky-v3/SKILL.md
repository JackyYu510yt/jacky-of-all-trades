---
name: "ideation-jacky-v3"
description: "Use instead of ideation-jacky: same outlier analysis and setlist workflow, plus a Sleep Lore style with the 7 data-backed fall-asleep lore title formats for sleep channels."
---

# Ideation Jacky — Title Maker V3 (Channel Outlier Data + Sleep Lore)

Run this whenever the user sends a channel list or outlier data list. Work through the steps in order. There is one stopping point where you wait for the user: the Setup picker after Step 1. After that, generate everything and print the final lists without stopping again.

## Outlier Extraction Rules

An outlier is based on the x-score next to the video title (like 0.5x, 0.7x, etc.). Only the FIRST x-score shown matters — capture that one.

Example data:

```
Latest Popular Oldest Sort by Popularity Top Keywords Ascending Descending 2 5 10 Clear 2:29:05 Now playing Watch later Add to queue 0.5x 3 Hours of SpongeBob Lore To Fall Asleep To, But It's Unsolved Mysteries 2.5K views 1 day ago 66 VPH 0.9x Remix 104 VPH 0.1x
```

Correct extraction:
- Outlierscore = 0.5x
- Videotitle = 3 Hours of SpongeBob Lore To Fall Asleep To, But It's Unsolved Mysteries
- Views = 2.5K

Another example:

```
Now playing 0.7x 0.8x The WORST Motorcycle Deaths Ever (Celebrity Edition) 20K views 3 days ago 63 VPH
```

Correct extraction:
- Outlierscore = 0.7x (WE WANT THIS ONE)
- 0.8x = IRRELEVANT
- Videotitle = The WORST Motorcycle Deaths Ever (Celebrity Edition)
- Views = 20K

If there is only one number, use that one. Everything else — timestamps, "Now Playing," "Remix," VPH, etc. — is irrelevant and should be ignored. Note that text like "1 MIN AGO" and "BREAKING NEWS" may be part of the video title itself.

## Critical Information

Videos on a small channel with big outliers (or when the channel was small with a big outlier) mean the video premise itself was super good, allowing it to become a huge outlier even on a small channel. This type of video is the most replicable and the most valuable to the user — weight it heavily. The best formats of all are ones that repeated on several small channels AND produced big outliers.

## STEP 1: Pattern Analysis

Based on good performers (3x outlier scores and above). Keep this brief — a few paragraphs, not tables.

A) **What works** — Identify common patterns across 3x+ outliers: recurring themes, emotional triggers, title structures, characters/subjects that appear repeatedly in top performers.

B) **What fails** — Look at the bottom performers (lowest outlier scores or lowest views). Identify patterns that consistently underperform. List 3-5 things to avoid.

C) **Cross-channel check** — If data from multiple channels is provided, flag any concepts that perform well on 2+ channels. These are the highest-confidence patterns. Prioritize components from these when generating titles.

D) **Fatigue check** — If the same concept appears 3+ times across the data, check whether views are growing, stable, or declining with each repeat. Flag any dying concepts to avoid.

E) **Sleep check** — Decide whether this is sleep / lore channel data: titles containing "Fall Asleep To", "To Help You Sleep", "To Sleep To", "Lore", or multi-hour runtimes, on non-crossover channels. If it is, say so in one line ("Sleep channel data detected — using Sleep Lore"), then note which of the 7 Sleep Lore formats (Style 6) show up in this data and how they performed. If this data clearly contradicts the saved ranking, say so; fresh data wins.

## SETUP PICKER (preview mode) — after Step 1, before Step 2

After printing the pattern analysis, ask the setup questions. Skip any question the user already answered in their message (e.g. "Full Mix, 10 channels, 1/day, 7 days"); if everything was answered, skip the picker entirely.

Use the AskUserQuestion tool with four questions in a single call. Question 1 depends on Step 1E.

**Question 1 — if Step 1E detected sleep data:** do NOT ask for a title style; Sleep Lore is already set. Ask instead: **"Which Sleep Lore formats should this batch rotate?"** (header: "Formats", single select). Options, each with a `preview` of 3 sample titles written for THIS batch's show:
- **All 7 core (Recommended)** — description: "Formats 1-7 rotated, weighted toward 1 and 2"
- **Core 7 + test slot** — description: "Same rotation, plus 1 in 10 titles tests Philosophy, How X Caused Y, Hidden Lore or Mistakes"
- **Top 4 only** — description: "Every X Explained, X Hours Of Lore, Unsolved Mysteries, Psychologist"

The user can type another answer (e.g. a specific list of format numbers, or a different style such as "What If" if they want a crossover batch instead). Honor it.

**Question 1 — otherwise:** **"Which title style should this batch use?"** (header: "Title style", single select). Options: What If, Scene Style, Hybrid, Mix. Fill each option's `preview` with that style's format line plus 3 sample titles written for THIS batch's franchise/data (not the generic examples below). For the Mix option, the preview shows 2 sample titles each for Hybrid Full Mix and Full Mix, labeled. If the Step 1 data clearly favors one style, list it first and add "(Recommended)" to its label. The user can type "Sleep Lore" to use Style 6; then use All 7 core unless they say otherwise.

**Question 2 — "How many channels?"** (header: "Channels", single select): options 5, 10, 15. The user can type another number.

**Question 3 — "How many videos per day, per channel?"** (header: "Vids/day", single select): options 1, 2, 3. The user can type another number.

**Question 4 — "How many days to fill?"** (header: "Days", single select): options 7, 14, 30. The user can type another number.

If the user picked Mix, immediately ask one follow-up with AskUserQuestion: **"Which mix?"** (header: "Mix type"): Hybrid Full Mix (description: "What If + Scene Style, ~12-15 of 30 lead with What If") and Full Mix (description: "Equal thirds of What If, Scene Style and Hybrid"), each with a `preview` of 3 sample titles for this batch.

If AskUserQuestion is not available, print the options for Question 1 (the Sleep Lore format sets if sleep data was detected, otherwise the style list) as a numbered list, each with 2-3 sample titles for this batch, and ask the user to reply with: option number, channels, videos per day per channel, days. Wait for the answer before Step 2.

**Total titles needed = channels × videos per day × days.** State this number before generating (e.g. "10 channels × 1/day × 7 days = 70 titles").

## TITLE STYLES

Styles 1-5 are for longform AI-narrated "What If" crossover videos. In those, the visiting (outsider) character is always the subject; the destination's native characters are the stakes or opponent, never the subject. Style 6 (Sleep Lore) is for non-crossover "fall asleep to" lore narration channels and has its own rules.

### 1. WHAT IF
A short question: "What If [character] [arrival verb] [destination]?"
Examples:
- What If Superman Entered The Invincible Universe?
- What If Vegeta Landed On Viltrum?

### 2. SCENE STYLE
Format: [Character] [did one specific thing] - And [consequence].
Past tense, em dash, and the payoff is often time-stamped ("by morning", "that night"). Never starts with "What If". Usually ties the arrival to a specific canon event or moment.
Examples:
- Superman Arrived The Night Omni-Man Killed The Guardians - And Was The Only One Left Standing By Morning
- Saitama Crashed Into Chicago - And Conquest Never Got Back Up

### 3. HYBRID
Opens with "What If", plays out like a Scene Style title, ends with a question mark.
Format: What If [character] [arrival verb] [event/place] - And [native reaction or consequence]?
Examples:
- What If Vegeta Landed During The Viltrumite War - And Thragg Realized Saiyans Don't Kneel?
- What If Goku Entered The Viltrumite War - And Nolan Felt Fear For The First Time?

### 4. HYBRID FULL MIX
A mixed list: big matchups get the Hybrid "What If" opener, story-driven premises stay in Scene Style. Roughly 12-15 of every 30 titles lead with "What If" (scale proportionally for other counts).

### 5. FULL MIX
A mixed list using all three base styles: What If, Scene Style and Hybrid. Roughly equal thirds (about 10 of each per 30 titles; scale for other counts), alternated so the same style never runs more than 2 titles in a row.
- What If: the simplest, highest-recognition matchups (strongest characters, plain arrival).
- Hybrid: big matchups that have a clear native reaction or rivalry.
- Scene Style: story premises tied to a specific canon event or moment.

Examples:
- What If Superman Entered The Invincible Universe?
- Saitama Crashed Into Chicago - And Conquest Never Got Back Up
- What If Vegeta Landed During The Viltrumite War - And Thragg Realized Saiyans Don't Kneel?
- What If Beerus Landed On Viltrum?
- Superboy Prime Arrived The Day The Invincible War Began - And Mark Realized He Wasn't The Strongest Version Of Himself

In the Detailed List, tag each title with its style (WI / SCENE / HYBRID). The no-more-than-2-in-a-row rule applies to the final Numbered List order.

### 6. SLEEP LORE
For faceless "fall asleep to" lore channels about one show or franchise (cartoons, anime, movies, games). Titles use ONLY the proven formats below, limited to the format set chosen in the Setup picker (default: All 7 core).

Data basis: Algrow "Cartoon Sleep Niches" folder — 17 sleep-lore channels (Steven Sleeps, Ricktopus, Snorebob, Adventure Bedtime, Midnight Marvel, Noctoon, Abismo, Toonology, Nightfalls, Stevenox, Bob's Bedtime, Harper Talbot, RickALoden, Galactic Glitches, Gumballology, Sleepy Finn, Roundtable Rewind), 150 outliers at 1.5x+ from May–Oct 2026. Ranked by: repeated on small channels (under 5K subs) AND produced big outliers. Scores are adjusted outlier scores.

**The 7 proven formats (in priority order):**

1. **Every [X] Explained To Fall Asleep To** — 8 small-channel hits across 3 channels; 13.0x on a small channel (Every Diamond's Power Explained), 9.0x on a bigger one. Slot: a power set, villains, creatures, factions, characters, locations, parodies.
2. **[X] Hours Of [Show] Lore To Fall Asleep To** — 17.1x on a 344-sub channel (2 Hours Of Obscure Gravity Falls Lore), 18.9x on Midnight Marvel (2 Hours Of Spiderman Lore). Slot: 2-5 hours; [Show] can be a single character or sub-franchise; "Obscure" is a proven modifier.
3. **[X] Hours Of [Show] Unsolved Mysteries And Theories** — 14.0x (Snorebob), 9.3x (Steven Sleeps), 7.1x (Ricktopus) across 3+ channels.
4. **Fall Asleep To What A Psychologist Would Say About [Character]** — 13.2x (Rose Quartz), repeated on Pink Diamond, Lapis, Dipper, Tina across 3 channels. Slot: emotionally complex or traumatized characters.
5. **[X] Hours Of [Show] Lore To Fall Asleep To, But It's [Angle]** — 9.3x and 5.1x on small channels. Angles: Unsolved Mysteries, Dark Theories, Forgotten, Conspiracies, Hidden Details You Missed, Character Secrets, Life-Changing Lessons.
6. **Fall Asleep To Every [Show] Theory That Turned Out To Be True** — 6.1x (Gravity Falls), 5.0x (SpongeBob), plus hits on 2 bigger channels.
7. **Fall Asleep To The Entire Story Of [Character]** — 16.1x on a bigger channel (Entire Story Of The Simpsons + Theories), 3.9x on small ones. Slot: main characters, villains, or the whole show; "+ Theories" is a proven add-on; "The Entire [Show] Timeline" is a proven variant.

**Test slot (only when "Core 7 + test slot" is chosen; at most 1 in every 10 titles, placed toward the end of the numbered list):** high ceiling but not yet proven on small channels.
- Fall Asleep To The Philosophy Of [Character] (32.2x, Adventure Bedtime)
- Fall Asleep To How [Past Event] Caused [Later Event] (9.1x-25.1x, Midnight Marvel)
- Fall Asleep To The Hidden Lore Of [Place/Object] (16.5x, Abismo)
- [X] Hours Of [Show] Mistakes To Fall Asleep To (15.9x, Noctoon)

**Sleep Lore rules:**
- Do NOT apply the What If arrival-verb rules to this style. No crossovers.
- Weight formats 1 and 2 heaviest for new or small channels — both hit 17x+ on channels with only hundreds of subs.
- No single format above ~25% of the batch (with Top 4 only, ~30%), and never the same format twice in a row in the Numbered List.
- Fill [Character] slots with the show's most recognizable characters, villains and factions first.
- Every theory, mystery, power or event named must be real canon or a real, widely discussed fan theory. Never invent lore.
- "3 MORE Hours Of [Show] Lore" sequels only for a title that already hit on that channel (10.2x proven).
- Capacity: a mid-size show supports roughly 40-60 distinct Sleep Lore titles before repeats feel stale; deep franchises (Simpsons, SpongeBob, MCU) support 100+. Repeating a winner with a new number or slot is fine (e.g. 100 and 101 Simpsons Easter Eggs both hit). If the batch is larger than the show can support, say so before generating.
- If fresh outlier data in this session contradicts this ranking, the fresh data wins; say so in Step 1E.

In the Detailed List, tag each Sleep Lore title with its format number (SLEEP-1 to SLEEP-7) or TEST.

### RULES FOR STYLES 1-5
- Use arrival verbs: Landed in, Entered, Arrived in, Crashed Into, Trapped in, Judged, Challenged, Hunted [native anchor].
- Avoid: Destroyed, Ended, Erased, Replaced, Conquered, Instantly Defeated, "built X to kill [native]". Destroyer/replacement framing underperforms.
- Name the peak version when it sharpens the title (Worldbreaker Hulk, Injustice Superman).

### RULES FOR EVERY STYLE
- No real people.

## STEP 2: Generate Titles

Generate exactly the total titles needed (channels × videos per day × days). Write every title in the chosen style (and, for Sleep Lore, the chosen format set) and follow that style's rules above.

Rules for generation:
- Every title must combine at least 3 elements from proven top performers (the Twist Principle — proven ingredients, fresh combination). For Sleep Lore, the proven format itself counts as one element; the subject and angle should come from the data where possible.
- If the content is based on an existing fictional universe, TV show, historical events, or any factual source material: every premise must be grounded in at least one real, verifiable fact from that source. State the canon/factual basis briefly after each title. Do not invent lore, fake events, or attribute things to real people/characters that have no basis.
- No single character, subject, or person should appear in more than 25% of the batch (e.g. max 5 out of 20, max 17 out of 70).
- The batch must include at least 3-4 different emotional triggers (not all defiance, not all humor, not all nostalgia, etc.).
- Do not generate titles that match the anti-patterns identified in Step 1B.
- Do not reuse concepts flagged as dying in Step 1D.
- Each title should be a fresh combination — no title should duplicate a concept already in the provided data or another title in the batch.

## STEP 3: First Output — Detailed List

State the chosen style (and Sleep Lore format set, if used) and the slot math at the top. Group titles by their primary theme or format. Under each group header, list titles with reasoning:

```
[THEME/FORMAT NAME] ([#] titles)

[#]. [Title]
→ Proven elements: [which 3+ components from the data this combines]
→ Source basis: [the real fact/canon this diverges from — 1 sentence]
```

Only include the Source basis line if the content is based on existing source material.

After the detailed list, add:

**TOP 5 PREDICTED PERFORMERS** — Pick the 5 titles most likely to outperform based on the data patterns, and briefly say why (reference specific data points — outlier scores, cross-channel validation, proven elements).

## STEP 4: Print Distribution Formats

Continue straight on from Step 3 — do not stop to ask anything. Use the channels, videos per day and days from the Setup picker.

### Format A — Numbered List (ranked and spaced, for bulk copying)

The numbered list IS the distribution order. All ordering happens here before numbering. Order titles using these rules:
- **Best titles first** — highest-confidence predicted performers go to the top to get early traction.
- **Variety between consecutive titles** — no two back-to-back titles share the same secondary character/subject, emotional trigger, or premise format.
- **Experiments toward the end** — lower-confidence or unproven concept titles (including Sleep Lore TEST titles) go later in the list.

Just the titles, numbered, no reasoning, no headers, no annotations (no style tags). Designed for pasting into a spreadsheet or posting tool.

```
1. [Title]

2. [Title]

3. [Title]
...
```

### Format B — Setlist (grouped by channel)

Take the Numbered List in exact order and deal titles out sequentially across channels (title 1 → Channel 1, title 2 → Channel 2, etc., wrapping around). With more than 1 video per day, each channel gets that many titles per day before the day number advances. No re-shuffling — the numbered list already handles ordering and variety.

CRITICAL: Each title MUST be on its own separate line. Never put multiple titles on the same line. Use double line breaks (a blank line) between every entry — this is vital for the setlist to paste correctly. Each title gets its day label inline.

Example (10 channels, 1 video/day, first 2 channels shown):

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

The setlist example shows layout only; the actual titles follow whichever style was chosen.