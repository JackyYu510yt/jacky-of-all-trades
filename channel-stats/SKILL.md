---
name: channel-stats
description: Read live channel data from YouTube Studio for every channel under a manager Gmail that is already logged in on a Chrome profile (TM / ECM managers) - subscribers, 28-day views, the Content tab (every video's visibility, status, date, views; scheduled/draft), and the Analytics Overview (28-day views, watch time, subs change, 48h realtime) plus a saved Analytics screenshot. Use when the user says "check channel stats", "get the views for the TM manager", "scrape the analytics", "what videos are scheduled", "screenshot the analytics". Live skill: real OS-level mouse/keyboard + screenshots/OCR, never Chrome remote debugging or WebDriver.
---

# Channel stats

For one manager Gmail logged in on a normal Chrome profile: verify the profile and the account, visit each
managed channel, record its numbers. Output is JSON in `results/` (dashboard wiring is deferred, by the user).
Structure: a TM Manager Gmail manages ~10 TM Gmail channels (testing); passing ones later move to an ECM Manager.

## Rules
- **No automation protocol.** No `--remote-debugging-port`, Selenium, Playwright, CDP, no injected userscripts.
  Input is `../google-login/screen_control.ps1` (real mouse/keyboard) + Windows OCR.
- Read-only. Never click Publish / Delete / settings. Never type into the page.
- A number that can't be read is `None`, never 0. (Exception: subscribers 0, inferred - see below.)
- **Match channels by @handle, never display name** (several channels are both "Sara Sara").
- Never Ctrl+W (UIA tab count is wrong: Studio's own sub-tabs count). Never OCR-click a bare word like
  "permissions" (opens a Help tab). Never write `\b` in an edit string (tool escaping turns it into a backspace).

## Run
```
python channel_stats.py list --profile "Account Checks" --manager provitmolik@gmail.com
python channel_stats.py run  --profile "Account Checks" --manager provitmolik@gmail.com
      [--only @handle,@handle] [--content] [--content-only] [--analytics] [--dashboard] [--retries 2] [--no-fast]
```
Exit 0 all ok / 1 some channels failed / 2 refused (wrong profile / wrong manager / stopped). A full channel is
~1-3 min; check free RAM first (>~5 GB) - a run was once killed for low memory.

## How identity is proven (every channel, before any number is recorded)
1. `chrome_profile.py open "<profile>"`: Chrome has ONE process; the window is found by its toolbar profile
   button name (UIA) = the requested profile exactly. Unknown/ambiguous -> exit 2 `VERIFY FAILED`.
2. Switch-account panel: top email must equal `--manager` else `WRONG MANAGER` (exit 2). Checked on every panel open.
3. Channel list = panel rows; avatars counted by pixels, parsed rows must be >= avatars. Own row skipped.
4. Per channel: fast path - URL UC id equals the cached id for that @handle and header name matches -> no switch.
   Otherwise switch via the panel, then verify the panel's checkmark row == expected @handle (pixel check, handle
   compared after look-alike normalisation) AND read the URL UC id. Id cached only after that passes.
5. A channel that fails identity is reported failed; numbers are never read off it.

## Sections (URL first, then verified)
Direct URLs only work for the channel the window is already on (another channel's URL = "Oops, you don't have
permission"). After switching: dashboard `/channel/<UC>`, content `/channel/<UC>/videos/upload|short|live`,
analytics `/channel/<UC>/analytics/tab-overview/period-default` (hyphens, not `=`; the old `tab-realtime` URL is blank).
`section_check()` after every navigation: URL path AND a cropped screenshot of the page-heading strip. Wrong
section -> StepFail. `ensure_dashboard()` before reading the dashboard card (scans leave the window elsewhere).

## What each part reads
- **Dashboard card** (`channel_stats.py`): subscribers + Last 28 days views. Zero subscribers: OCR can't see a lone
  bold 0, so subs=0 only when the panel says "No subscribers" AND a digit glyph is present (`subs_source` records it).
- **Content** (`content_scan.py`, `--content`): tabs Videos/Shorts/Live. Per item: title_start (list truncates),
  visibility, status, date_text, views, notices, scheduled_date/scheduled_time. The list shows no scheduled TIME
  -> `scheduled_time` is null (opening each video would be needed). Complete only if collected == pager total
  ("1-N of N"; OCR reads "14 of 14" as "140f14" - regex handles it). >30 videos (second page) NOT handled: reports
  incomplete. Empty tab = header present, no rows, no pager (OCR garbles the empty-state sentence).
  Hover hides the Visibility cell, so rows anchor on the Date cell and the mouse is parked at the scrollbar.
- **Analytics** (`analytics_scan.py`, `--analytics`): range, "Last 28 days", views (headline sentence and Views card
  must agree), watch hours, subscribers change, Realtime subscribers + views last 48h. The right panel is a
  carousel (Realtime / Latest content / ...) whose first card varies and can rotate on its own: the scanner steps
  the > arrow until "Realtime" shows. Saves a cropped screenshot of the exact parsed capture to
  `evidence/<handle>/analytics-<timestamp>.png` + `analytics-latest.png`. Per-day splits (the old userscript's
  hourly-bar hover) are NOT built; user chose to live with the 48h total.
- **Dashboard** (`dashboard_scan.py`, `--dashboard`): Latest video performance (title best-effort from the
  thumbnail overlay, age, rank "2 of 10" - OCR reads it "20f10", views, CTR %, avg view duration), Channel
  analytics (subscribers, +N in last 28 days, 28d views, watch hours, Top content last 48h rows) and Recent
  subscribers (name + count). Comments/likes (small grey icon row) are NOT readable by OCR -> absent; the
  screenshot shows them. Saves `evidence/<handle>/dashboard-top-*.png` + `dashboard-lower-*.png` (+ `-latest`).
- Not built: Analytics top-content table, other tabs (Content/Audience/Trends), per-video IDs, daily views.

## Page-model variants seen live (2026-11-02, manager fgnf70093@gmail.com)
- **Account menu**: some headers show a wide "Name / You're a manager" box instead of an avatar circle; `open_menu`
  clicks that box. The switcher panel's lower part ("Other accounts") lists ANOTHER login's channels: parsing and the
  avatar count stop at that header. A short name ("Ri Ra") can drop out of OCR: the row is kept with name None.
- **Content**: `/content` is a preview ("Discover your new content page", 3 cards, "View all"). `/videos/upload` still
  lands on the full list, and if the preview shows, `scan_tab` clicks "View all" BEFORE the section check (proven).
  Dates can be day-first ("4 Nov 2026"): normalised to "Nov 4, 2026". Scheduled/draft rows: views inferred 0.
  Heading sits lower on this layout: `HEAD_CROP` is 115px tall.
- **Insights** (`insights_scan.py`): `/analytics/tab-overview` redirects to `/analytics/hub_overview` ("Channel
  insights", chips 48 hours / 7 days / 28 days). `scan_analytics` detects the redirect and hands over. Reads 28-day
  views / watch hours / subscribers / top content / recent video, then the "48 hours" chip = realtime views, then
  restores "28 days". 3 screenshots in `evidence/<handle>/insights-*`. The trend arrow fuses onto the number in OCR
  ("4" reads "40"): found by pixel and stripped. A lone bold 0 is invisible: recorded as 0 only when exactly one
  digit-sized glyph is there, and listed in `inferred_zero` / `*_source`.
- **Dashboard (insights flavour)**: "Current subscribers", Summary card, "Go to channel insights". Middle card is
  read by its labels, not fixed y. Output has `variant: insights|classic`. Some small values (CTR 0%, a 4 beside a dash)
  stay None.

## Gotcha: negative scroll
`screen_control.ps1 wscroll ... -5` via `-File` fails (PowerShell reads `-5` as a parameter name); `sc()` now
routes negative numbers through `-Command` with quoting. Before 2026-11-02 every scroll-up / "park the mouse"
call failed silently. Always scroll to top with `-30` and check the page actually moved.

## More lessons (2026-11-02)
- **Analytics layout (b)**: classic page with Ask Studio chips and a static Realtime column (no carousel). The
  Realtime numbers are lone bold digits: `realtime_fill` reads them by zoomed crop OCR, else one digit-sized glyph =
  0 (listed in `inferred_zero`). Only a number ABOVE the label line counts: the crop also holds "Last 48 hours", whose
  "48" once got recorded as the value.
- **Dashboard Summary "Views" digit** is a small lone digit Windows OCR cannot see at any zoom (Tina, Roy, RvVf).
  If the glyph is there (`views_glyph_present`) the channel stays ok and `views_28d` is filled from the Analytics
  headline sentence, labelled `views_source: analytics headline ...` (needs `--analytics`, else stays None).
- Switcher checkmark pixel x-range is 800-848. `sc()` kills a stuck `screen_control.ps1` after 90s, retries once,
  then raises StepFail (a `wkey` stall used to hang a pass for hours).
- **Desktop lock**: with the RDP session disconnected/locked there is no foreground window and every input call hangs
  (`Ensure-Foreground` waits up to 6 min). Check `focus <hwnd>` returns in ~1s before a run; pass 6 timed out for this.
- **Memory**: a disconnected second Windows session (Chrome) held ~8 GB and the harness killed a run for low RAM. Log
  that session off (not just disconnect), keep >5 GB free.
- One intermittent failure seen once: identity mismatch (panel check stayed on the previous channel) on 3 attempts
  in a row, then passed on every rerun. Cause unknown. Rerun the channel with `--only`.
- Known gap: `list` mode shows a raw traceback on StepFail.

## Status (2026-11-02)
Proven live: full 10-channel pass on manager sfdtgrfregrtvcbgfhg@gmail.com with --content --analytics --dashboard:
10 ok / 0 failed (pass 8, `results/channel-stats-20261102-195404.json`), all three content tabs complete on every
channel, classic and Insights layouts both read, and the same numbers matched pass 7 where both read them.
Also proven: profile verify, wrong-manager refusal, channel lists, identity checks, section checks, fault recovery.
NOT yet proven: manager fgnf70093@gmail.com full pass, Draft / Unlisted / Private rows, >30 videos (reports
incomplete), comments/likes (not OCR-readable), scheduled times (not shown in list), permissions check, ECM profile.
