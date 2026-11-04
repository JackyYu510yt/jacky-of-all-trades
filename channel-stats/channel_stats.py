"""channel-stats core: for a manager Gmail logged in on a named Chrome profile, verify we are logged INTO
the right accounts, visit every managed channel, read subscribers + 28-day views. Read-only.

  python channel_stats.py list --profile "Account Checks" --manager provitmolik@gmail.com
  python channel_stats.py run  --profile "Account Checks" --manager provitmolik@gmail.com
        [--only @handle,@handle] [--permissions all|first|none] [--owners owners.json] [--fault NAME]

Real OS-level input + OCR through ../google-login/screen_control.ps1. No CDP / WebDriver / debug port.
Exit: 0 all ok, 1 some channels failed, 2 refused (verify failed / wrong manager / stopped).
Per-channel statuses: ok | failed. A number that can't be read is None, never 0.
"""
import argparse, json, os, random, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
GL = os.path.join(os.path.expanduser("~"), ".claude", "skills", "google-login")
SC = os.path.join(GL, "screen_control.ps1")
SHOTS = os.path.join(HERE, "shots")
RESULTS = os.path.join(HERE, "results")
T0 = time.time()
STUDIO = "https://studio.youtube.com/"
EMAIL = re.compile(r"[\w.+\-]+@[\w\-]+\.[\w.]+")
HANDLE = re.compile(r"^@[\w.\-%]{3,}$")
NUM = re.compile(r"^[\d][\d.,]*[KMB]?$", re.I)


class Refuse(Exception):
    """Stop the whole run: wrong profile/manager, focus lost, STOP file."""


class StepFail(Exception):
    """One step failed; the channel loop may retry."""


def log(m):
    print(f"{time.time()-T0:6.1f}s  {m}", flush=True)


def sc(*args, timeout=90):
    if any(re.fullmatch(r"-\d+", str(a)) for a in args):
        # `-File` makes PowerShell read "-5" as a parameter NAME (every scroll-up silently failed). Quote it via -Command.
        q = " ".join("'" + str(a).replace("'", "''") + "'" for a in args)
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"& '{SC}' {q}"]
    else:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", SC, *map(str, args)]
    for tries in (1, 2):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
            break
        except subprocess.TimeoutExpired:
            # a stalled screen_control call (seen once: wkey hung >90s). One retry, then fail the STEP, never the run.
            log(f"screen_control {args[0]} timed out after {timeout}s (try {tries})")
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process -Filter \"Name='powershell.exe'\" | Where-Object { $_.CommandLine -like '*screen_control.ps1*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                           capture_output=True, timeout=30)
            if tries == 2:
                raise StepFail(f"screen_control {args[0]} timed out twice")
    out = (p.stdout or "").strip()
    if not out and p.stderr:
        out = "SC_STDERR: " + " ".join(p.stderr.split())[:300]
    for bad in ("FOCUS_LOST", "STOPPED", "OUTSIDE_WINDOW", "INPUT_BUSY"):
        if bad in out:
            raise Refuse(f"screen_control: {out.splitlines()[-1][:160]}")
    return out


def ps(cmd, timeout=60):
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout).stdout


# ---------------------------------------------------------------- window / page primitives
UIA_INFO = r'''
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]%H%)
$A=[System.Windows.Automation.AutomationElement]; $T=[System.Windows.Automation.TreeScope]::Descendants
$ec=New-Object System.Windows.Automation.PropertyCondition($A::ControlTypeProperty,[System.Windows.Automation.ControlType]::Edit)
$url=""; foreach($e in $root.FindAll($T,$ec)){ if($e.Current.Name -match "Address"){ try{$url=$e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value}catch{} } }
$tc=New-Object System.Windows.Automation.PropertyCondition($A::ControlTypeProperty,[System.Windows.Automation.ControlType]::TabItem)
$tabs=$root.FindAll($T,$tc).Count
@{url=$url;tabs=$tabs} | ConvertTo-Json -Compress
'''


def win_info(h):
    try:
        return json.loads(ps(UIA_INFO.replace("%H%", str(h))).strip() or "{}")
    except Exception:
        return {}


def win_title(h):
    out = sc("list")
    m = re.search(rf"^{h} \| (.*)$", out, re.M)
    return m.group(1).strip() if m else ""


def channel_id_from_url(u):
    m = re.search(r"/channel/(UC[\w\-]{20,24})", u or "")
    return m.group(1) if m else None


def focus(h):
    sc("focus", h)


def ocr_json(out):
    i = out.find("OCR: {")
    if i < 0:
        return None
    body = out[i + 5:]
    body = body[:body.rfind("}") + 1]
    return json.loads(re.sub(r"[\x00-\x1f\x7fâ€¨â€©]", " ", body), strict=False)


class Page:
    def __init__(self, shot, data):
        self.shot = shot
        self.words = [w for ln in data.get("lines", []) for w in ln.get("words", [])]
        for w in self.words:
            w["cx"], w["cy"] = w["x"] + w["w"] / 2, w["y"] + w["h"] / 2

    def rows(self, x0=0, x1=10 ** 6, y0=0, y1=10 ** 6, tol=9):
        ws = sorted((w for w in self.words if x0 <= w["cx"] <= x1 and y0 <= w["cy"] <= y1), key=lambda w: w["cy"])
        rows, cur = [], []
        for w in ws:
            if cur and abs(w["cy"] - cur[-1]["cy"]) > tol:
                rows.append(cur); cur = []
            cur.append(w)
        if cur:
            rows.append(cur)
        out = []
        for r in rows:
            r.sort(key=lambda w: w["x"])
            out.append({"y": sum(w["cy"] for w in r) / len(r), "x": r[0]["x"], "words": r,
                        "text": " ".join(w["t"] for w in r)})
        return out

    def text(self):
        return " ".join(w["t"] for w in sorted(self.words, key=lambda w: (round(w["cy"] / 9), w["x"])))


def read(h, tag, retries=2):
    os.makedirs(SHOTS, exist_ok=True)
    shot = os.path.join(SHOTS, f"{tag}.png")
    for i in range(retries + 1):
        out = sc("ocr", h, shot)
        d = ocr_json(out)
        if d is not None:
            return Page(shot, d)
        time.sleep(1.2)
    raise StepFail(f"ocr gave no result: {out[:120]}")


def click_word(h, page, w, dx=0, dy=0):
    x = int(w["cx"] + dx + random.uniform(-w["w"] * .2, w["w"] * .2))
    y = int(w["cy"] + dy + random.uniform(-2, 2))
    focus(h)
    sc("wclick", h, x, y, page.shot)


def find_word(page, pat, x0=0, x1=10 ** 6, y0=0, y1=10 ** 6):
    r = re.compile(pat, re.I)
    for w in page.words:
        if x0 <= w["cx"] <= x1 and y0 <= w["cy"] <= y1 and r.search(w["t"]):
            return w
    return None


def find_row(page, pat, **kw):
    r = re.compile(pat, re.I)
    for row in page.rows(**kw):
        if r.search(row["text"]):
            return row
    return None


def hkey(s):
    """Handle comparison key: OCR swaps look-alikes between reads (k8o4f / k804f, TM10 / TMIO)."""
    return (s or "").lower().translate(str.maketrans("oilsb", "01158"))


CACHE = os.path.join(HERE, "channels.json")


def cache_load():
    try:
        return json.load(open(CACHE, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def cache_get(manager, handle):
    return cache_load().get(manager.lower(), {}).get(hkey(handle))


def cache_put(manager, ch, cid):
    """Only ever called after the panel-checkmark verification passed for this channel."""
    c = cache_load()
    clash = [v["handle"] for k, v in c.get(manager.lower(), {}).items() if v["channel_id"] == cid and k != hkey(ch["handle"])]
    if clash:
        raise StepFail(f"channel id {cid} is already cached for {clash}; refusing to map {ch['handle']} to it")
    c.setdefault(manager.lower(), {})[hkey(ch["handle"])] = {"name": ch["name"], "handle": ch["handle"], "channel_id": cid,
                                                           "learned": time.strftime("%Y-%m-%d")}
    json.dump(c, open(CACHE, "w", encoding="utf-8"), indent=1)


def header_text(pg):
    return " ".join(r["text"] for r in pg.rows(x0=780, y0=90, y1=180))      # newer header: name box sits lower (y~140-165)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def num_val(s):
    if s is None:
        return None
    m = re.match(r"^([\d.,]+)([KMB]?)$", s.strip(), re.I)
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    return int(round(n * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2).upper()]))


# ---------------------------------------------------------------- recovery
def ensure_studio(h, tag="es"):
    """Get the window back to a normal Studio page: stray tab, wrong site, 'Oops' error, open dialog."""
    focus(h)
    for _ in range(3):
        title = win_title(h)
        info = win_info(h)
        if "YouTube Studio" in title and "studio.youtube.com" in (info.get("url") or ""):
            pg = read(h, f"{tag}_chk")
            if find_word(pg, r"^moderation$") and find_word(pg, r"^defaults$") and find_word(pg, r"^Agreements$"):
                log("Settings dialog open -> Close")
                cw = find_word(pg, r"^Close$", y0=600)
                if cw:
                    click_word(h, pg, cw)
                else:
                    sc("wkey", h, "{ESC}")
                time.sleep(1.5)
                continue
            if re.search(r"(?<![A-Za-z])Oops(?![A-Za-z])|Something went wrong", pg.text()) or title.startswith("Oops"):
                log("Studio error page -> reload")
                sc("wkey", h, "{F5}"); time.sleep(7)
                continue
            return pg
        log(f"not on Studio (title='{title[:50]}', tabs={info.get('tabs')}) -> recovering")
        if not title:
            raise Refuse("hwnd is not a visible window (window gone)")   # main() re-opens the profile via the verified opener
        # never Ctrl+W: UIA's tab count is unreliable and closing the only tab closes the window
        sc("go", h, STUDIO); time.sleep(7)
    raise StepFail("could not get back onto Studio")


SECTIONS = {   # section -> (URL path regex, big page-heading regex read from the cropped screenshot)
    "dashboard": (r"/channel/UC[\w\-]+/?(\?|$)", r"Channel dashboard|Channel analytics"),
    "videos": (r"/videos/upload", r"^Videos$|^Channel$|^content$"),
    "shorts": (r"/videos/short", r"^Shorts$|^Channel$|^content$"),
    "analytics": (r"/analytics/tab-overview", r"^Channel$|^analytics$|^Insights$|^Analytics$"),
    "live": (r"/videos/live", r"^Live|^Channel$|^content$"),
    "insights": (r"/analytics/hub_overview", r"^insights$"),     # new page model: "Channel insights" (+ a banner above it)
}
SECTION_CROP = {"insights": "90,165,700,200"}                   # heading sits lower under the banner
HEAD_CROP = "90,165,700,115"     # x,y,w,h of the page title strip, right after navigation and before any scroll


def section_check(h, expect, tag="sec"):
    """Prove we are on the expected Studio section by two independent reads: the URL path (UI Automation) and a
    screenshot cropped to just the page heading (OCR). Raises StepFail naming what it saw instead."""
    path_re, head_re = SECTIONS[expect]
    url = win_info(h).get("url") or ""
    if not re.search(path_re, url):
        raise StepFail(f"section: expected {expect}, URL is {url[:90]}")
    shot = os.path.join(SHOTS, f"{tag}_head.png")
    words = []
    for _ in range(3):        # the heading reads "Channel content" first and the section name once loaded
        d = ocr_json(sc("ocr", h, shot, SECTION_CROP.get(expect, HEAD_CROP))) or {}
        words = [w["t"] for ln in d.get("lines", []) for w in ln.get("words", [])]
        if re.search(head_re, " ".join(words), re.I) or any(re.search(head_re, w, re.I) for w in words):
            return words
        time.sleep(2)
    raise StepFail(f"section: expected heading for {expect}, cropped screenshot reads {words}")


def ensure_dashboard(h, cid, tag="ed"):
    """The numbers card lives on the Channel dashboard. Any other Studio page (Content/Shorts/Live tab left behind by
    a content scan, Analytics, ...) -> navigate to this channel's dashboard, and confirm by URL, not by hope."""
    pg = ensure_studio(h, tag)
    for _ in range(2):
        url = win_info(h).get("url") or ""
        if channel_id_from_url(url) == cid and re.search(r"/channel/UC[\w\-]+/?(\?|$)", url):
            return pg
        log(f"not on the channel dashboard ({url[:70]}) -> go to it")
        sc("go", h, f"https://studio.youtube.com/channel/{cid}"); time.sleep(7)
        pg = ensure_studio(h, tag + "2")
    url = win_info(h).get("url") or ""
    if channel_id_from_url(url) != cid:
        raise StepFail(f"could not reach the dashboard of {cid} (at {url[:80]})")
    section_check(h, "dashboard", tag)
    return pg


def close_menus(h):
    focus(h)
    sc("wkey", h, "{ESC}"); time.sleep(0.5)
    sc("wkey", h, "{ESC}"); time.sleep(0.5)


# ---------------------------------------------------------------- account menu / switcher
def open_menu(h, tag):
    """Avatar (top right) -> first-level menu with the channel name + @handle and 'Switch account'."""
    for attempt in range(3):
        focus(h)
        pg = read(h, f"{tag}_hdr")
        hdr = pg.rows(x0=780, y0=90, y1=140)
        box = find_row(pg, r"You.re a manager") or find_row(pg, r"You.re an? (owner|editor)")
        if box and box["words"][0]["cx"] > 780 and box["words"][0]["cy"] < 200:
            # newer header: a wide "Name / You're a manager" box instead of a bare avatar circle
            click_word(h, pg, box["words"][0], dx=0)
        elif hdr:
            click_word(h, pg, hdr[0]["words"][-1], dx=-30)
        else:
            sc("wclick", h, 940, 113, pg.shot)
        time.sleep(1.8)
        pg = read(h, f"{tag}_menu")
        if find_word(pg, r"^switch$") or find_row(pg, r"Switch account"):
            return pg
        log("menu not open, retry")
        close_menus(h)
    raise StepFail("could not open the account menu")


def menu_identity(pg):
    """Name + handle from the first-level menu."""
    hw = [w for w in pg.words if HANDLE.match(w["t"]) and w["cx"] > 600 and w["cy"] < 300]
    if not hw:
        return None, None
    hw.sort(key=lambda w: w["cy"])
    h = hw[0]
    name_row = [r for r in pg.rows(x0=600, y0=h["cy"] - 40, y1=h["cy"] - 6) if r["words"]]
    name = name_row[-1]["text"] if name_row else None
    return name, h["t"]


def open_switcher(h, tag):
    """Menu -> 'Switch account' -> the Accounts sub-panel. Success = its 'Accounts' header AND the manager
    email are on screen (the first-level menu also shows an @handle, so that alone proves nothing)."""
    for attempt in range(3):
        pg = open_menu(h, tag)
        w = find_word(pg, r"^Switch$")
        if not w:
            sw = find_row(pg, r"Switch account")
            w = sw["words"][0] if sw else None
        if not w:
            close_menus(h); continue
        click_word(h, pg, w, dx=40)
        time.sleep(2.2)
        pg = read(h, f"{tag}_sw")
        if find_word(pg, r"^Accounts$", x0=560, y1=160) and any(EMAIL.search(w["t"]) for w in pg.words if w["cx"] > 560):
            return pg
        log("switcher sub-panel not open, retry")
        close_menus(h)
    raise StepFail("switcher did not open")


def parse_switcher(pg):
    """-> (manager_email, [ {name, handle, manager(bool), subs, y, x_name} ]) from one OCR page."""
    panel = [w for w in pg.words if w["cx"] > 560]
    emails = [w for w in panel if EMAIL.search(w["t"])]
    email = EMAIL.search(emails[0]["t"]).group(0) if emails else None
    rows = pg.rows(x0=630, x1=870)            # the text column only: no avatar letters, no page text
    lim = other_accounts_y(pg)
    if lim:                                    # below "Other accounts" are ANOTHER login's channels: never ours
        rows = [r for r in rows if r["y"] < lim - 5]
    chans = []
    for i, r in enumerate(rows):
        hw = next((w for w in r["words"] if HANDLE.match(w["t"])), None)
        if hw:
            prev = rows[i - 1] if i else None
            nxt = rows[i + 1] if i + 1 < len(rows) else None
            if not prev:
                continue
            if r["y"] - prev["y"] > 40 or "manager" in prev["text"].lower() or "subscriber" in prev["text"].lower():
                # short names ("Ri Ra") sometimes drop out of OCR: the row above is then the previous channel's
                # subtitle. The handle is still a real row; its name is unknown, its y is one line up.
                name, y, x = None, r["y"] - 20, hw["cx"] - 8 - 0
                x = rows[i]["words"][0]["cx"] - 40
            else:
                name, y, x = prev["text"].strip(), prev["y"], prev["words"][0]["cx"]
            sub = nxt["text"] if nxt and nxt["y"] - r["y"] < 36 else ""
            m = re.search(r"(?<![\w.,])(\d[\d.,]*[KMB]?)\s+subs", sub, re.I)
            chans.append({"name": name, "handle": hw["t"], "is_manager": bool(re.search(r"manager", sub, re.I)),
                          "subs_listed": m.group(1) if m else ("0" if re.search(r"(?<![A-Za-z])No\s+su", sub, re.I) else None),
                          "y": y, "x": x, "shot": pg.shot})
    return email, chans


def other_accounts_y(pg):
    """y of the 'Other accounts' header (another signed-in login's channels start below it), or None."""
    r = find_row(pg, r"Other accounts|^accounts$", x0=560, x1=870, y0=300)
    return r["y"] if r else None


def expected_rows(pg):
    """Count avatar circles in the panel (runs of coloured pixels down x=578..622): independent of OCR."""
    from PIL import Image
    im = Image.open(pg.shot).convert("RGB")
    runs, cur = 0, 0
    lim = other_accounts_y(pg)
    for y in range(205, min(im.height, (int(lim) - 15) if lim else 925)):
        colored = any(max(im.getpixel((x, y))) - min(im.getpixel((x, y))) > 40 or sum(im.getpixel((x, y))) < 600
                      for x in range(585, 616, 5))
        if colored:
            cur += 1
        else:
            if cur >= 30:
                runs += 1
            cur = 0
    if cur >= 30:
        runs += 1
    return runs


def current_handle(pg, chans):
    """The row with the checkmark (= the channel we are logged in on). OCR can't read the tick, so look at
    pixels: the tick is dark ink in a narrow column right of the row text; no other row has ink there."""
    from PIL import Image
    im = Image.open(pg.shot).convert("L")
    best = (0, None)
    for c in chans:
        y0, y1 = int(c["y"]) - 8, int(c["y"]) + 30
        ink = sum(1 for x in range(800, 848) for y in range(max(y0, 0), min(y1, im.height))
                  if im.getpixel((x, y)) < 110)
        if ink > best[0]:
            best = (ink, c)
    return best[1]["handle"] if best[0] >= 25 else None


def panel_state(h, tag, expect_manager):
    """Open Switch account and read: manager email (must match), channel rows, which one is checked."""
    pg = open_switcher(h, tag)
    email, chans = parse_switcher(pg)
    if not email or email.lower() != expect_manager.lower():
        raise Refuse(f"WRONG MANAGER: panel says logged in as {email}, expected {expect_manager}")
    return pg, chans, current_handle(pg, chans)


def scroll_panel(h, pg, notches):
    focus(h)
    sc("wscroll", h, 800, 620, notches, pg.shot)
    time.sleep(0.8)


def panel_complete(pg):
    """True when the panel's footer (Add account / Sign out) is visible = the list isn't cut off."""
    return bool(find_row(pg, r"Add account|Sign out", x0=560, x1=870)) or bool(other_accounts_y(pg))


def list_channels(h, tag="list"):
    """All channel rows. Completeness is checked against the avatar count; a short parse is re-read
    (union by handle) up to 3 times, and a still-short list is a hard stop, never a silent gap."""
    pg = open_switcher(h, tag)
    email, chans = parse_switcher(pg)
    seen = {hkey(c["handle"]): c for c in chans}
    want = expected_rows(pg)
    for i in range(3):
        if len(seen) >= want and panel_complete(pg):
            break
        if not panel_complete(pg):
            scroll_panel(h, pg, 6)
        else:
            time.sleep(0.8)
        pg = read(h, f"{tag}_sw{i}")
        e2, more = parse_switcher(pg)
        for c in more:
            seen.setdefault(hkey(c["handle"]), c)
        want = max(want, expected_rows(pg)) if panel_complete(pg) else want
    close_menus(h)
    if want and len(seen) < want:
        raise Refuse(f"channel list incomplete: parsed {len(seen)} rows but the panel shows {want} avatars")
    log(f"panel avatars={want} parsed={len(seen)}")
    return email, list(seen.values())


def switch_to(h, handle, tag, pg=None):
    """Bring the row with this handle into view (panel already open, or open it), click it."""
    pg = pg or open_switcher(h, tag)
    for i in range(6):
        _, chans = parse_switcher(pg)
        hit = [c for c in chans if hkey(c["handle"]) == hkey(handle)]
        if hit:
            c = hit[0]
            focus(h)
            sc("wclick", h, int(c["x"] + 20), int(c["y"]), pg.shot)
            time.sleep(6)
            return
        if panel_complete(pg) and i > 0:
            break
        scroll_panel(h, pg, 5)
        pg = read(h, f"{tag}_sw{i}")
    raise StepFail(f"handle {handle} not found in switcher")


# ---------------------------------------------------------------- verification + reading
def verify_identity(h, ch, tag, manager):
    """Switch-account panel: logged in as the expected manager AND the checked row is the channel we meant.
    Matched by @handle, never by display name (several channels are both called "Sara Sara")."""
    pg, chans, cur = panel_state(h, tag, manager)
    close_menus(h)
    if not cur or hkey(cur) != hkey(ch["handle"]):
        raise StepFail(f"identity mismatch: panel check is on {cur!r}, wanted {ch['handle']!r}")
    cid = channel_id_from_url(win_info(h).get("url"))
    if not cid:
        raise StepFail("no channel id in the URL")
    return cid


def read_card(pg):
    """Channel analytics card -> {subscribers, views_28d, period_ok, raw}. None when unreadable (never 0)."""
    head = None
    for w in pg.words:
        if re.match(r"^Channel$", w["t"], re.I):
            nx = [v for v in pg.words if re.match(r"^analytics$", v["t"], re.I) and 0 < v["x"] - w["x"] < 120
                  and abs(v["cy"] - w["cy"]) < 8]
            if nx and w["cx"] > 300 and w["cy"] > 150:       # not the sidebar / page title
                head = {"x": w["x"], "y": w["cy"]}
                break
    if not head:
        raise StepFail("Channel analytics card not on page")
    x0 = head["x"] - 25
    card = pg.rows(x0=x0, x1=x0 + 300, y0=head["y"] - 5, y1=head["y"] + 330)
    subs = views = None
    period_ok = False
    for i, r in enumerate(card):
        if re.search(r"Current subscribers", r["text"], re.I) and i + 1 < len(card):
            for nr in card[i + 1:i + 3]:
                t = nr["words"][0]["t"]
                if re.match(r"^[Oo]$", t):
                    t = "0"
                if NUM.match(t):
                    subs = t; break
        if re.search(r"^Summary", r["text"], re.I):
            for nr in card[i + 1:i + 3]:
                if re.search(r"Last 28 days", nr["text"], re.I):
                    period_ok = True
        if period_ok and views is None and re.match(r"^Views\b", r["text"], re.I):
            for w in r["words"][1:]:
                if NUM.match(w["t"]):
                    views = w["t"]; break
    return {"_head": (head["x"], head["y"]), "subscribers": subs, "views_28d": views, "period_ok": period_ok, "subs_value": num_val(subs),
            "views_value": num_val(views), "rounded": any(v and re.search(r"[KMB]$", v, re.I) for v in (subs, views))}


def views_glyph_present(pg):
    """Summary 'Views' value is a lone small digit Windows OCR cannot see ("Views 5 -" reads as just "Views").
    True when ink sits in the value column on the Views row, i.e. there IS a number there we simply cannot read."""
    from PIL import Image
    lab = find_word(pg, r"^Views$", x0=415, x1=520, y0=480, y1=700)
    if not lab:
        return False
    im = Image.open(pg.shot).convert("L")
    y = int(lab["cy"])
    return any(im.getpixel((x, yy)) < 110 for x in range(600, 664) for yy in range(y - 9, y + 9))


def read_big_number(h, head, tag):
    """The big 'Current subscribers' digit is sometimes dropped by the full-page OCR. Zoomed OCR of just that strip.
    Returns the text or None - never a guess."""
    x, y = int(head[0]) - 10, int(head[1]) + 30
    out = sc("ocr", h, os.path.join(SHOTS, f"{tag}_big.png"), f"{x},{y},260,90")
    d = ocr_json(out)
    if not d:
        return None
    for ln in d.get("lines", []):
        for w in ln.get("words", []):
            t = "0" if re.match(r"^[Oo]$", w["t"]) else w["t"]
            if NUM.match(t):
                return t
    return None


def glyph_present(shot, head):
    """Dark ink in the big-number slot under 'Current subscribers' (OCR returns nothing for a bold lone 0)."""
    from PIL import Image
    im = Image.open(shot).convert("L")
    x0, y0 = int(head[0]), int(head[1]) + 35
    ink = sum(1 for x in range(x0, x0 + 60) for y in range(y0, min(y0 + 50, im.height)) if im.getpixel((x, y)) < 100)
    return ink >= 40


def read_permissions(h, tag):
    """Settings -> Permissions: owner email + manager emails. Always closes the dialog."""
    pg = read(h, f"{tag}_p0")
    g = find_word(pg, r"^Settings$", x1=200, y0=800)
    focus(h)
    if g:
        click_word(h, pg, g)
    else:
        sc("wclick", h, 41, 971, pg.shot)          # collapsed sidebar: the gear icon, bottom-left
    time.sleep(2.5)
    try:
        pg = read(h, f"{tag}_p1")
        pw = find_word(pg, r"^Permissions$", x1=300, y0=300)
        if not pw:
            raise StepFail("Settings dialog / Permissions item not found")
        click_word(h, pg, pw)
        time.sleep(2.5)
        pg = read(h, f"{tag}_p2")
        if not find_row(pg, r"Permissions for"):
            raise StepFail("Permissions page did not open")
        owner_w = find_word(pg, r"^Owner$", x0=500)
        emails = [(EMAIL.search(w["t"]).group(0), w["cy"]) for w in pg.words if EMAIL.search(w["t"]) and w["cx"] > 300]
        if not owner_w or not emails:
            raise StepFail("no Owner / emails on the Permissions page")
        owner = min(emails, key=lambda e: abs(e[1] - owner_w["cy"]))[0]
        managers = [e for e, _ in emails if e != owner]
        return {"owner": owner.lower(), "managers": [m.lower() for m in managers]}
    finally:
        cw = None
        try:
            pg = read(h, f"{tag}_p3")
            cw = find_word(pg, r"^Close$", y0=600)
            if cw:
                click_word(h, pg, cw)
                time.sleep(1.2)
            else:
                close_menus(h)
        except Exception:
            close_menus(h)


# ---------------------------------------------------------------- faults (tests only)
def inject(h, name):
    log(f"FAULT injected: {name}")
    focus(h)
    if name == "wrongpage":                       # tab left on a non-Studio page
        sc("go", h, "https://support.google.com/youtube/answer/9072033"); time.sleep(5)
    elif name == "helptab":                       # a stray second tab becomes the active one
        sc("wkey", h, "^t"); time.sleep(1)
        sc("go", h, "https://support.google.com/youtube/answer/9072033"); time.sleep(5)
    elif name == "menuopen":                      # a menu left open
        open_menu(h, "fault")
    elif name == "reload":
        sc("wkey", h, "{F5}"); time.sleep(0.5)


# ---------------------------------------------------------------- orchestration
def open_profile(profile):
    p = subprocess.run([sys.executable, os.path.join(HERE, "chrome_profile.py"), "open", profile],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise Refuse((p.stdout + p.stderr).strip()[:300])
    return json.loads(p.stdout)


def content_block(h, cid, tag):
    import content_scan
    t = time.time()
    r = content_scan.scan_content(h, cid, tag)
    log(f"content: {r['total_items']} items {r['summary']} complete={r['complete']} ({time.time() - t:.0f}s)")
    return r


def dashboard_block(h, cid, ch, tag):
    import dashboard_scan
    r = dashboard_scan.scan_dashboard(h, cid, tag + "d", label=re.sub(r"[^\w\-]", "", ch["handle"]))
    log(f"dashboard: {r.get('status')} latest={r.get('latest_video', {}).get('views_detail')} subs={r.get('channel_analytics', {}).get('subscribers')}")
    return r


def analytics_block(h, cid, ch, tag):
    import analytics_scan
    t = time.time()
    r = analytics_scan.scan_analytics(h, cid, tag, label=re.sub(r"[^\w\-]", "", ch["handle"]))
    log(f"analytics: {r.get('status')} views={r.get('views')} realtime48h={r.get('realtime_views_48h')} ({time.time() - t:.0f}s)")
    return r


def process_channel(h, ch, a, owners, first_perm, wrong_first):
    tag = re.sub(r"\W", "", ch["handle"])[:20]
    if wrong_first:
        # test fault: click a DIFFERENT channel first, so identity verification must catch it
        log("FAULT: switching to a wrong channel first")
    last = None
    for attempt in range(1, a.retries + 2):
        try:
            ensure_studio(h, tag)
            cid = None
            known = cache_get(a.manager, ch["handle"])
            if known and not (attempt == 1 and wrong_first) and a.fast:
                # Already on it? The URL's UC id is free to read: if it equals this channel's known id, no switching.
                pg = ensure_studio(h, tag + "f")
                got = channel_id_from_url(win_info(h).get("url"))
                if got == known["channel_id"] and norm(known["name"])[:6] in norm(header_text(pg)):
                    cid = got
                    log(f"{ch['handle']}: already on it (URL id {cid} matches) - no switch")
                else:
                    why = "URL id differs" if got != known["channel_id"] else "header name not matched"
                    log(f"{ch['handle']}: fast path refused ({why}: URL {got}, known {known['channel_id']}) -> switch accounts and check")
            if not cid:
                pg, chans, cur = panel_state(h, tag + "pre", a.manager)
                target = wrong_first["handle"] if (attempt == 1 and wrong_first) else ch["handle"]
                if cur and hkey(cur) == hkey(target):
                    close_menus(h)
                else:
                    switch_to(h, target, tag, pg)
                    ensure_studio(h, tag)
                cid = verify_identity(h, ch, tag + "v", a.manager)
                cache_put(a.manager, ch, cid)         # learned only after the checkmark + handle check passed
            perm = None
            if a.permissions == "all" or (a.permissions == "first" and first_perm):
                perm = read_permissions(h, tag)
                if a.manager.lower() not in perm["managers"]:  # optional deep check (--permissions)
                    raise StepFail(f"manager {a.manager} not in Permissions managers {perm['managers']}")
                exp = next((v for k, v in owners.items() if hkey(k) == hkey(ch["handle"])), None)
                if exp and exp.lower() != perm["owner"]:
                    raise Refuse(f"{ch['handle']}: owner is {perm['owner']}, expected {exp}")
            if a.content_only:
                res = {"status": "ok", "attempts": attempt, "channel_id": cid, "content": content_block(h, cid, tag)}
                if a.analytics:
                    res["analytics"] = analytics_block(h, cid, ch, tag)
                if a.dashboard:
                    res["dashboard"] = dashboard_block(h, cid, ch, tag)
                return res
            pg = ensure_dashboard(h, cid, tag + "c")
            card = read_card(pg)
            head = card.pop("_head")
            if card["subscribers"] is None:
                card["subscribers"] = read_big_number(h, head, tag)
                card["subs_value"] = num_val(card["subscribers"])
                if card["subscribers"] is not None:
                    log(f"{ch['handle']}: subscribers read by zoomed OCR = {card['subscribers']}")
            card["subs_source"] = "ocr"
            if card["subscribers"] is None and ch.get("subs_listed") == "0" and glyph_present(pg.shot, head):
                # OCR can't see a lone bold 0. Two independent sources agree: the Switch-account panel says
                # "No subscribers" and the card has a digit glyph where the number goes.
                card["subscribers"], card["subs_value"] = "0", 0
                card["subs_source"] = "switcher:No subscribers + glyph present"
                log(f"{ch['handle']}: subscribers = 0 (panel says No subscribers, glyph present, OCR blind to it)")
            insights_card = bool(re.search(r"channel\s+insights|realtime\s+data|live\s+count", pg.text(), re.I))
            glyph = card["views_28d"] is None and card["period_ok"] and views_glyph_present(pg)
            if card["views_28d"] is None and (insights_card or glyph) and card["period_ok"] and card["subscribers"] is not None:
                # Insights-flavour card: "Views 4 —" loses its small bold number in OCR. Not a reason to drop the channel;
                # the Insights analytics scan reads the same number from the big card.
                card["views_note"] = "unreadable on the dashboard Summary card (insights layout); use analytics.views"
                card["views_pending_analytics"] = True
                log(f"{ch['handle']}: dashboard card: subs read, Summary views glyph present but unreadable (noted; analytics fills it)")
            elif not card["period_ok"] or card["subscribers"] is None or card["views_28d"] is None:
                raw = [[(w["t"], round(w["x"])) for w in r["words"]] for r in pg.rows(x0=415, x1=705, y0=440, y1=600)]
                raise StepFail(f"card unreadable: {card} summary_words={raw}")
            final = os.path.join(SHOTS, f"final_{tag}.png")
            try:
                os.replace(pg.shot, final)
            except OSError:
                final = pg.shot
            res = {"status": "ok", "attempts": attempt, "channel_id": cid, "owner_email": perm and perm["owner"],
                   "manager_emails": perm and perm["managers"], **card, "shot": final}
            if a.content:
                res["content"] = content_block(h, cid, tag)
            if a.analytics:
                res["analytics"] = analytics_block(h, cid, ch, tag)
                an_v = res["analytics"].get("views")
                if res.pop("views_pending_analytics", False) and res["views_28d"] is None and res["analytics"].get("status") == "ok" and an_v is not None:
                    res["views_28d"], res["views_value"] = str(an_v), an_v
                    res["views_source"] = "analytics headline (Summary digit unreadable by OCR)"
            res.pop("views_pending_analytics", None)
            if a.dashboard:
                res["dashboard"] = dashboard_block(h, cid, ch, tag)
            return res
        except Refuse:
            raise
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            log(f"{ch['handle']} attempt {attempt} failed: {last}")
            wrong_first = None
            try:
                close_menus(h)
                ensure_studio(h, tag + "r")
            except Refuse:
                raise
            except Exception:
                pass
    return {"status": "failed", "attempts": a.retries + 1, "error": last}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "run"])
    ap.add_argument("--profile", required=True)
    ap.add_argument("--manager", required=True, help="expected manager Gmail")
    ap.add_argument("--only")
    ap.add_argument("--permissions", choices=["all", "first", "none"], default="none")
    ap.add_argument("--owners", help="json {handle: expected TM gmail}")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--no-fast", dest="fast", action="store_false", help="always verify through the panel (re-learns ids)")
    ap.add_argument("--dashboard", action="store_true", help="also read the Channel dashboard cards + save screenshots")
    ap.add_argument("--analytics", action="store_true", help="also read Analytics > Overview + save a screenshot")
    ap.add_argument("--content", action="store_true", help="also scan the Content tab (videos/shorts/live)")
    ap.add_argument("--content-only", dest="content_only", action="store_true", help="verify channel, scan Content only")
    ap.add_argument("--fault")
    ap.add_argument("--wrong-first", help="test: handle to (wrongly) click before the first real channel")
    a = ap.parse_args()
    os.makedirs(RESULTS, exist_ok=True)
    owners = {k.lower(): v for k, v in json.load(open(a.owners)).items()} if a.owners else {}

    try:
        pr = open_profile(a.profile)
        h = pr["hwnd"]
        log(f"profile '{pr['profile']}' verified (hwnd {h}, already_open={pr['already_open']})")
        sc("resize", h, 1053, 1044, 0, 0)
        ensure_studio(h, "start")
        if a.fault:
            inject(h, a.fault)
            ensure_studio(h, "afterfault")
        email, chans = list_channels(h)
        log(f"switcher manager email: {email}")
        if not email or email.lower() != a.manager.lower():
            raise Refuse(f"WRONG MANAGER: logged in as {email}, expected {a.manager}")
        mine = [c for c in chans if c["is_manager"]]
        log(f"{len(chans)} rows, {len(mine)} managed channels (skipped own: {[c['name'] for c in chans if not c['is_manager']]})")
        if a.cmd == "list":
            print(json.dumps({"manager": email, "channels": [{k: c[k] for k in ("name", "handle", "subs_listed")} for c in mine]}, indent=1))
            return 0
        if a.only:
            want = {hkey(x.strip()) for x in a.only.split(",")}
            mine = [c for c in mine if hkey(c["handle"]) in want]
        results = []
        for i, c in enumerate(mine):
            wf = None
            if a.wrong_first and i == 0:
                wf = next((x for x in chans if hkey(x["handle"]) == hkey(a.wrong_first)), None)
            for _try in (1, 2):
                try:
                    r = process_channel(h, c, a, owners, i == 0, wf)
                    break
                except Refuse as e:
                    if "not a visible window" in str(e) and _try == 1:
                        log("window disappeared -> re-opening the profile (verified)")
                        pr = open_profile(a.profile); h = pr["hwnd"]
                        sc("resize", h, 1053, 1044, 0, 0)
                    else:
                        raise
            r.update({"name": c["name"], "handle": c["handle"], "subs_listed": c["subs_listed"],
                      "manager": email, "profile": pr["profile"], "read_at": time.strftime("%Y-%m-%d %H:%M:%S")})
            results.append(r)
            log(f"{c['handle']}: {r['status']} " + (f"subs={r.get('subscribers')} views28d={r.get('views_28d')}" if r["status"] == "ok" else r["error"]))
        out = os.path.join(RESULTS, f"channel-stats-{time.strftime('%Y%m%d-%H%M%S')}.json")
        json.dump({"manager": email, "profile": pr["profile"], "results": results}, open(out, "w"), indent=1)
        bad = [r for r in results if r["status"] != "ok"]
        log(f"saved {out}: {len(results) - len(bad)} ok, {len(bad)} failed")
        return 1 if bad else 0
    except Refuse as e:
        log(f"REFUSED: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

