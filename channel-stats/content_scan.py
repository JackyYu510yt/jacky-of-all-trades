"""content_scan: read the Studio Content tab (Videos / Shorts / Live) of the channel the window is ON.
Read-only. The caller (channel_stats.process_channel, or `python content_scan.py --hwnd H`) must already have
verified WHICH channel this is; this module only checks the page it lands on is that channel's Content page.

Per video: title_start (the list truncates titles), visibility (Public/Unlisted/Private/Scheduled/Draft...),
status (Published/Scheduled/Draft...), date_text, scheduled_date/scheduled_time (only when Scheduled; the time
is None unless the list shows one), views, notices. Completeness check: the pager's "1-N of N" total must equal
the number of rows collected, per tab; otherwise `complete` is False and nothing is silently dropped.
"""
import re, time, json, sys, argparse
import channel_stats as c

TABS = {"videos": "videos/upload", "shorts": "videos/short", "live": "videos/live"}
VIS = re.compile(r"^(Public|Unlisted|Private|Scheduled|Draft|Restricted|Members)\b", re.I)
VIS_FIX = {"pubiic": "Public", "publlc": "Public", "unllsted": "Unlisted", "privale": "Private"}
DATE = re.compile(r"\b([A-Z][a-z]{2}) (\d{1,2}), (\d{4})\b")
DATE_DM = re.compile(r"\b(\d{1,2}) ([A-Z][a-z]{2}) (\d{4})\b")      # newer/regional layout: "4 Nov 2026"


def find_date(text):
    """First date in text, normalised to 'Nov 4, 2026' whichever layout the account uses; None if absent."""
    m = DATE.search(text)
    if m:
        return f"{m.group(1)} {int(m.group(2))}, {m.group(3)}"
    m = DATE_DM.search(text)
    return f"{m.group(2)} {int(m.group(1))}, {m.group(3)}" if m else None


TIME = re.compile(r"\b(\d{1,2}:\d{2})\s*([AP]M)\b", re.I)
PAGER = re.compile(r"(\d+)\s*[-–]\s*(\d+?)\s*(?:of|0f)\s*(\d+)")   # OCR reads "14 of 14" as "140f14"
STATUS = re.compile(r"^(Published|Scheduled|Draft|Processing|Uploading|Premiere|Premieres|Uploaded)\b", re.I)
X_TITLE, X_NOTICE, X_VIS, X_DATE, X_VIEWS = (285, 545), (545, 685), (685, 805), (805, 930), (930, 1015)


def _views(words):
    for w in sorted(words, key=lambda w: -w["x"]):
        if c.NUM.match(w["t"]):
            return w["t"], c.num_val(w["t"])
    return None, None


VIS_PREFIX = {"pub": "Public", "unl": "Unlisted", "pri": "Private", "sch": "Scheduled", "dra": "Draft",
              "res": "Restricted", "mem": "Members"}


def parse_rows(pg):
    """One list row per Date cell (robust: a hovered row hides the Visibility word behind 'Pub..' / a tooltip).
    Rows with no date (drafts) are anchored on the Visibility word instead."""
    anchors = []
    for r in pg.rows(x0=X_DATE[0], x1=X_DATE[1], y0=335):
        if find_date(r["text"]):
            anchors.append(r["y"])
    for w in pg.words:
        if X_VIS[0] <= w["cx"] <= X_VIS[1] and w["cy"] > 335 and VIS.match(w["t"])                 and not any(abs(w["cy"] - y) < 25 for y in anchors):
            anchors.append(w["cy"])
    out = []
    line = lambda x0, x1, y0, y1: [w for w in pg.words if x0 <= w["cx"] <= x1 and y0 <= w["cy"] <= y1]
    for y in sorted(anchors):
        same = lambda x0, x1: sorted(line(x0, x1, y - 10, y + 10), key=lambda w: w["x"])
        date_main = " ".join(w["t"] for w in same(*X_DATE))
        sub = " ".join(w["t"] for w in sorted(line(*X_DATE, y + 12, y + 34), key=lambda w: w["x"]))
        vw = next((w["t"] for w in same(*X_VIS) if re.match(r"^[A-Za-z]{3}", w["t"])), "")
        vtxt = VIS_PREFIX.get(vw[:3].lower())
        dm, tm = find_date(date_main + " " + sub), TIME.search(date_main + " " + sub)
        sm = STATUS.search(sub) or STATUS.search(date_main)
        v_txt, v_val = _views(same(*X_VIEWS))
        notices = " ".join(w["t"] for w in line(*X_NOTICE, y - 10, y + 10) if w["t"] not in "—-–").strip()
        title = " ".join(w["t"] for w in same(*X_TITLE))
        row = {"title_start": title, "visibility": vtxt, "status": sm.group(1).capitalize() if sm else None,
               "date_text": dm, "views": v_val, "views_text": v_txt,
               "notices": notices or None, "y": int(y)}
        if row["views"] is None and (vtxt in ("Scheduled", "Draft") or (row["status"] or "") in ("Scheduled", "Draft")):
            row["views"], row["views_source"] = 0, "inferred (unpublished; OCR cannot see a lone 0)"
        if vtxt == "Scheduled" or (row["status"] or "") == "Scheduled":
            row["scheduled_date"] = row["date_text"]
            row["scheduled_time"] = f"{tm.group(1)} {tm.group(2).upper()}" if tm else None
        out.append(row)
    return out


def key(r):
    return (c.norm(r["title_start"])[:18], r["date_text"])


def pager(pg):
    m = PAGER.search(pg.text())
    return tuple(int(x) for x in m.groups()) if m else None


def scan_tab(h, cid, tab, tag, max_scrolls=40):
    url = f"https://studio.youtube.com/channel/{cid}/{TABS[tab]}"
    for attempt in (1, 2):
        c.sc("go", h, url); time.sleep(7)
        pg = c.ensure_studio(h, f"{tag}ct")
        got = c.channel_id_from_url(c.win_info(h).get("url"))
        if got != cid:
            raise c.StepFail(f"content page URL id {got} != expected {cid}")
        if not c.find_word(pg, r"^Visibility$"):
            # some accounts get a newer page model: a short preview with a "View all" link instead of the full list
            va = c.find_word(pg, r"^View$") and c.find_row(pg, r"View all")
            if va:
                c.log("content: preview layout -> clicking 'View all'")
                w = next((w for w in va["words"] if w["t"].lower() == "all"), va["words"][0])
                c.click_word(h, pg, w, dx=-18); time.sleep(6)
                pg = c.ensure_studio(h, f"{tag}va")
        c.section_check(h, tab, f"{tag}{tab}")       # right section: URL path + cropped heading screenshot
        if c.find_word(pg, r"^Visibility$") or re.search(r"No content|will show|show here|Upload videos|doesn.t have any", pg.text(), re.I):
            break
        time.sleep(3)
    else:
        raise c.StepFail("content list did not load")
    c.sc("wscroll", h, 1042, 600, -1, pg.shot); time.sleep(0.8)      # park the mouse off the table (hover hides cells)
    seen, rows, total, stale = {}, [], None, 0
    for i in range(max_scrolls):
        pg = c.read(h, f"{tag}_{tab}_{i}")
        for r in parse_rows(pg):
            k = key(r)
            if k not in seen:
                seen[k] = r; rows.append(r)
        p = pager(pg)
        if p:
            total = p
        if p and len(rows) >= p[2]:
            break
        before = len(rows)
        c.sc("wscroll", h, 1042, 600, 4, pg.shot); time.sleep(1.2)
        pg2 = c.read(h, f"{tag}_{tab}_{i}b")
        for r in parse_rows(pg2):
            k = key(r)
            if k not in seen:
                seen[k] = r; rows.append(r)
        p = pager(pg2) or total
        total = p or total
        if total and len(rows) >= total[2]:
            break
        stale = stale + 1 if len(rows) == before else 0
        if stale >= 2:
            break
    empty = False
    if not rows and not total:
        # OCR garbles the empty-state sentence ("No available content videos Upload"), so go structural:
        # table header on screen + still no rows and no pager after a settle wait = empty tab.
        time.sleep(3)
        pg = c.read(h, f"{tag}_{tab}_e")
        empty = bool(c.find_word(pg, r"^Visibility$")) and not parse_rows(pg) and not pager(pg)
    n_total = 0 if empty else (total[2] if total else None)
    for r in rows:
        r.pop("y", None)
    return {"tab": tab, "rows": rows, "listed_total": n_total, "collected": len(rows),
            "complete": (n_total is not None and len(rows) == n_total),
            "paged": bool(total and total[1] < total[2])}


def scan_content(h, cid, tag="cs", tabs=("videos", "shorts", "live"), retries=2):
    out = {}
    for tab in tabs:
        last = None
        for attempt in range(1, retries + 2):
            try:
                out[tab] = scan_tab(h, cid, tab, tag)
                if out[tab]["complete"]:
                    break
                last = f"incomplete: collected {out[tab]['collected']} of {out[tab]['listed_total']}"
                c.log(f"content/{tab}: {last} (attempt {attempt})")
            except c.Refuse:
                raise
            except Exception as e:
                last = f"{type(e).__name__}: {e}"
                c.log(f"content/{tab} attempt {attempt} failed: {last}")
                try:
                    c.ensure_studio(h, tag + "cr")
                except c.Refuse:
                    raise
                except Exception:
                    pass
        else:
            if tab not in out:
                out[tab] = {"tab": tab, "rows": [], "complete": False, "error": last}
    try:      # leave the window on the channel dashboard, not on whichever tab was scanned last
        c.ensure_dashboard(h, cid, tag + "bk")
    except c.Refuse:
        raise
    except Exception as e:
        c.log(f"content: could not return to dashboard ({e})")
    allrows = [r for t in out.values() for r in t["rows"]]
    summary = {"public": 0, "unlisted": 0, "private": 0, "scheduled": 0, "draft": 0, "other": 0}
    for r in allrows:
        summary[(r["visibility"] or "").lower() if (r["visibility"] or "").lower() in summary else "other"] += 1
    return {"tabs": out, "summary": summary, "total_items": len(allrows),
            "complete": all(t.get("complete") for t in out.values())}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hwnd", type=int, required=True)
    ap.add_argument("--tabs", default="videos,shorts,live")
    a = ap.parse_args()
    cid = c.channel_id_from_url(c.win_info(a.hwnd).get("url"))
    print(json.dumps(scan_content(a.hwnd, cid, "cs", tuple(a.tabs.split(","))), indent=1))
