"""analytics_scan: read the Studio Analytics > Overview tab of the channel the window is ON. Read-only.
Caller must already have verified WHICH channel this is (same contract as content_scan).

Reads: period label + date range, headline views, the three metric cards (views / watch time hours / subscribers
change), the Realtime panel (subscribers, views last 48h) and the top-content rows. Two independent reads of the
same number (headline sentence vs Views card) must agree, else the scan fails and retries. A number OCR cannot see
(a lone bold 0) is None, never 0.

  python analytics_scan.py --hwnd H
"""
import os, re, time, json, argparse
import channel_stats as c

URL = "https://studio.youtube.com/channel/{cid}/analytics/tab-overview/period-default"
RANGE = re.compile(r"([A-Z][a-z]{2} \d{1,2}(?:, \d{4})?)\s*[-\u2013]\s*([A-Z][a-z]{2} \d{1,2}, \d{4})")


def _num(t):
    return c.num_val(t.replace("+", "")) if t else None


def parse_overview(pg):
    txt = pg.text()
    out = {}
    # period (top right): "Oct 5 - Nov 1, 2026" over "Last 28 days"
    top = " ".join(r["text"] for r in pg.rows(x0=700, y0=330, y1=470))      # lower when Ask Studio chips are shown
    m = RANGE.search(top)
    out["range"] = f"{m.group(1)} - {m.group(2)}" if m else None
    m = re.search(r"Last\s+(\d+)\s+days", top)
    out["period"] = f"Last {m.group(1)} days" if m else None
    # headline sentence
    m = re.search(r"got\s+([\d.,]+[KMB]?)\s+views?\s+in\s+the\s+last\s+(\d+)\s+days", txt, re.I)
    out["headline_views"] = c.num_val(m.group(1)) if m else None
    # metric cards: label row then value row
    lab = c.find_row(pg, r"Views.*Watch time.*Subscribers", x0=100, x1=745, y0=480, y1=680)
    out["views"] = out["watch_hours"] = out["subs_change"] = None
    if lab:
        vals = pg.rows(x0=100, x1=745, y0=lab["y"] + 8, y1=lab["y"] + 45)
        toks = [w["t"] for w in vals[0]["words"]] if vals else []
        toks = [t for t in toks if re.match(r"^[+\-]?[\d.,]+[KMB]?$", t)]
        if len(toks) >= 3:
            out["views"], out["watch_hours"], out["subs_change"] = _num(toks[0]), float(toks[1].replace(",", "")), _num(toks[2]) * (-1 if toks[2].startswith("-") else 1)
        elif len(toks) == 2:
            # the Subscribers column shows a dash / lone 0 (no number OCR can see): views + watch time are read,
            # subs_change stays None (never guessed)
            out["views"], out["watch_hours"] = _num(toks[0]), float(toks[1].replace(",", ""))
            out["subs_change_note"] = "Subscribers card has no readable number (dash or lone 0)"
        elif toks:
            out["_card_tokens"] = toks
    # Realtime panel (right column)
    rt = c.find_word(pg, r"^Realtime$", x0=780, y0=420, y1=560)        # anchor on the heading, not on fixed y
    ry = rt["cy"] if rt else 440
    rs = c.find_word(pg, r"^Subscribers$", x0=780, y0=ry + 40, y1=ry + 170)
    out["realtime_subscribers"] = None
    if rs:
        n = [w for w in pg.words if abs(w["cy"] - (rs["cy"] - 23)) < 14 and 780 <= w["cx"] <= 900 and c.NUM.match(w["t"])]
        out["realtime_subscribers"] = c.num_val(n[0]["t"]) if n else None
    r48 = c.find_word(pg, r"^48$", x0=780, y0=ry + 120, y1=ry + 300)
    out["realtime_views_48h"] = None
    if r48:
        n = [w for w in pg.words if abs(w["cy"] - (r48["cy"] - 23)) < 14 and 780 <= w["cx"] <= 900 and c.NUM.match(w["t"])]
        out["realtime_views_48h"] = c.num_val(n[0]["t"]) if n else None
    return out


EVIDENCE = os.path.join(c.HERE, "evidence")


def right_card(pg):
    """Heading of the right-hand carousel card ('Realtime', 'Latest content', ...)."""
    return " ".join(r["text"] for r in pg.rows(x0=780, x1=1030, y0=420, y1=520)).strip()   # y varies with the chips row


def goto_realtime(h, pg, tag, max_steps=12):
    """The right panel is a carousel ('1 of 10'); which card shows first varies per load. Step with the > arrow."""
    for step in range(max_steps):
        if re.search(r"Realtime", right_card(pg), re.I):
            return pg
        of = next((w for w in pg.words if w["t"].lower() == "of" and w["cx"] > 780 and w["cy"] > 700), None)
        if not of:
            raise c.StepFail(f"carousel pager not found (right card reads '{right_card(pg)}')")
        c.focus(h)
        c.sc("wclick", h, int(of["cx"] + 103), int(of["cy"]), pg.shot)      # the > arrow sits ~103px right of "of"
        time.sleep(1.5)
        pg = c.read(h, f"{tag}_car{step}")
    raise c.StepFail("Realtime card not reached in the carousel")


def _ink_glyphs(shot, x0, x1, y0, y1):
    """Number of separate dark blobs (left to right, gaps > 3px) in the box; used to see a lone digit OCR dropped."""
    from PIL import Image
    im = Image.open(shot).convert("L")
    cols = [x for x in range(x0, x1) if any(im.getpixel((x, y)) < 90 for y in range(max(y0, 0), min(y1, im.height)))]
    if not cols:
        return 0, 0
    blobs, start = [], cols[0]
    for a, b in zip(cols, cols[1:] + [None]):
        if b is None or b - a > 3:
            blobs.append((start, a)); start = b
    return len(blobs), blobs[0][1] - blobs[0][0] + 1


def realtime_fill(h, pg, d):
    """The Realtime column's two big numbers (subscribers, views last 48h) are often lone bold digits that full-page
    OCR drops. Zoomed crop OCR reads a lone 1-9; a lone 0 is invisible to it, so: crop read first, then one digit-sized
    glyph with nothing read = 0 (recorded in d['inferred_zero'])."""
    d.setdefault("inferred_zero", [])
    rt = c.find_word(pg, r"^Realtime$", x0=780, y0=420, y1=560)
    ry = rt["cy"] if rt else 440
    targets = (("realtime_subscribers", c.find_word(pg, r"^Subscribers$", x0=780, y0=ry + 40, y1=ry + 170)),
               ("realtime_views_48h", c.find_word(pg, r"^48$", x0=780, y0=ry + 120, y1=ry + 300)))
    for key, lw in targets:
        if d.get(key) is not None or not lw:
            continue
        toks = []
        for dy, wd in ((-34, 120), (-37, 120), (-31, 120), (-34, 150), (-40, 130)):      # a 2px shift flips whether OCR sees a lone digit
            out = c.sc("ocr", h, os.path.join(c.SHOTS, f"rt_{key}.png"), f"786,{int(lw['y']) + dy},{wd},50")
            words = [w for ln in (c.ocr_json(out) or {}).get("lines", []) for w in ln.get("words", [])]
            label_ys = [w["y"] for w in words if re.match(r"^(Views|Last|hours?|hc|Subscribers|•)$", w["t"], re.I) or w["t"] == "48"]
            ly = min(label_ys) if label_ys else 34 - dy - 34 + 34
            # only a number ABOVE the label line counts: the crop also holds "Last 48 hours", whose "48" is not a value
            toks = [w["t"] for w in words if c.NUM.match(w["t"]) and w["y"] < ly - 8]
            if toks:
                break
        if toks:
            d[key] = c.num_val(toks[0]); continue
        n, wd = _ink_glyphs(pg.shot, 792, 900, int(lw["y"]) - 32, int(lw["y"]) - 6)
        if n == 1 and 7 <= wd <= 22:
            d[key] = 0; d["inferred_zero"].append(key)
    return d


def save_evidence(shot, cid, label, kind="analytics"):
    """Copy the exact capture that was parsed (page content only, browser frame cropped off) to a stable place."""
    from PIL import Image
    d = os.path.join(EVIDENCE, label or cid)
    os.makedirs(d, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    im = Image.open(shot)
    w, hh = im.size
    im = im.crop((8, 88, w - 8, hh - 8))
    path = os.path.join(d, f"{kind}-{stamp}.png")
    im.save(path)
    im.save(os.path.join(d, f"{kind}-latest.png"))
    return path


def scan_analytics(h, cid, tag="an", retries=2, label=None):
    last = None
    for attempt in range(1, retries + 2):
        try:
            c.sc("go", h, URL.format(cid=cid)); time.sleep(9)
            pg = c.ensure_studio(h, tag + "e")
            got = c.channel_id_from_url(c.win_info(h).get("url"))
            if got != cid:
                raise c.StepFail(f"analytics URL id {got} != expected {cid}")
            if "hub_overview" in (c.win_info(h).get("url") or ""):
                import insights_scan          # newer page model: the old URL redirected to "Channel insights"
                c.log("analytics: Insights page model (hub_overview)")
                return insights_scan.scan_insights(h, cid, tag + "i", label)
            c.section_check(h, "analytics", tag)
            pg = c.read(h, tag + "_ov")
            pg = goto_realtime(h, pg, tag)
            c.sc("wscroll", h, 1042, 600, -1, pg.shot); time.sleep(0.8)   # park mouse: no hover tooltips in the evidence shot
            pg = c.read(h, tag + "_fin")
            d = realtime_fill(h, pg, parse_overview(pg))
            if d["realtime_subscribers"] is None and d["realtime_views_48h"] is None:
                raise c.StepFail("Realtime card on screen but no numbers read")
            bad = []
            if d["period"] != "Last 28 days":
                bad.append(f"period={d['period']}")
            if d["views"] is None or d["headline_views"] is None:
                bad.append("views/headline unreadable")
            elif d["views"] != d["headline_views"]:
                bad.append(f"views card {d['views']} != headline {d['headline_views']}")
            if bad:
                raise c.StepFail("; ".join(bad) + f" {d}")
            d["screenshot"] = save_evidence(pg.shot, cid, label)
            d["read_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            d["status"] = "ok"
            return d
        except c.Refuse:
            raise
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            c.log(f"analytics attempt {attempt} failed: {last}")
            try:
                c.ensure_studio(h, tag + "r")
            except c.Refuse:
                raise
            except Exception:
                pass
    # Studio rolls out new page models per account (renamed tabs like "Insights", different cards). If the known
    # markers are absent, say so and keep a screenshot, instead of guessing numbers off a layout we don't know.
    res = {"status": "failed", "error": last}
    try:
        pg = c.read(h, tag + "_unk")
        markers = {"Overview": bool(c.find_word(pg, r"^Overview$")), "Views": bool(c.find_word(pg, r"^Views$")),
                   "Watch time": bool(re.search(r"Watch time", pg.text())), "Subscribers": bool(c.find_word(pg, r"^Subscribers$"))}
        if not all(markers.values()):
            res["layout_unrecognized"] = True
            res["markers_seen"] = markers
            res["screenshot"] = save_evidence(pg.shot, cid, "_unrecognized_" + (label or cid))
            c.log(f"analytics: LAYOUT NOT RECOGNIZED {markers} -> screenshot kept at {res['screenshot']}")
    except c.Refuse:
        raise
    except Exception:
        pass
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hwnd", type=int, required=True)
    ap.add_argument("--label", help="evidence folder name (default: channel id)")
    a = ap.parse_args()
    cid = c.channel_id_from_url(c.win_info(a.hwnd).get("url"))
    print(json.dumps(scan_analytics(a.hwnd, cid, label=a.label), indent=1))
