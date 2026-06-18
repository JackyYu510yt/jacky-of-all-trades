---
name: web-capture
description: >-
  Headed-Selenium web automation + page-state forensics. Use whenever the user
  wants to scrape a page, automate a browser flow, debug why a page shows an
  error, or capture evidence from a live site. Captures a full forensic bundle
  per page — live DOM/outerHTML, visible innerText, final URL + title + window
  handles, JavaScript console log, network log as HAR with status codes +
  headers, and a screenshot — then clicks a target, handles a new tab, captures
  the same bundle on the result, and builds a 3-factor DETECTION SIGNATURE
  (URL + error text + stable DOM marker) plus a STATE CLASSIFIER that names which
  state a page is in. Triggers: "scrape this page", "automate this site",
  "dump the DOM / page source / outerHTML", "grab the rendered text",
  "capture the console logs", "capture the network / HAR / XHR", "get the
  status codes / headers", "click X then capture", "handle the new tab",
  "why is this page erroring", "build a detection signature / fingerprint for
  this error state", "classify what state the page is in". NETWORK + CONSOLE are
  captured WITHOUT a proxy (Chrome DevTools logs) — do not reach for
  selenium-wire (proven broken here).
---

# web-capture

Open any URL in a **headed** Chrome on a chosen profile, capture a complete
forensic bundle before and after an interaction, and fingerprint the resulting
state. Network and console come straight from **Chrome's own DevTools logs** —
no proxy, no selenium-wire, no fragile certificates.

A **proven, tested engine** ships with this skill: `page_diag.py`. Prefer driving
it. Only hand-write Selenium when the task needs something the engine doesn't
cover (multi-step flows), and even then follow the patterns below.

---

## The one-sentence job this skill answers

> "Open `<url>` in a headed Selenium session on profile X, screenshot each step,
> dump the DOM + innerText + final URL, capture console and network (HAR) logs,
> click `<element>`, handle any new tab, then capture the same artifacts on the
> resulting page and give me a detection signature for that error state."

---

## The artifact bundle (what "capture a page" means)

Every captured page produces these **7 files** in its own folder. This list is
the contract — when the user says "capture the page," produce all of it:

| File | What it is |
|---|---|
| `screenshot.png` | full-window screenshot of the visible page |
| `page.html` | live `document.documentElement.outerHTML` (post-JS DOM, not view-source) |
| `body.txt` | `document.body.innerText` — the visible text only |
| `meta.json` | final URL, page title, **all window handles**, active handle, counts |
| `console.json` | Chrome console log (JS errors/warnings via `get_log('browser')`) |
| `network.har` | HAR 1.2 of every request — assembled from DevTools Network events |
| `xhr.json` | just the XHR/fetch calls, each with status code + response headers |

Plus a `_complete` sentinel written only after all 7 are attempted, and a
`capture_errors` map in `meta.json` — so a single failed artifact (e.g. a
screenshot) never silently sinks the rest.

---

## How to run the bundled engine

The engine is at `~/.claude/skills/web-capture/page_diag.py` with a ready venv at
`~/.claude/skills/web-capture/.venv`. On Windows:

```powershell
$skill = "C:\Users\Shadow\.claude\skills\web-capture"
& "$skill\.venv\Scripts\python.exe" "$skill\page_diag.py" `
    --url "https://example.com" `
    --click "css=a.login" `
    --profile "Default" `
    --error-text "Something went wrong" `
    --yes
```

If the venv is missing (moved machine), recreate it:
`python -m venv "$skill\.venv"; & "$skill\.venv\Scripts\python.exe" -m pip install -r "$skill\requirements.txt"`

### Flags

| Flag | Meaning |
|---|---|
| `--url URL` | page to open (auto-prepends `https://` if no scheme) |
| `--click SPEC` | target: `css=…`, `xpath=…`, `link_text=…`, `partial_link_text=…`, or a bare CSS selector |
| `--profile NAME` | Chrome profile folder (e.g. `Default`, `Profile 1`), `fresh` for a throwaway, or `list` to print profiles and exit |
| `--user-data-dir DIR` | override the Chrome "User Data" parent dir |
| `--copy-profile` | copy the profile to a temp dir so Chrome need not be closed (strips `Singleton*` locks) |
| `--error-text "…"` | the known error phrase to anchor the signature on |
| `--yes` | non-interactive: auto-accept the proposed signature, skip all prompts |

Anything **not** passed is asked at the **startup gate** (the only place the tool
talks to you). After the gate, the engine runs blind to completion.

### Output

One timestamped folder under `./page-diag-runs/<UTC>-<rand>/`:
```
step1-initial/   <7 artifacts> + _complete
step2-after-click/   <7 artifacts> + _complete
  origin-tab/    <7 artifacts>     (only if the click opened a new tab)
signature.json   classification.json   run-summary.json   run.log
```

---

## Detection signature + state classifier (the "error-state" part)

The whole point beyond raw capture: turn a messy page into a **reusable
fingerprint**.

- **Signature** = 3 factors that together identify a state:
  1. `url_pattern` — the result URL with query/hash stripped.
  2. `text_markers` — either the user-supplied `--error-text`, or phrases the
     engine scrapes from a built-in error dictionary ("something went wrong",
     "try again later", "service unavailable", …). **Only markers actually
     present on the page are anchored on** — a supplied phrase that isn't on the
     page drops confidence instead of faking a match.
  3. `dom_marker` — the smallest **stable** selector for the error element.
     Preference order: a non-hashed `id` → `data-testid`/`data-test`/`role`/
     `aria-label`/`name` → a text-anchored XPath. Auto-generated/hashed class
     names (CSS-modules, emotion) are rejected on purpose so the marker survives
     a reload.
- **Classifier** (`score_state`) scores a live or saved page against known
  signatures: URL match (0.34) + text markers present (0.33) + DOM marker present
  (0.33). `is_match` is true at ≥ 0.5. No match → `label: "unknown"`. It works
  both live (during a run) and **offline** against a saved step folder, so a
  signature can be re-verified later.

When the user describes a flaky/error state, the move is: capture it once, build
the signature, then reuse `classify_state` to detect it on later runs.

---

## Best practices this skill enforces (the user's expectations)

These are not optional — they reflect hard-won preferences. Apply them whether
driving the engine or writing fresh Selenium.

1. **Proxy-free network capture.** Use Chrome DevTools performance logs, not
   selenium-wire. Set on `Options`:
   ```python
   opts.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
   opts.add_experimental_option("perfLoggingPrefs", {"enableNetwork": True})
   ```
   Then `driver.get_log("performance")` yields `Network.requestWillBeSent` /
   `responseReceived` / `loadingFinished` events → assemble the HAR + status +
   headers. `driver.get_log("browser")` yields the console.
2. **Explicit waits, never `time.sleep` guesses** for elements. Wait for
   `element_to_be_clickable` before clicking; wait for network to go quiet (poll
   `performance.getEntriesByType('resource').length` until stable) before
   capturing, so AJAX pages don't yield an empty HAR.
3. **New tab = compare handle SETS**, not counts: `set(after) - set(before)`.
   Switch to the new handle; also snapshot the origin tab (errors can render on
   either).
4. **Self-healing & evidence-first.** Atomic writes (temp-then-rename). Per-
   artifact isolation so one miss is logged in `capture_errors`, not swallowed.
   A click timeout is a logged TIMEOUT state with a non-zero exit — never a hang.
   `driver.quit()` is wrapped so it can't mask the real error. Never
   `except: pass`.
5. **Autonomous engine, optional startup gate.** Ask setup questions (profile,
   URL, target, known error text) ONCE up front; after that the engine runs with
   zero human input. CLI flags can pre-fill every prompt for scripted/headless
   use (`--yes`). No `input()` after the browser is up.
6. **KISS.** One click in v1. One reusable `capture_page` for every step. Don't
   add video capture, full-page stitching, or ML similarity unless a concrete
   need shows up.
7. **Probe, don't assume.** Before trusting any capability on a new
   machine/Chrome version, run a tiny smoke (load a page, assert
   `get_log('performance')` returns ≥1 `Network.responseReceived` and
   `get_log('browser')` works). The environment lies; verify.

---

## Why no proxy (read before anyone suggests selenium-wire)

selenium-wire was tested on this box and **fails for HTTPS**: its bundled
mitmproxy calls `X509.get_extension`, which modern pyOpenSSL removed, so every
HTTPS page dies with `net::ERR_CONNECTION_CLOSED` and the HAR comes back empty.
The maintained `selenium-wire-lw` fork needs Python ≥ 3.12 (this box is 3.11).
The DevTools-log approach needs no proxy, no CA, no extra dependency, and was
proven to capture status codes + headers + console with zero errors. The only
thing it gives up is HTTPS response **bodies** — out of scope for v1 (signatures
use innerText + DOM). If bodies are ever needed, fetch them per-request via CDP
`Network.getResponseBody` (v2 escape hatch), still no proxy.

---

## Environment (verified)

- Python 3.11.9, venv at `~/.claude/skills/web-capture/.venv`
- `selenium==4.15.2` (only third-party dep); Selenium Manager auto-fetches
  chromedriver to match installed Chrome (148 at build time)
- Chrome profiles live under
  `%LOCALAPPDATA%\Google\Chrome\User Data`; `--profile list` prints them
- Reuse of a logged-in profile requires Chrome **fully closed** (or
  `--copy-profile`)

---

## Extending past one click

For multi-step flows (login → navigate → act → capture), the engine's functions
are the building blocks — import or mirror them: `make_driver`, `capture_page`,
`wait_and_click`, `handle_new_tab`, `build_signature`, `score_state`. Keep every
new step inside the same best-practices: explicit waits, capture the full bundle
at each state worth recording, handle-set tab detection, atomic writes, and a
detection signature for any state the user wants to detect again later.

## Quick reference: design plan

The full design rationale, per-function audit specs, the independent review, and
the findings log live in
`C:\Users\Shadow\Desktop\Compiled Binaries\Skills\prep-page-diagnostic.txt`.
