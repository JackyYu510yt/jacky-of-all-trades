---
name: "destination-crossover-research"
description: "Use instead of crossover-angle-research: destination-locked What If crossover research. Picks destinations, angles, characters and titles from small-channel outlier proof and the user's validated rules."
---

# Destination Crossover Research

The user runs longform (1-3 hr), AI-narrated "What If [character] entered [universe]" channels. Target: 1.5-2.5K views per video, 75K+ views per channel per month, $20-40 RPM.

## The two terms

- **Destination** = the universe every video on a channel takes place in. Locked forever. It sets the channel's ceiling.
- **Angle** = the origin bucket the visiting characters come from (Anime, DC, Marvel...). One angle per channel.

Channel = one destination x one angle. Each S-tier destination can hold up to 5-6 channels, one per angle.

**Core rule: lock the destination, rotate the origin.** Same character, different destination, can be a 10-45x spread (Superman in Infinity War 135K vs Superman in Halo 2.9K).

## Evidence over procedure

The steps below are the default order of work, not a script. When this run's own data contradicts a default (a rule, a ratio, a title shape), follow the data and say in one line which default you overrode and why. Before writing titles, re-read the failure rules you found in THIS run and check every title against them. When evidence for a rule is confounded (different characters, one channel, few videos), call it unproven rather than proven, and test it instead of banning it.

## What counts as proof

A **destination-framed, narrated What If video on a channel under 30K subs**, with its outlier multiplier.

- Big channels, fight animations, official clips and Death Battle-style videos are **demand signals only**, never proof for a title. Raw views from big channels measure channel authority, not premise (Batman in Invincible: 200K on a large channel, 1.8K on small ones).
- Short-form (under ~25 min) What Ifs, even on small channels, are demand signals for a 1-3 hr format, not proof.
- **Bad-channel outlier method:** low-quality small channels that usually get low views but occasionally spike are the cleanest signal. When the same premise type spikes across several such channels (e.g. "spaceship enters Star Trek/Star Wars"), it's validated.

## Modes

- **Full research** (default): destinations/angles, characters, titles, doc.
- **Quick titles**: user wants the N best titles for a destination. Skip ranking and the doc; still run the failure rules, title gate and event-test spread. Answer in chat.
- **Character pick**: user gives destination x angle and wants the best 20 characters. Use the character bank + live check.

## Step 1 - Ask everything upfront

One round, with AskUserQuestion (plain text if unavailable):

1. **Destination** (or "recommend one").
2. **How many channels / which angles** - or "just titles".
3. **Title style(s)**: What If, Scene, Hybrid, Hybrid Full Mix.
4. **Titles per channel** (user has used 3, 7, 14, 30).

**Title style question - always show examples.** Ask it as a multiSelect question with the four styles as the four options. Under every option, show an example title so the user can see each style before choosing:

- Put one example title in each option's `description` (it shows under the label).
- Also put 2-3 example titles in each option's `preview`.
- When the destination is already known, write the examples for that destination (its native anchor and canon events). Otherwise use the defaults below.
- In plain text (no AskUserQuestion), list the four styles, then an **Examples** block at the bottom with one or two titles per style.

Default examples (Invincible):

- **What If** - What If Superman Entered The Invincible Universe? / What If Vegeta Landed On Viltrum?
- **Scene** - Superman Arrived The Night Omni-Man Killed The Guardians - And Was The Only One Left Standing By Morning
- **Hybrid** - What If Vegeta Landed During The Viltrumite War - And Thragg Realized Saiyans Don't Kneel?
- **Hybrid Full Mix** - mix of the two: What If Goku Entered The Viltrumite War - And Nolan Felt Fear For The First Time? / Saitama Crashed Into Chicago - And Conquest Never Got Back Up

Don't research until 1 and 2 are answered. If 3-4 are open, research first and ask again before titles (with the same examples, now written for the chosen destination).

## Step 2 - Timing check

Web-search the destination: latest release, next season/film/game with dates, spinoffs. Flag a trough plainly and name the next spikes. Note when most proof was posted (a hype window inflates medians). Note the destination's **native anchor** (e.g. Omni-Man, Homelander, Thanos) - it is the stakes or opponent, **never the subject**.

## Step 3 - Evidence

Start from the reference data below, then refresh live.

1. **Seed channels first.** Pull recent videos from the seed list (bottom of this file) with Algrow `get_channel_videos` (try `sort: popular` too) and re-check views/outliers for the destination.
2. **Algrow `search_viral_videos`** (longform and shorts) with `max_subs: 30000`; record title, views, outlier, handle. Pass a seed channel's handle as `search` to find similar outliers. To get multipliers for a set of known small channels, pass their IDs as `channel_ids` with the destination as `search`, `min_video_views` ~500 and `uploaded_within_days` ~730. If it fails twice, fall back to `youtube_search` and check sub counts before counting anything as proof; say so.
3. **Algrow `youtube_search`** (`sort_by: view_count`, `type: video`), destination-framed only: "[origin] in [destination]", "what if [origin] entered/landed in [destination]", plus sub-destination nouns (table below). Never use "[anchor] vs [character]" as a proof query - it returns fight animations.
4. **AO3 / FanFiction.net** crossover counts as secondary demand signals. Note unreachable sources as gaps.
5. Look up release timing for the top origin universes too.
6. **Event-framing check:** collect every small-channel video in this destination whose title names a canon event, and compare it with plain arrival titles of similar-strength characters. Record the result as proven-up, proven-down or unproven.

**Staleness rule:** for a destination not in the reference data, the first 3 uploads are the test; don't assume bucket performance transfers.

| Destination | Sub-destination search nouns |
|---|---|
| Invincible | Viltrum, Viltrumite War, Omni-Man, Thraxa, GDA |
| The Boys | Vought, Homelander, The Seven, Compound V |
| DC | Injustice, Gotham, Metropolis, Themyscira, Arkham |
| Marvel | Infinity War, Endgame, X-Men, Wakanda, Asgard, Titan |
| Star Trek | Federation, Enterprise, TNG, Voyager |
| Game of Thrones | Westeros, Beyond the Wall, King's Landing, the Long Night |
| Warhammer 40K | Imperium of Man, 41st Millennium, Cadia, the Warp, Golden Throne |

## Step 4 - Score with the 12 variables

Use these, in rank order, to judge destinations and premises:

1. **Destination** - sets the ceiling. Pick it first.
2. **Destination saturation** - a passionate, under-served destination beats a crowded one (Underworld, Stargate vs Star Wars).
3. **Character-destination thematic fit** - does the character's core nature create a problem in this world? (Predator in Underworld 55K vs Predator in Walking Dead 8.9K, same channel.) "Powerful guy shows up" is not a premise.
4. **Crossover type** - universe-vs-universe (fleet, civilization, faction) has a higher ceiling at 1-3 hr than a solo drop (BSG in Star Trek 117K, 91x).
5. **Origin recognition** - most recognizable character that still creates tension (Dr. Doom 32K vs Spider-Man 2099 2.1K in The Boys).
6. **Fandom overlap** - shared audiences (Harry Potter x Percy Jackson 19K, #1 on its channel).
7. **Tonal contrast** - a tonally wrong character sells in the title (Deadpool in DC 17K vs Deadpool in The Boys 3.6K).
8. **Power dynamic** - "could break this world" or "genuinely at risk"; pure stomp with no tension fails.
9. **Tone match vs contrast** - go hard either way; neutral pairings are lowest.
10. **Origin fandom size** - matters less than expected.
11. **Character count** - solo beats teams for single invasions; civilizations beat solo for universe-vs-universe.
12. **Version** - name the peak version (Worldbreaker Hulk, Injustice Superman) - sharpens title and thumbnail.

## Step 5 - Rank angles by ceiling AND floor

Angles: **S-tier** Anime, DC, Marvel. **A-tier** Gaming/Mythology/Gods, Sci-Fi, Movie/TV characters. Also valid where supported: **Horror** (e.g. Gotham; SCP entries count), **Versions** (specific variants of heroes for dedicated fans - see @IFPortal-comix), **Civilizations/Ships** (sci-fi destinations). One channel per angle; never subdivide thematically ("Gods, Demons & Cosmic Beings" fragments a validated bucket).

For each destination x angle: ceiling (top small-channel video), floor (median of every qualifying video found, not just hits), count of videos 5K+, outlier, competition.

- High ceiling AND high floor -> launch first.
- High ceiling, thin volume -> real angle; test 2-3 videos before a dedicated channel.
- No video above ~4K -> not an angle, cut it.
- High outlier, low absolute views -> premise works, audience small; test first.
- **Idea depth test:** need 100+ viable video ideas for the destination x angle. Fewer -> merge angles or skip.

Flag overlapping angle pairs (Marvel/DC) so channels don't compete. Give each cross-angle character (Ghost Rider, Lucifer, Alucard, Spawn) exactly one home channel.

## Step 6 - Failure rules (apply BEFORE writing titles)

| Rule | Evidence | Applies to |
|---|---|---|
| Street-level origins die where raw physicality is the currency | Batman in Invincible 1.8K; Batman & Spider-Man in Invincible 504 | Invincible, WH40K, Dragon Ball-tier |
| Street-level and joke origins underperform even in grounded destinations | The Boys: Kick-Ass 860, Puri Puri Prisoner 1.4K, Spider-Man 2099 3K, Black Panther 4.3K (0.27x) | The Boys and similar |
| Native character is never the subject - the outsider arrives | Superman landed in Gotham 934; Harley Quinn in DC 499; Batman folds Goku 379 | All |
| "Replaced [native]" framing makes the native the subject | Tifa Replaced Homelander 2.5K | All |
| Native anchors work as visitors elsewhere, not at home | Homelander in WH40K 22K; put him in WH40K/Invincible/IW, not The Boys | All |
| Tech-heavy origins underperform in medieval/magic settings | Iron Man in GoT 2.4K; Terminator in GoT 3.2K | GoT, Harry Potter |
| Destroyer framings lose to arrival framings | Thanos destroyed DC 598; "One Punch Was Enough to End the Marvel Universe" 639 vs "Goku Entered the Marvel Universe" 32K; The Boys: Saitama Ended Vought 6.9K vs Saitama Landed 23K | All |
| Fanservice-led picks cap near 4-5K unless they can physically threaten the native anchor | The Boys: Makima 3.6K, Kurumi 3.5K, Boa Hancock 3.3K, Tifa 2.5K vs Power Girl 15.8K, Tatsumaki 10.6K | Anime, Gaming |
| Isekai and cute-gaming origins underperform in power-scaling worlds | Rimuru in Invincible 3.4K; Kirby 3K; Escanor 2K; Izayoi 956 | Invincible |
| Anime is thin in hard sci-fi; sci-fi origins dominate | Naruto in Star Trek 1.3K, Gohan 897 vs BSG 117K | Star Trek, Stargate, Star Wars |
| Teams fail where solo arrivals win | Justice League in Star Wars 1.4K vs Superman 53K | Star Wars (check elsewhere; JL did 33K in The Boys) |
| A locked origin gimmick flattens every destination | Saitama-only channel: 800-2K everywhere | Channel design |
| Deadpool-type comedic chaos needs a serious destination | Deadpool DC 17K vs Boys 3.6K | Tonal-contrast characters |
| "Short version" cut-downs collapse | The Boys: SCP-096 at 2.2 hr 7.7K vs a 36-min short version 1.1K | Format |

**Unproven, test don't ban - canon-event framing.** The Boys, one channel: plain Power Girl 15.8K and Supergirl 14.2K vs event-framed Luffy 5.5K, Bayonetta 5.5K, Saber 3.7K. Confounded: the event titles used weaker picks. Run it as a spread test (Step 8), never with a weak character.

**Preferred verbs:** Landed in, Entered, Arrived in, Crashed Into, Trapped in, Judged, Challenged, Hunted [anchor] (Battle Beast Hunted Homelander 11.5K). **Avoid:** Destroyed, Ended, Erased, Replaced, Conquered, Instantly defeated, "built X to kill [anchor]".

Add any new pattern the fresh data shows (a premise type repeatedly under ~2K). New patterns found in this run outrank defaults elsewhere in this file.

## Step 7 - Characters per channel

- **Proven picks:** small-channel destination-framed video exists, with views + multiplier.
- **Canon-extension picks:** validated elsewhere (character bank or another destination's proof) + a strong fit for this destination.
- Pick by matchup and fit, never popularity alone; drop anything breaking Step 6.
- Rank proven picks by views and multiplier; this ranked list is what titles draw from.

## Step 8 - Titles

Plan each channel's first 15 uploads as one run; a shorter batch (3, 7) is the front of that run.

**Fill order and spread:**

1. **Slots 1-3: the three strongest proven picks, plain arrival titles.** Never an experiment in the first three.
2. **Event-framed tests, spread through the run** (unless Step 3's event check came back proven-up or proven-down):
   - **3 tests in the first 15**, at roughly slots 5, 10 and 14; at least 4 slots apart; never back to back.
   - **Short batches:** a 7-title batch carries 1 test (slot 5 or 6); a 14-title batch carries 2; a 3-title batch carries none.
   - **Each test uses a proven pick from the top half of that channel's ranking**, so a miss can't be blamed on the character. No fanservice, street-level or joke picks.
   - **Each test uses a different canon anchor** (e.g. martial law, Flight 37, Herogasm), so the run shows which events pull, not just whether events pull.
   - **Spread across characters too:** a character used in a test never appears in a plain title within 3 slots of it.
   - Mark each in the doc as **(event test)**, with its canon basis.
3. **Everything else: proven picks in plain arrival form**, strongest first, then **canon extensions in plain form**. Across the 15, aim for roughly 60/40 proven/extension; when the proven bench is deep, lean further toward proven.
4. **Proven-up:** if Step 3 found event titles beating plain ones in this destination, use up to 2 per 7. **Proven-down:** if they clearly lost with comparable characters, use none.
5. Never invent a premise with neither proof nor a validated character.

**Readout (put this in the doc's governance section):** after video 15, compare the median of the 3 event tests with the median of the channel's plain titles. At or above the plain median -> raise to 2 per 7 for that destination. Below half of it -> drop event framing there. In between -> run 3 more.

Proven titles first, marked with views + multiplier of the proof. Same numbering across styles. Put unverified older-scrape picks later in each channel's order than re-verified ones.

| Destination | Canon anchors |
|---|---|
| Invincible | Guardians of the Globe massacre, the Chicago fight, the Viltrumite War, the Invincible War, Thraxa, Conquest's arrival |
| The Boys | Vought, Homelander's rise, Herogasm, martial law, Compound V, Flight 37, Vought Rising (1950s) |
| Marvel | Infinity War, the Snap, Endgame, Battle of Titan, Civil War, Battle of Wakanda |
| DC | the Injustice Regime, Darkseid's invasion, the Long Halloween, Arkham breakout |
| Game of Thrones | War of the Five Kings, the Red Wedding, the Long Night, Beyond the Wall |
| Warhammer 40K | the Golden Throne, Cadia, the Warp, Horus Heresy, a Tyranid hive fleet |
| Star Wars | the Clone Wars, the Death Star, Order 66, the Outer Rim, Naboo |

### Four title styles

1. **What If** - short question. *What If Superman Entered The Invincible Universe?*
2. **Scene Style** - [Character] [did one specific thing] - And [consequence]. Past tense, em dash, payoff often time-stamped. No "What If". *Superman Arrived The Night Omni-Man Killed The Guardians - And Was The Only One Left Standing By Morning*
3. **Hybrid** - opens "What If", plays out scene style, ends in a question mark. *What If Vegeta Landed During The Viltrumite War - And Thragg Realized Saiyans Don't Kneel?*
4. **Hybrid Full Mix** - big matchups get the Hybrid opener, story premises stay Scene Style; ~12-15 of every 30 lead with "What If".

Scene and Hybrid styles carry a scene by design; the event-test spread applies to What If style.

New style requested -> show 2-6 examples for approval first.

### Title gate (every title)

- [ ] Locked destination; the outsider is the subject.
- [ ] Arrival verb; no destroyer or replacement framing.
- [ ] Breaks no Step 6 rule, including new rules found in this run.
- [ ] Cites a small-channel proof video OR a validated character with a stated fit.
- [ ] No plain canon-extension slot is used while a stronger unused proven pick exists for that channel.
- [ ] Event tests follow the spread (position, top-half character, unique anchor, marked).
- [ ] Peak version named where it sharpens the title.
- [ ] No real people.

Rewrite or drop failures; don't just flag them.

### Self-check before output

Re-read the finished title lists as if seeing them fresh, with only the doc's conclusions in mind. Would someone reading just the failure rules and proven-pick rankings write the same titles? If not, revise.

## Step 9 - Channel name + thumbnail family

- The name must signal every upload. Pass: "Gotham What If" (Horror x DC), "The Fractured Realm" (DC x Invincible). Fail: "Wayne Rewritten" (implies Batman as subject), "Amazons Altered" (implies untested Themyscira).
- Note the thumbnail config family: **Comic Book** (The Boys, Invincible, DC, Marvel, IW); own configs for **Star Trek** (spaceship-led), Star Wars, Walking Dead, WH40K, etc. Reference thumbnails come from the best small channel running that destination, mixing angles. Give overlapping angles (DC/Marvel) different dominant colours.

## Output (full research)

A doc the user can keep and edit:

1. **Bottom line** - channels in launch order + timing caveat.
2. **Timing check** table.
3. **Angles ranked** - rank, angle, ceiling (linked, views, multiplier), floor, competition, idea-depth estimate, decision rule. Overlap warning.
4. **Failure rules for this destination** (and the event-framing check result).
5. **Characters per channel** - proven + canon-extension.
6. **Top 3 titles per channel** with proof links.
7. **Angles cut** with numbers.
8. **Channel name + thumbnail family.**
9. **Data gaps + launch governance** (below), including the event-test readout.
10. **Title lists** - one section per style, one subsection per channel, event tests marked. Note any default overridden by this run's data.

"Paste" requests -> short ranked list in chat.

## Launch governance

- Phase 1: S-tier destinations, highest-confidence angle each. Phase 2: A-tier after Phase 1 has seasoned.
- Season 10-15 videos over 60-90 days before judging.
- **Kill:** under 2K median at video 15 (the older note said under 1K average; use 2K median as the bar and mention the 1K floor as the hard stop).
- **Scale:** 5K+ median -> double down.
- **Event-test readout** at video 15, per Step 8.

## Reference data (scraped 2026-06-25; 1,854 videos, 24 mostly sub-30K channels)

Refresh live; say when numbers are from.

### User's tiers

- **S destinations:** The Boys, Invincible, DC, Marvel, Star Trek, Infinity War/Endgame (Star Wars was S in an earlier note, A in later ones - treat as A).
- **A destinations:** Game of Thrones, Walking Dead, Warhammer 40K, MHA, Underworld, Stargate, Harry Potter, Supernatural.
- **Watch:** Percy Jackson (timing play), Predator Planet, John Wick Underworld, Hazbin Hotel.

### Destination floors from the scrape (destination-framed titles only)

| Destination | Videos | Median | Peak | Videos 5K+ |
|---|---|---|---|---|
| Infinity War/Endgame | 8 | 13K | 135K (43x) | 6 |
| Underworld | 19 | 8.7K | 87K (26.8x) | 10 |
| Marvel | 73 | 4.5K | 134K | 32 |
| Walking Dead | 27 | 4.5K | 22K | 10 |
| DC (incl. Injustice/Gotham) | 121 | 3.6K | 86K | 47 |
| Harry Potter | 61 | 3.6K | 32K | 26 |
| MHA | 42 | 3.5K | 23K | 19 |
| Invincible | 35 | 3.4K | 66K (6.6x) | 13 |
| Warhammer 40K | 260 | 2.8K | 259K | 98 |
| The Boys | 273 | 2.7K | 62K | 100 |
| Game of Thrones | 50 | 2.7K | 18K | 16 |
| Supernatural | 9 | 1.6K | 77K | 3 |
| Stargate | 63 | 1.6K | 32K | 9 |
| Star Trek | 118 | 1.5K | 117K (91x) | 15 |
| Star Wars | 198 | 1.2K | 60K | 21 |

Star Trek, Stargate and Supernatural are hit-driven (huge peaks, low medians): the hits are universe-vs-universe ships/civilizations or a perfect-fit character. Solo character drops there floor low.

### Destination x angle anchors

- **Invincible** - DC: Superman 66K (6.6x), Justice League 14K (3.1x), Superboy Prime 7.7K (2.5x). Anime: Vegeta 12K (4.2x), Saitama 12K & 11K, Goku 9.8K (2.9x), Beerus 9.2K (2.6x), Frieza 7.7K, Jiren 7.3K, Broly 7.1K. Cut: Gaming/Myth, Sci-Fi (Kirby 3K, Alien X 1.9K, Rick Sanchez 2.3K).
- **The Boys** (refreshed 2026-10-20) - DC: Black Adam 59K (15.8x), Superman & Batman 33.9K, Justice League 33K (6.2x, Jun), Flash 21.9K, Darkseid 19.7K, Superman 17.7K (4.36x), Injustice Regime 17.2K, Power Girl 15.8K (3.24x), Lucifer 15.3K (2.85x), Supergirl 14.2K, Lobo 10.1K (2.96x). Marvel: Wolverine 62K (4x, Jun), Dr. Doom 49K (3.35x), Worldbreaker Hulk 32.9K, Ghost Rider 23K (5.62x), Sentry 19.2K, Iron Man 16.9K, Loki 14.5K, Scarlet Witch 12.9K, Fantastic Four 12.6K. Anime: Goku 110K (29.7x), Goku & Vegeta 41.8K (10.6x), Saitama 23K (3.93x), Ainz 16.2K, Garou 13.7K, Tatsumaki 10.6K, Sung Jin-Woo 10.5K. Gaming: Doom Slayer 21.9K (5.89x), Sub-Zero 12.8K (2.51x), Archie Shadow 10.7K (3.22x), Scorpion 10.3K (2.15x), Archie Sonic 8.8K, Sarah Kerrigan 7.3K. Horror & SCP: Spawn 27.7K, Alucard 13.5K (3.75x), SCP-049 9.5K, SCP-096 7.7K, SCP-173 5.1K. Movie/TV & Sci-Fi: Darth Vader 13K (9.2x, Jun), Omni-Man 12.5K, Battle Beast 11.5K (2.16x), Godzilla 10K (Jun), Rick Sanchez 8.7K. Launch order found: DC, Anime, Marvel (60+ days after DC), Gaming; Horror & SCP and Movie/TV & Sci-Fi as tests. Event framing: unproven (see Step 6). Suggested event tests: Injustice Superman During Homelander's Martial Law (DC), Vegeta During Martial Law (Anime), Thor The Day Flight 37 Went Down (Marvel). Most proof posted Dec 2025-Mar 2026 (Season 5 hype); show ended May 20, 2026; Vought Rising due 2027.
- **DC** - Anime x Injustice: Vegeta 22K (8.7x), Saitama 17K (4.5x), Beerus 9K. Anime x DC: Saitama 24K, Beerus 24K, Goku 18K, OPM vs Darkseid 17K (6x). Marvel: Avengers 29K (16.4x), Deadpool 17K, Spider-Man 13K. Horror x Gotham: Alucard 15K/14K/9.1K, Michael Myers 8.7K (3.4x), Ghost Rider 9.9K.
- **Marvel** - Sci-Fi: Emperor of Mankind 134K (8.6x), Space Marine 40K. DC: Superman 34K (12.3x), Batman 13K (10.3x). Anime: Goku 32K (9.9x) & 15K (12.8x), Rimuru 25K, Saitama 19K.
- **Infinity War/Endgame** - DC: Superman 135K (43.2x), Justice League 39K & 24K, Darkseid 23K. Anime: Saitama in Endgame 3.9K (weak; frame the event as setting).
- **Star Trek** - Sci-Fi/civilizations: BSG 117K (91x), UNSC Infinity 11K (5.9x), Q gave Stargate Command a starship 16K (12x). DC: Superman 57K (7.8x), Green Lantern 12K. Sci-Fi characters: Yoda 30K. Movie/TV: Sheldon Cooper 5.3K (3.6x).
- **Star Wars** - Sci-Fi: UNSC Infinity 60K (32x), Master Chief 22K (11.8x), Sanguinius 18K. DC: Superman 53K (57x). Marvel: Black Adam 11K (9.7x). Test: Goku met the Jedi 9.6K (7.2x).
- **Warhammer 40K** - DC: Superman 259K (9.1x), Homelander 22K, Justice League 17K. Anime: OPM 147K, Goku 95K, Vegeta 47K, Ainz 35K (9.6x). Gaming/Myth: Doom Slayer 131K, Optimus Prime 59K, Master Chief 50K, Kratos 46K. Sci-Fi: Darth Vader 92K, Doctor Manhattan 71K (7.4x).
- **Underworld** - Marvel: Blade 87K (26.8x) & 58K (13x), Wolverine 18K. Movie/TV: Predator 55K (10.3x). Anime: Alucard 17K & 14K.
- **Game of Thrones** - Gaming/Myth: Kratos 18K + 5.9K, Guts 8.5K. Marvel: Deadpool (Red Wedding) 12K (3.8x), Wolverine 11K. Anime: Sung Jin-Woo 5K (5.5x).
- **Walking Dead** - Movie/TV: John Wick 22K, Terminator 13K. Marvel: Wolverine 14K, Punisher 13K.
- **Harry Potter** ("raised by"/arrival format) - Marvel: Doctor Strange 32K (5.3x), Tony Stark adopted Harry 8.2K. Anime: Rimuru 15K, Ainz 12K, Frieren 8.1K (8.8x). Fandom overlap: Percy Jackson 19K (9.1x). DC: Lucifer 23K.
- **MHA** - Marvel: Spider-Man 23K, Ghost Rider 20K (5x), Iron Man 16K (4.2x). DC: Justice League 18K, Superman 17K. Gaming: Metal Sonic 12K (55.7x), Shadow 4.5K (20.5x).
- **Supernatural** - DC: Lucifer 77K (13x). Marvel: Doctor Strange 12K. Thin volume; test first.
- **Stargate** - Sci-Fi: USS Voyager 32K (24.8x), Star Trek found a Stargate 29K (13.1x), UNSC Infinity 9.4K. Marvel: Avengers 9.5K (3.9x).

### Character bank (top picks per angle; full list in user's master list)

- **Anime:** Goku (deepest idea supply), Saitama (but don't lock a channel to him), Alucard/Hellsing (dark-anime identity), Vegeta, Ainz, Rimuru (avoid in Invincible), Beerus, Gojo, Sung Jin-Woo, Broly, Frieza, All Might, Frieren, Guts, Garou.
- **DC:** Superman (highest ceiling), Injustice Superman (distinct version), Lucifer, Black Adam, Justice League, Darkseid, Superboy Prime, Wonder Woman, Power Girl, Supergirl, Flash, Green Lantern, Lobo; Batman only in non-power-scaling destinations.
- **Marvel:** Ghost Rider, Wolverine, Blade, Thor, Deadpool (serious destinations), Worldbreaker Hulk (always this version), Dr. Doom, Doctor Strange, Punisher, Magneto, Iron Man, Sentry, Loki.
- **Gaming/Myth/Gods:** Doom Slayer, Kratos, Master Chief/UNSC Infinity, Predator, Optimus Prime, Sub-Zero, Scorpion, Archie Shadow/Sonic, Cthulhu, Odin, Dante.
- **Sci-Fi:** BSG fleet, Emperor of Mankind, UNSC Infinity, Doctor Manhattan, Darth Vader, Space Marines, Yoda/Jedi Council, Rick Sanchez, Judge Dredd, Borg.
- **Movie/TV:** Predator, Agent 47, Godzilla (Legendary), Rambo, John Wick, Terminator, Leon Kennedy, Michael Myers, Spawn, Sheldon Cooper, Constantine, Sherlock Holmes, Omni-Man/Battle Beast (outside Invincible).

## Seed channels (re-check these first)

@variantuniverses (did not resolve in Algrow on 2026-10-20), @MultiverseExplorer-2k01, @GalacticGate-u8s, UCSNhkKZOQrmouGA-EO15hew (Warhammer Theorist), UCHC6XXSwUfLM2u8LGra2L8Q, UCjfboemmvfzr3ifcOY64ATA (Multiverse Crossover - Boys/Invincible/Injustice), @InfiniteMultiverseIf-n1v, @LoreTheorists, @crossover_lore, @TheGrimdarkNexus, @WARHAMMERTALE, @CROSS_HARRY_P, UCBLi7Tqa_nSNMSA-voiNU1w, @GODDESsFICTION, @LoreActrossGalaxies, @nindopiece, @TheLorebinder, @StarVerseX, @JediLords, @MultiverseGalaxyIf, @MultiverseTheories-r4x, @Behindcloseddoors-k7k, @MythsoftheMultiverse, @ImperiumsWounds, @AzeRoth24-p7c, @IFPortal-comix (versions angle - user flagged as super high potential), @GateChronicles-q5g and @LegendsRebornNetwork-s8f (bad-channel outlier validation for ship-in-Star Trek/Star Wars), @Sungod9548 (Cursed Domain - large short-form, demand signal only), UC4vpVO2OkIndUWyk1OGWrCA (Galaxy If Multiverse - Goku in The Boys 110K).

## Principles

- Every ranking claim needs a number; proof numbers come from small channels with a multiplier. Label big-channel numbers as demand signals.
- When this run's data contradicts a default in this file, follow the data and say so; when the evidence is confounded, test instead of banning.
- When the user's notes conflict, follow the newer note and say which you used.
- Say plainly when a source failed or data is stale.
- Link proof videos as https://www.youtube.com/watch?v=<video_id>.