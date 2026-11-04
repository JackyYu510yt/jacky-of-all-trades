"""dashboard_scan: read the Studio Channel dashboard of the channel the window is ON, and save screenshots. Read-only.
Same contract as content_scan / analytics_scan: the caller has already verified WHICH channel this is.

Cards read (3-column layout at 1053px; column split by x):
  left   Latest video performance: title (OCR of the thumbnail overlay - best effort), views/comments/likes,
         age ("First 1 day 19 hours"), Ranking by views "2 of 10", Views, Thumbnail CTR, Average view duration
  middle Channel analytics: current subscribers, "+N in last 28 days", Summary (Last 28 days) views + watch hours,
         Top content (Last 48 hours) rows
  below  Recent subscribers (last 90 days): name + subscriber count (visible rows)
A number OCR cannot see is None, never 0. Screenshots: top of page + scrolled lower part, cropped to page content.
"""
import re, time, json, argparse
import channel_stats as c
import analytics_scan as an

L, M = (105, 405), (415, 705)


def _col(pg, x0, x1, y0, y1):
    return pg.rows(x0=x0, x1=x1, y0=y0, y1=y1)


def parse_dashboard(pg):
    out = {"latest_video": {}, "channel_analytics": {}}
    lv = out["latest_video"]
    # --- left card
    stats = [r for r in _col(pg, *L, 450, 480)]
    if stats:
        nums = [w["t"] for w in stats[0]["words"] if re.match(r"^\d[\d.,]*[KMB]?$", w["t"], re.I)]
        if len(nums) >= 3:
            lv["views"], lv["comments"], lv["likes"] = (c.num_val(n) for n in nums[:3])
        else:
            lv["_stat_tokens"] = nums
    title = " ".join(r["text"] for r in _col(pg, 130, 380, 380, 435))
    lv["title_ocr"] = title or None            # text over the thumbnail: OCR is rough here; match to Content list by prefix
    for r in _col(pg, *L, 500, 700):
        t = r["text"]
        m = re.search(r"First\s+(.+)$", t)
        if m and "age" not in lv:
            lv["age"] = m.group(1).strip()
        m = re.search(r"(\d+?)\s*(?:of|0f)\s*(\d+)", t)      # OCR reads "2 of 10" as "20f10"
        if m and re.search(r"Ranking", t):
            lv["rank"], lv["rank_of"] = int(m.group(1)), int(m.group(2))
        elif re.match(r"^Views\b", t) and r["words"][0]["cx"] < 200:
            m = re.search(r"([\d.,]+[KMB]?)\s*$", t); lv["views_detail"] = c.num_val(m.group(1)) if m else None
            if lv["views_detail"] is None and _glyph_at(pg, 335, 375, r["y"]):
                lv["views_detail"], lv["views_detail_source"] = 0, "inferred (lone 0 invisible to OCR)"
        elif re.search(r"click-through", t, re.I):
            m = re.search(r"(\d+(?:\.\d+)?)\s*%", t); lv["ctr_pct"] = float(m.group(1)) if m else None
        elif re.search(r"Average view duration", t, re.I):
            m = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)\s*$", t); lv["avg_view_duration"] = m.group(1) if m else None
    # --- middle card
    ca = out["channel_analytics"]
    m = re.search(r"\+?(-?\d[\d.,]*)\s+in last (\d+) days", " ".join(r["text"] for r in _col(pg, *M, 360, 400)))
    ca["subs_change"] = int(m.group(1).replace(",", "")) if m else None
    ca["subs_change_days"] = int(m.group(2)) if m else None
    # everything below is anchored on the card's own labels, not on fixed y (the card varies per account)
    lab = c.find_word(pg, r"^Current$", x0=M[0], x1=M[1], y0=300, y1=420)       # "Current subscribers" (+ big number)
    cur = [w for w in pg.words if M[0] <= w["cx"] <= M[1] and re.match(r"^\d[\d.,]*[KMB]?$", w["t"], re.I)
           and ((lab and 15 < w["cy"] - lab["cy"] < 70) or (not lab and 325 <= w["cy"] <= 370))]
    ca["subscribers"] = c.num_val(cur[0]["t"]) if cur else None
    if ca["subscribers"] is None and lab and _lone_zero(pg, lab):
        ca["subscribers"], ca["subscribers_source"] = 0, "inferred (a lone bold 0 is invisible to OCR)"
    for r in _col(pg, *M, 380, 700):
        m = re.match(r"^(Views|Watch time.*?)\s+([\d.,]+[KMB]?)", r["text"])
        if m:
            ca["views_28d" if m.group(1) == "Views" else "watch_hours_28d"] = (c.num_val(m.group(2)) if m.group(1) == "Views" else float(m.group(2).replace(",", "")))
    top = []
    hd = c.find_word(pg, r"^Top$", x0=M[0], x1=M[1], y0=380)
    for r in (_col(pg, *M, hd["cy"] + 30, hd["cy"] + 140) if hd else _col(pg, *M, 615, 700)):
        ws = r["words"]
        if len(ws) >= 2 and re.match(r"^\d[\d.,]*[KMB]?$", ws[-1]["t"], re.I):
            top.append({"title_start": " ".join(w["t"] for w in ws[:-1]), "views": c.num_val(ws[-1]["t"])})
    ca["top_content_48h"] = top
    return out


def _glyph_at(pg, x0, x1, y):
    """Exactly one digit-sized dark glyph in the box x0..x1 on the text line at y."""
    from PIL import Image
    im = Image.open(pg.shot).convert("L")
    cols = [x for x in range(x0, x1) if any(im.getpixel((x, yy)) < 80 for yy in range(int(y) - 8, int(y) + 8))]
    if not cols:
        return False
    runs, start = [], cols[0]
    for a, b in zip(cols, cols[1:] + [None]):
        if b is None or b - a > 3:
            runs.append((start, a)); start = b
    return len(runs) == 1 and 6 <= runs[0][1] - runs[0][0] + 1 <= 16


def _lone_zero(pg, lab):
    """One digit-sized dark glyph where the big number should be, and OCR read no text there."""
    from PIL import Image
    im = Image.open(pg.shot).convert("L")
    y0, y1 = int(lab["cy"]) + 15, int(lab["cy"]) + 75
    cols = [x for x in range(M[0] + 20, M[0] + 140) if any(im.getpixel((x, y)) < 80 for y in range(y0, min(y1, im.height)))]
    if not cols:
        return False
    runs, start = [], cols[0]
    for a, b in zip(cols, cols[1:] + [None]):
        if b is None or b - a > 3:
            runs.append((start, a)); start = b
    return len(runs) == 1 and 8 <= runs[0][1] - runs[0][0] + 1 <= 24


def parse_recent_subs(pg):
    """'Recent subscribers' card (middle column, below the analytics card): name line then 'N subscribers'."""
    hdr = c.find_word(pg, r"^Recent$", x0=M[0], x1=M[1])
    if not hdr:
        return None
    rows = _col(pg, 490, 700, hdr["cy"] + 50, 1040)
    subs, prev = [], None
    for r in rows:
        m = re.match(r"^([\d.,]+[KMB]?)\s+subscribers?$", r["text"], re.I)
        if m and prev:
            subs.append({"name": prev, "subscribers": c.num_val(m.group(1))}); prev = None
        else:
            prev = r["text"]
    return subs


def scan_dashboard(h, cid, tag="db", retries=2, label=None):
    last = None
    for attempt in range(1, retries + 2):
        try:
            c.ensure_dashboard(h, cid, tag)
            c.sc("wscroll", h, 1042, 600, -30, c.os.path.join(c.SHOTS, f"{tag}_chk.png")); time.sleep(1.5)   # to top, mouse off the cards
            pg = c.read(h, tag + "_top")
            d = parse_dashboard(pg)
            if d["channel_analytics"].get("subscribers") is None and d["channel_analytics"].get("views_28d") is None:
                raise c.StepFail("dashboard cards not recognised (Channel analytics card unreadable)")
            d["variant"] = "insights" if re.search(r"channel\s+insights|realtime data|live count", pg.text(), re.I) else "classic"
            d["screenshot_top"] = an.save_evidence(pg.shot, cid, label, kind="dashboard-top")
            c.sc("wscroll", h, 1042, 600, 6, pg.shot); time.sleep(1.5)
            pg2 = c.read(h, tag + "_low")
            d["recent_subscribers"] = parse_recent_subs(pg2)
            d["screenshot_lower"] = an.save_evidence(pg2.shot, cid, label, kind="dashboard-lower")
            c.sc("wscroll", h, 1042, 600, -30, pg2.shot); time.sleep(0.8)
            d["read_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            d["status"] = "ok"
            return d
        except c.Refuse:
            raise
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            c.log(f"dashboard attempt {attempt} failed: {last}")
            try:
                c.ensure_studio(h, tag + "r")
            except c.Refuse:
                raise
            except Exception:
                pass
    return {"status": "failed", "error": last}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hwnd", type=int, required=True)
    ap.add_argument("--label")
    a = ap.parse_args()
    cid = c.channel_id_from_url(c.win_info(a.hwnd).get("url"))
    print(json.dumps(scan_dashboard(a.hwnd, cid, label=a.label), indent=1, ensure_ascii=True))
