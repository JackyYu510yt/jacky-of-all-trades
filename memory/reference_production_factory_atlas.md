---
name: reference-production-factory-atlas
description: "Jacky's Production Factory is the documentation atlas (read it before describing how a lane works); code is edited in the live folders, never there"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9438c703-ffb0-43e7-907e-36d70f4b7724
  modified: 2026-08-26T23:56:26.519Z
---

`C:\Users\Shadow\Desktop\Compiled Binaries\Jacky's Production Factory\` is the **atlas**, not the
running system. Read it BEFORE describing how any lane is architected — the user's mental model is
documented there and in `Tinkering\stagger-dashboard\IMAGE-LANE-TRUTH.md`.

Working rule (user decision 2026-08-22, "Option B"): **code is edited in the LIVE folders**
(`Testing\Jacky Rush`, `Testing\Account Setup`, `Tinkering\stagger-dashboard`) — never in the Factory.
The Factory holds tool/function maps, `MANIFEST.md` (per-file provenance + sha1), `05-FIX-BACKLOG.md`,
test plans, results. It is a SNAPSHOT and drifts: on 2026-08-26, 6 of 11 image-lane files differed
from live (`gemini_worker.py` 14 KB behind, `cohort_keeper.py` 43 KB / 6 days behind).

**So: audit and trace against the LIVE tree; read the Factory for the architecture and the why.**

Key architecture fact I got wrong once (2026-08-26) — the image lane is **one account fleet with two
paths**, not two pools: the same `aistudio_account_*` profiles reached through the AI Studio website
(~25 img/acct) and through the Gemini HTTP endpoint (~140-250 img/acct, a **separate** budget).
Sources: `image_supply_driver.py:64-67`, `IMAGE-LANE-TRUTH.md:138-139`.

Related: [[project-image-lane-connection-audit]]
