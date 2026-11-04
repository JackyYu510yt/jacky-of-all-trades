"""insights_scan: the newer "Channel insights" analytics page model (URL .../analytics/hub_overview). Read-only.
Studio rolls this out per account; the old /analytics/tab-overview URL redirects there. analytics_scan.scan_analytics
hands over to scan_insights() when the window lands on hub_overview.

Layout (proven on France Dhi, 2026-11-02): range chips "48 hours / 7 days / 28 days / More", then a stack of metric
cards (Views, Watch time (hours), Subscribers: a big number + a green/red trend arrow + a chart), then Content
(Recent video performance, Top content), How viewers find your content, Audience. No Realtime card: the "48 hours"
chip is the realtime equivalent. Output keys mirror analytics_scan (views, watch_hours, realtime_views_48h ...).

OCR notes: the trend arrow merges into the number ("4" + arrow reads "40") -> found by pixel and stripped; a lone bold
"0" is invisible (Subscribers 0) -> None, never 0.
"""
import re, time, json, argparse
import channel_stats as c
import analytics_scan as an

URL = "https://studio.youtube.com/channel/{cid}/analytics/hub_overview"
NUMTOK = re.compile(r"^[+\-]?[\d][\d.,]*[KMB]?$", re.I)
CHART_RANGE = re.compile(r"([A-Z][a-z]{2} \d{1,2}, \d{4})")


def _arrow_x(shot, x0, x1, y0, y1):
    """Left edge of the trend-arrow circle (green or red) inside the box, or None."""
    from PIL import Image
    im = Image.open(shot).convert("RGB")
    for x in range(x0, min(x1, im.width)):
        for y in range(y0, min(y1, im.height)):
            r, g, b = im.getpixel((x, y))
            if (g > 100 and r < 70 and b < 70) or (r > 170 and g < 90 and b < 90):
                return x
    return None


INFERRED = []      # numbers recorded as 0 because OCR can't see a lone bold 0 but a single dark glyph is there


def _lone_glyph(pg, lab):
    """True when exactly one digit-sized dark glyph sits where the big number is (OCR saw no text there).
    Wider than ~26px or several blobs = something else -> not inferred."""
    from PIL import Image
    im = Image.open(pg.shot).convert("L")
    y0, y1 = int(lab["cy"]) + 18, int(lab["cy"]) + 80
    cols = [x for x in range(128, 260) if any(im.getpixel((x, y)) < 80 for y in range(y0, min(y1, im.height)))]
    if not cols:
        return False
    runs, start = [], cols[0]
    for a, b in zip(cols, cols[1:] + [None]):
        if b is None or b - a > 3:
            runs.append((start, a)); start = b
    return len(runs) == 1 and 8 <= runs[0][1] - runs[0][0] + 1 <= 24


def card_value(pg, label_re, x1=330):
    """Big number under a metric-card label, with the trend arrow's merged glyph removed. None if unreadable."""
    lab = c.find_word(pg, label_re, x0=120, x1=x1)
    if not lab:
        return None
    cand = [w for w in pg.words if 18 < w["cy"] - lab["cy"] < 80 and w["x"] < 300 and NUMTOK.match(w["t"])]
    if not cand:
        if _lone_glyph(pg, lab):
            INFERRED.append(f"{lab['t']}=0")
            return 0
        return None
    w = min(cand, key=lambda w: w["x"])
    t = w["t"]
    ax = _arrow_x(pg.shot, int(w["x"]), int(w["x"] + w["w"] + 60), int(w["y"]), int(w["y"] + w["h"]))
    if ax is not None and w["x"] + w["w"] > ax + 3 and len(t) > 1:
        t = t[:-1]                      # OCR fused the arrow circle onto the number as one more digit
    return c.num_val(t)


def chart_range(pg):
    """Chart axis start/end dates under the Views chart: the actual window the numbers cover."""
    ds = [w for w in pg.rows(x0=120, x1=1000, y0=780, y1=830)]
    txt = " ".join(r["text"] for r in ds)
    found = CHART_RANGE.findall(txt)
    return f"{found[0]} - {found[-1]}" if len(found) >= 2 else None


def chip(pg, label):
    """Click target for a range chip ('48 hours' / '28 days')."""
    n = label.split()[0]
    return c.find_word(pg, rf"^{n}$", x0=230, x1=520, y0=415, y1=465)


def click_chip(h, pg, label, tag):
    w = chip(pg, label)
    if not w:
        raise c.StepFail(f"range chip '{label}' not found")
    c.focus(h)
    c.click_word(h, pg, w, dx=18)
    time.sleep(2.5)
    return c.read(h, tag)


def selected_chip(pg):
    """Which chip is the dark (selected) one: sample pixels left of each chip's number."""
    from PIL import Image
    im = Image.open(pg.shot).convert("L")
    best = None
    for label in ("48 hours", "7 days", "28 days"):
        w = chip(pg, label)
        if not w:
            continue
        dark = sum(1 for x in range(int(w["x"]) - 10, int(w["x"]) - 4) for y in range(int(w["y"]) - 2, int(w["y"]) + 4)
                   if im.getpixel((x, y)) < 60)
        if dark >= 20:
            best = label
    return best


def top_content(pg):
    """Rows of the 'Top content' card: title (best effort) + views."""
    hd = c.find_word(pg, r"^Top$", x0=570, x1=700)
    if not hd:
        return None
    out = []
    for r in pg.rows(x0=650, x1=1000, y0=hd["cy"] + 40, y1=hd["cy"] + 260):
        nums = [w for w in r["words"] if w["cx"] > 940 and NUMTOK.match(w["t"])]
        title = " ".join(w["t"] for w in r["words"] if w["cx"] < 940)
        if nums and title:
            out.append({"title_start": title, "views": c.num_val(nums[-1]["t"])})
    return out


def recent_video(pg):
    hd = c.find_word(pg, r"^Recent$", x0=120, x1=300)
    if not hd:
        return None
    age = next((r["text"] for r in pg.rows(x0=120, x1=545, y0=hd["cy"] + 10, y1=hd["cy"] + 40) if re.search(r"day|hour|minute", r["text"])), None)

    def val(label):
        lw = c.find_row(pg, label, x0=120, x1=545, y0=hd["cy"] + 40, y1=hd["cy"] + 260)
        if not lw:
            return None
        v = [w for w in lw["words"] if w["cx"] > 440]
        return v[-1]["t"] if v else None
    return {"age": age, "views": c.num_val(val(r"^Views$") or "") if val(r"^Views$") else None,
            "ctr": val(r"click-through"), "avg_view_duration": val(r"Average view")}


def parse_state(pg):
    """Everything readable on one screen of the page; the scan merges several screens."""
    return {"views": card_value(pg, r"^Views$"), "watch_hours": card_value(pg, r"^Watch$"),
            "subscribers": card_value(pg, r"^Subscribers$"), "chart_range": chart_range(pg)}


def scan_insights(h, cid, tag="in", label=None):
    c.sc("go", h, URL.format(cid=cid)); time.sleep(8)
    pg = c.ensure_studio(h, tag + "e")
    if c.channel_id_from_url(c.win_info(h).get("url")) != cid:
        raise c.StepFail("insights URL id != expected")
    c.section_check(h, "insights", tag)
    c.sc("wscroll", h, 1042, 600, -30, pg.shot); time.sleep(1)
    pg = c.read(h, tag + "_top")
    if selected_chip(pg) != "28 days":
        pg = click_chip(h, pg, "28 days", tag + "_c28")
    pg = c.read(h, tag + "_t28")
    if selected_chip(pg) != "28 days":
        raise c.StepFail(f"28 days chip not selected (selected: {selected_chip(pg)})")
    top = parse_state(pg)
    if top["views"] is None:
        raise c.StepFail("Views card number not read")
    shot_top = an.save_evidence(pg.shot, cid, label, "insights-28d")
    # lower screens: subscribers card, top content, recent video performance
    c.sc("wscroll", h, 1042, 600, 8, pg.shot); time.sleep(1.5)
    pg2 = c.read(h, tag + "_low")
    subs = card_value(pg2, r"^Subscribers$")
    tc, rv = top_content(pg2), recent_video(pg2)
    shot_low = an.save_evidence(pg2.shot, cid, label, "insights-lower")
    # 48 hours = the realtime equivalent
    c.sc("wscroll", h, 1042, 600, -30, pg2.shot); time.sleep(1)
    pg3 = click_chip(h, c.read(h, tag + "_p3"), "48 hours", tag + "_c48")
    if selected_chip(pg3) != "48 hours":
        raise c.StepFail(f"48 hours chip not selected (selected: {selected_chip(pg3)})")
    v48 = card_value(pg3, r"^Views$")
    shot_48 = an.save_evidence(pg3.shot, cid, label, "insights-48h")
    click_chip(h, pg3, "28 days", tag + "_back")        # leave the page as we found it
    return {"variant": "insights", "period": "Last 28 days", "range": top["chart_range"], "views": top["views"],
            "watch_hours": top["watch_hours"], "subscribers": subs, "top_content": tc, "recent_video": rv,
            "realtime_views_48h": v48, "screenshot": shot_top, "screenshot_lower": shot_low, "screenshot_48h": shot_48,
            "inferred_zero": list(INFERRED),
            "subscribers_note": None if subs is not None else "unreadable",
            "read_at": time.strftime("%Y-%m-%d %H:%M:%S"), "status": "ok"}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hwnd", type=int, required=True)
    ap.add_argument("--label")
    a = ap.parse_args()
    cid = c.channel_id_from_url(c.win_info(a.hwnd).get("url"))
    print(json.dumps(scan_insights(a.hwnd, cid, label=a.label), indent=1))
