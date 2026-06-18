---
name: reference-web-capture-skill
description: The /web-capture skill — proxy-free headed-Selenium page capture + detection signatures; selenium-wire is broken on this box
metadata: 
  node_type: memory
  type: reference
  originSessionId: 20e1c9d9-f898-4280-b90d-caa0c927b438
---

The `/web-capture` skill (at `~/.claude/skills/web-capture/`) is the go-to for any
web scraping / browser automation / page-error-diagnosis task. It bundles a
proven engine `page_diag.py` + a Python 3.11 venv (`selenium==4.15.2` only).

What it does: opens a URL in **headed** Chrome on a chosen profile, captures a
7-file forensic bundle per page (outerHTML, innerText, meta=url/title/handles,
console.json, network.har with status+headers, xhr.json, screenshot), clicks a
target, handles new tabs (handle-set diff), then builds a 3-factor **detection
signature** (URL + error text + stable DOM marker) and a **state classifier**.

**Hard-won gotcha — do NOT use selenium-wire for network capture on this box.**
Proven broken: its bundled mitmproxy calls `X509.get_extension` (removed in
modern pyOpenSSL) → every HTTPS load fails `net::ERR_CONNECTION_CLOSED`, HAR
empty. The maintained `selenium-wire-lw` fork needs Python ≥3.12 (box is 3.11).
**Use Chrome DevTools logs instead** (no proxy): set
`goog:loggingPrefs={'performance':'ALL','browser':'ALL'}` +
`perfLoggingPrefs={'enableNetwork':True}`, then `get_log('performance')` for
network (assemble HAR from `Network.*` events) and `get_log('browser')` for
console. Trade-off: no HTTPS response bodies (metadata only) — fine for v1.

Design plan + AUDITOR review + findings:
`C:\Users\Shadow\Desktop\Compiled Binaries\Skills\prep-page-diagnostic.txt`.
Built via [[feedback_probe_dont_assume]] (two live smoke tests settled the
arch) and [[feedback_evidence_first_error_recon]].
