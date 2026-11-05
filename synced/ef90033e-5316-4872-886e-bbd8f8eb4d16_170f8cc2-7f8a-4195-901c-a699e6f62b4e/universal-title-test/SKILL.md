---
name: "universal-title-test"
description: "Test a scraped YouTube channel's titles for the Universal Horizontally Scalable Titles bank: find speculative outliers, template them, stress-test on four franchises, update the bank JSON."
---

# Universal Title Test

The user runs speculative "what if" lore channels across many franchises. They keep a bank of title templates that work on ANY franchise (the Universal Horizontally Scalable Titles list). This skill takes one channel's video list and decides which of its titles join the bank.

## Inputs

1. **The channel's videos.** Usually a pasted scrape in this format:
   ```
   [12] Title here
       Views: 18k views | Duration: 18:25 | Posted: 3 weeks ago | Outlier: 2.1x | VPH: 4 VPH
   ```
   If the user gives only a channel URL, pull its videos with the Algrow tools and write them into that format. Those tools are deferred, so load them with ToolSearch first. Get the outlier scores from Algrow too; never estimate them.
2. **The bank**: `universal_titles_bank.json`, attached by the user. If none is attached, ask for it once. If they don't have one, start an empty bank: `{"meta": {"name": "Universal Horizontally Scalable Titles", "version": "1.0"}, "slots": {}, "templates": [], "global_rules": [], "rejected": []}`.

Work on a copy of the bank in the working directory, never the upload.

## Step 1: Write the scripts

Write `parse_scrape.py` and `apply_decisions.py` from the code blocks at the end of this file into the working directory, exactly as given.

## Step 2: Parse

Save the scrape to `scrape.txt` and run:

```
python3 parse_scrape.py scrape.txt > candidates.json
```

This gives you:
- **qualifying**: speculative titles at 3x+ outlier OR 150K+ views, at any age. They are sorted with `small_channel_proof` first.
- **flops**: speculative titles with no outlier score, at least 14 days old.
- **non_speculative_outliers**: listicles and other formats. List these in the report; don't test them.

### Tags
- **small_channel_proof**: implied baseline (views ÷ outlier) under 20K at 5x+. This is the strongest premise evidence, because the idea performed without a big audience behind it. Weight it highest.
- **still_hot**: 100+ views per hour.
- **mega_outlier**: 10x+.

Speculative means the title opens with What If / Why / What Happens / What Happened / What REALLY / How Did / Could / Can / Would. If a qualifying title is clearly speculative but the regex missed it (e.g. "Every Time X Almost..."), add it by hand.

## Step 3: Identify the source franchise

This is usually obvious from the titles. If the channel covers several franchises, set `source_franchise` per title by splitting the decisions into one file per franchise.

## Step 4: Template each qualifying title

Strip every franchise-specific noun into a slot. Reuse the bank's existing slot names whenever they fit. These are the starting slots:

| Slot | Meaning |
|---|---|
| FRANCHISE | Franchise name as fans search it |
| WORLD | The in-universe society or faction |
| UNIVERSE | The whole setting, for origin titles |
| ENDING | The definitive ending; use "[HERO] Dies" for franchises with no ending |
| CHARACTER_GROUP | Broad cast group (Character, Avenger, Cullen) |
| VILLAIN_FAMILY | Antagonist family with survivors |
| HATED_CHARACTER | Disliked character who survived or got off easy |
| MAIN_VILLAIN | Central villain |
| HERO | Protagonist |
| UNDERDOG_FAMILY | Poorest or most underestimated family |
| OUTSIDE_FORCE | Real-world force (A Modern Army, Humans) |
| POWERFUL_GROUP / WEAKER_WORLD | A dominant faction and who it could conquer |
| BROKEN_ITEM | The single most overpowered item; use once per franchise |

Add a new slot only when none of these fits, and give it a one-line description in `new_slots`.

Then classify each title:
- **match**: its template is already in the bank, even if the wording differs slightly. Matching is by meaning: "What Happened to EVERY X" matches "What Happens To EVERY X". Add it as proof.
- **new**: a template the bank doesn't have.
- **not templatable**: the premise depends on something only this franchise has (a hidden world inside ours, a magic school, a specific object). Put it in `rejected` with a reason. Also check the bank's `rejected` log first, so a title rejected before isn't re-tested.

## Step 5: Stress-test new templates

Fill each new template for all four test franchises, using these slot values. If a new slot is needed, choose the best value for that franchise.

| Slot | game_of_thrones | twilight | dc | marvel |
|---|---|---|---|---|
| FRANCHISE | Game of Thrones | Twilight | DC | Marvel |
| WORLD | Westeros | The Vampire World | The Justice League | The Avengers |
| UNIVERSE | Westeros | Vampires | The DC Universe | The Marvel Universe |
| ENDING | Game of Thrones Ended | Breaking Dawn | Batman Dies | Endgame |
| CHARACTER_GROUP | Character | Cullen | Hero | Avenger |
| VILLAIN_FAMILY | The Lannisters | The Volturi | The League of Assassins | The Black Order |
| HATED_CHARACTER | Bronn | Jacob | The Joker | Star-Lord |
| MAIN_VILLAIN | The Night King | Aro | Darkseid | Thanos |
| HERO | Jon Snow | Bella | Superman | Peter Parker |
| UNDERDOG_FAMILY | The Starks | The Swans | The Kents | The Parkers |
| OUTSIDE_FORCE | A Modern Army | Humans | The US Military | A Modern Army |
| POWERFUL_GROUP | The Targaryens | The Volturi | Superman | Asgard |
| WEAKER_WORLD | Essos | The Human World | Earth | Earth |
| BROKEN_ITEM | Wildfire | Vampire Venom | Lazarus Pits | Pym Particles |

Rate each filled title honestly:
- **S**: an instant click. The slot fits naturally, and fans already argue about it.
- **O**: it works, but the slot is a stretch or the stakes are lower.
- **W**: the slot doesn't exist in that franchise, or the premise is false. Examples: "Why Westeros NEVER United" when they did unite, or "bring back" a villain who never died. Comic deaths don't stick, so death-based premises are W for DC.

Read the filled title aloud. Rate the title as written, not what it could be with a better slot value. If a different value would rescue it, say so in `notes`.

Tiers are computed from the score (S=2, O=1, W=0, max 8):
- 7–8 → **universal**
- 5–6 → **conditional**. Write a `condition` naming what a franchise needs, e.g. "a definitive ending", "deaths that stick", "a villain family with survivors".
- 0–4 → **franchise_specific**. It stays in the bank, but off the universal list.

## Step 6: Anti-proof

For each flop, check whether it is a weaker variant of a bank template. If it is, add it as `anti_proof` with a one-line lesson about what killed it: phrasing ("Could X beat Y"), shrunken stakes, a narrowed theme, a repeated BROKEN_ITEM, or a beloved character in a hated-character slot. Flops that match nothing are skipped.

Also derive any new rule worth adding to `global_rules`, and add it directly to the bank copy.

## Step 7: Apply

Write `decisions.json` in the shape documented at the top of `apply_decisions.py`. Copy views, outlier, vph and tags from `candidates.json`; never retype numbers. Then run:

```
python3 apply_decisions.py universal_titles_bank.json decisions.json
```

The script dedupes proof, refreshes tags, and upgrades a template to `cross_validated` when proof arrives from a second franchise. It also bumps the version and logs the run.

## Step 8: Report and deliver

Send the updated bank file back. In the reply, give:
- **New universal templates**, each with its four test titles and score. Lead with these.
- **New conditional and franchise_specific templates**, with their conditions.
- **Upgrades to cross_validated.** This is the most important signal over time, because it means a template has worked on two franchises.
- **Anti-proof lessons learned.**
- **Non-speculative outliers worth a separate look.** Note especially small_channel_proof listicles; the user may want a listicle bank later.
- **Bank totals by tier.**

Keep the report short. Give a table of new templates, one line per upgrade, and one line per lesson.

## parse_scrape.py

```python
#!/usr/bin/env python3
"""Parse a YouTube channel scrape into candidates for the universal title test.

Usage: python3 parse_scrape.py SCRAPE.txt [--min-outlier 3] [--min-views 150000] > candidates.json

Accepts the scraper format:
  [12] Title here
      Views: 18k views | Duration: 18:25 | Posted: 3 weeks ago | Outlier: 2.1x | VPH: 4 VPH
"""
import argparse, json, re, statistics, sys

SPECULATIVE = re.compile(
    r"^(what if|why|what happens|what happened|what really|how did|how does|how do|"
    r"could|can|would|what would|is|are|did|does|who would)\b", re.I)
UNIT_DAYS = {"second": 1 / 86400, "minute": 1 / 1440, "hour": 1 / 24, "day": 1,
             "week": 7, "month": 30, "year": 365}


def parse_views(s):
    m = re.match(r"([\d.,]+)\s*([kmb]?)", s.strip().lower())
    if not m:
        return None
    return int(float(m.group(1).replace(",", "")) * {"": 1, "k": 1e3, "m": 1e6, "b": 1e9}[m.group(2)])


def parse_outlier(s):
    s = s.strip()
    m = re.search(r"([\d.]+)\s*x", s)
    return float(m.group(1)) if m else None  # ">100x" -> 100.0, "--" -> None


def parse_age(s):
    m = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year)", s.lower())
    return round(int(m.group(1)) * UNIT_DAYS[m.group(2)], 2) if m else None


def parse(text):
    url = (re.search(r"^URL:\s*(\S+)", text, re.M) or [None, None])[1]
    videos, current = [], None
    for line in text.splitlines():
        head = re.match(r"^\s*\[(\d+)\]\s+(.+?)\s*$", line)
        if head:
            current = {"idx": int(head.group(1)), "title": head.group(2)}
            videos.append(current)
            continue
        if current and "Views:" in line:
            fields = {}
            for part in line.split("|"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    fields[k.strip().lower()] = v.strip()
            current["views"] = parse_views(fields.get("views", ""))
            current["outlier"] = parse_outlier(fields.get("outlier", ""))
            vph = re.match(r"([\d.]+)", fields.get("vph", ""))
            current["vph"] = float(vph.group(1)) if vph else None
            current["age_days"] = parse_age(fields.get("posted", ""))
            current["duration"] = fields.get("duration")
    return url, videos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scrape")
    ap.add_argument("--min-outlier", type=float, default=3.0)
    ap.add_argument("--min-views", type=int, default=150_000)
    ap.add_argument("--small-baseline", type=int, default=20_000,
                    help="implied baseline below this + outlier >= 5x = small_channel_proof")
    a = ap.parse_args()

    url, videos = parse(open(a.scrape, encoding="utf-8").read())
    views = [v["views"] for v in videos if v.get("views")]
    out = {"channel": url, "videos_parsed": len(videos),
           "channel_median_views": int(statistics.median(views)) if views else None,
           "thresholds": {"min_outlier": a.min_outlier, "min_views": a.min_views},
           "qualifying": [], "non_speculative_outliers": [], "flops": []}

    for v in videos:
        v["speculative"] = bool(SPECULATIVE.match(v["title"]))
        o, n = v.get("outlier"), v.get("views") or 0
        v["implied_baseline"] = int(n / o) if o else None
        tags = []
        if o and o >= 5 and v["implied_baseline"] and v["implied_baseline"] < a.small_baseline:
            tags.append("small_channel_proof")
        if (v.get("vph") or 0) >= 100:
            tags.append("still_hot")
        if o and o >= 10:
            tags.append("mega_outlier")
        v["tags"] = tags
        qualifies = (o or 0) >= a.min_outlier or n >= a.min_views
        if qualifies:
            out["qualifying" if v["speculative"] else "non_speculative_outliers"].append(v)
        elif v["speculative"] and o is None and (v.get("age_days") or 0) >= 14:
            out["flops"].append(v)

    # Strongest premise proof first: small-channel hits, then raw outlier.
    out["qualifying"].sort(key=lambda v: ("small_channel_proof" not in v["tags"], -(v.get("outlier") or 0)))
    out["non_speculative_outliers"].sort(key=lambda v: -(v.get("outlier") or 0))
    out["flops"].sort(key=lambda v: v.get("views") or 0)
    json.dump(out, sys.stdout, indent=2)
    print(f"\nparsed {len(videos)} | qualifying {len(out['qualifying'])} | "
          f"non-speculative outliers {len(out['non_speculative_outliers'])} | flops {len(out['flops'])}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
```

## apply_decisions.py

```python
#!/usr/bin/env python3
"""Apply title-test decisions to the Universal Horizontally Scalable Titles bank.

Usage: python3 apply_decisions.py BANK.json DECISIONS.json
Writes BANK.json in place and prints a run report.

DECISIONS.json:
{
  "source_channel": "https://www.youtube.com/@...",
  "source_franchise": "Harry Potter",
  "matches":    [{"template_id": "...", "title": "...", "views": 0, "outlier": 0, "vph": 0, "tags": []}],
  "new":        [{"id": "...", "template": "... {SLOT} ...", "requires": ["SLOT"],
                  "new_slots": {"SLOT": "description"},
                  "proof": [{"title": "...", "views": 0, "outlier": 0, "tags": []}],
                  "test": {"game_of_thrones": {"title": "...", "rating": "S"}, "twilight": {...},
                           "dc": {...}, "marvel": {...}},
                  "condition": "what a franchise needs for this to work (conditional tier)",
                  "notes": "..."}],
  "anti_proof": [{"template_id": "...", "title": "...", "views": 0, "lesson": "..."}],
  "rejected":   [{"title": "...", "reason": "not templatable / franchise-specific"}]
}
"""
import datetime, json, sys

POINTS = {"S": 2, "O": 1, "W": 0}
TEST_SET = ["game_of_thrones", "twilight", "dc", "marvel"]


def tier_for(score):
    return "universal" if score >= 7 else "conditional" if score >= 5 else "franchise_specific"


def main(bank_path, dec_path):
    bank = json.load(open(bank_path))
    dec = json.load(open(dec_path))
    src_fr, src_ch = dec["source_franchise"], dec.get("source_channel")
    default_fr = bank["meta"].setdefault("source_franchise", "Harry Potter")
    bank.setdefault("rejected", [])
    for e in bank.pop("excluded_not_universal", []):  # legacy key from v1.x
        bank["rejected"].append({"template": None, "example_title": e["title"], "reason": e["reason"]})

    by_id = {t["id"]: t for t in bank["templates"]}
    for t in bank["templates"]:
        if "stress_test" in t:
            t["tier"] = tier_for(int(t["stress_test"]["score"].split("/")[0]))

    rep = {k: [] for k in ("proof_added", "duplicates_skipped", "upgraded_to_cross_validated",
                           "new_universal", "new_conditional", "new_franchise_specific", "anti_proof_added",
                           "not_templatable", "errors")}

    def known(t):
        return {p["title"].lower() for p in t.get("proof", []) + t.get("anti_proof", [])}

    def franchises(t):
        return {p.get("franchise", default_fr) for p in t.get("proof", [])}

    for m in dec.get("matches", []):
        t = by_id.get(m["template_id"])
        if not t:
            rep["errors"].append(f"unknown template_id {m['template_id']}")
            continue
        if m["title"].lower() in known(t):
            for p in t.get("proof", []):  # refresh tags on the existing proof entry
                if p["title"].lower() == m["title"].lower() and m.get("tags"):
                    added = sorted(set(m["tags"]) - set(p.get("tags", [])))
                    if added:
                        p["tags"] = sorted(set(p.get("tags", [])) | set(m["tags"]))
                        rep.setdefault("tags_refreshed", []).append(f"{m['title']} +{added}")
            rep["duplicates_skipped"].append(m["title"])
            continue
        is_new_franchise = src_fr not in franchises(t)
        entry = {k: m[k] for k in ("title", "views", "outlier", "vph", "tags") if k in m}
        entry.update(franchise=src_fr, channel=src_ch)
        t.setdefault("proof", []).append(entry)
        rep["proof_added"].append(f"{t['id']}: {m['title']}")
        if is_new_franchise and t.get("confidence") != "cross_validated":
            t["confidence"] = "cross_validated"
            rep["upgraded_to_cross_validated"].append(t["id"])

    rejected_templates = {r.get("template") for r in bank["rejected"]}
    for n in dec.get("new", []):
        if n["id"] in by_id:
            rep["errors"].append(f"{n['id']} already exists; send it as a match instead")
            continue
        if n["template"] in rejected_templates:
            rep["duplicates_skipped"].append(f"{n['template']} (previously rejected)")
            continue
        missing = [f for f in TEST_SET if f not in n.get("test", {})]
        if missing:
            rep["errors"].append(f"{n['id']} missing test franchises {missing}")
            continue
        ratings = {f: n["test"][f]["rating"] for f in TEST_SET}
        score = sum(POINTS[r] for r in ratings.values())
        stress = {"score": f"{score}/8", "ratings": ratings,
                  "titles": {f: n["test"][f]["title"] for f in TEST_SET}}
        tier = tier_for(score)
        proof = [dict(p, franchise=src_fr, channel=src_ch) for p in n.get("proof", [])]
        for slot, desc in n.get("new_slots", {}).items():
            bank["slots"].setdefault(slot, desc)
        rec = {"id": n["id"], "template": n["template"], "requires": n.get("requires", []),
               "tier": tier, "confidence": "proven", "priority": {"universal": 3, "conditional": 5}.get(tier, 7),
               "proof": proof, "example": stress["titles"]["game_of_thrones"], "stress_test": stress}
        if n.get("condition"):
            rec["condition"] = n["condition"]
        if n.get("notes"):
            rec["notes"] = n["notes"]
        bank["templates"].append(rec)
        by_id[n["id"]] = rec
        rep[f"new_{tier}"].append(f"{n['template']} ({score}/8)")

    for a in dec.get("anti_proof", []):
        t = by_id.get(a["template_id"])
        if not t:
            rep["errors"].append(f"unknown template_id {a['template_id']} in anti_proof")
            continue
        if a["title"].lower() in known(t):
            rep["duplicates_skipped"].append(a["title"])
            continue
        t.setdefault("anti_proof", []).append(dict(a, franchise=src_fr))
        rep["anti_proof_added"].append(f"{t['id']}: {a['title']}")

    for r in dec.get("rejected", []):
        rep["not_templatable"].append(r["title"])

    order = {"universal": 0, "conditional": 1, "franchise_specific": 2}
    bank["templates"].sort(key=lambda t: (order.get(t.get("tier"), 2),
                                          -int(t.get("stress_test", {}).get("score", "0/8").split("/")[0]),
                                          t.get("priority", 9)))
    major, minor = (bank["meta"].get("version", "1.0").split(".") + ["0"])[:2]
    bank["meta"]["version"] = f"{major}.{int(minor) + 1}"
    bank["meta"].setdefault("runs", []).append({"date": datetime.date.today().isoformat(),
                                                "channel": src_ch, "franchise": src_fr})
    json.dump(bank, open(bank_path, "w"), indent=2)

    counts = {k: len(v) for k, v in rep.items() if v}
    tiers = {}
    for t in bank["templates"]:
        tiers[t.get("tier", "untiered")] = tiers.get(t.get("tier", "untiered"), 0) + 1
    print(json.dumps({"bank_version": bank["meta"]["version"], "bank_tiers": tiers,
                      "counts": counts, "details": {k: v for k, v in rep.items() if v}}, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:3])
```