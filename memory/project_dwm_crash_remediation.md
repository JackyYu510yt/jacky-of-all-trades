---
name: DWM crash + farming-bot memory-leak remediation
description: Windows Server 2022 box crashed DWM via commit-limit exhaustion from leaking farming bots; pagefile tuned and nightly restart cron installed as mitigation
type: project
originSessionId: fc16d26e-2fd6-4e5d-96c3-ad364b6d7d7a
---
On 2026-04-21 ~3:27 AM, `dwm.exe` crashed with `STATUS_COMMITMENT_LIMIT` (0xC00001AD) and Windows logged the user off. Root cause: two farming bots leaked memory over ~10 hours until two `node.exe` children (PIDs 23560 + 10656) held ~94 GB + ~88 GB virtual memory, eating the full 183 GB commit limit. DWM's next allocation failed.

**Machine:** Windows Server 2022, 64 GB RAM, WIN-1UEA9ID9M74 (user: Shadow).

**Leaky bots** (auto-start from user's Startup folder):
- `C:\Users\Shadow\Desktop\Compiled Binaries\Video Printer Pipeline V1\startup_mats_farmer.bat` — launches `py -3.11 mats_farmer.py`
- `C:\Users\Shadow\Desktop\Testing\VeoUnlimited\startup_veounlimited.bat` — launches `v3.8\VeoUnlimitedPro.exe`

The node.exe processes are children spawned by these (likely Playwright/Puppeteer under the Python or the exe). Leak root cause not yet fixed — mitigated only.

**Remediation applied:**
- Pagefile: auto-manage disabled, set 32 GB init / 256 GB max → commit limit ~320 GB (needs reboot to shrink from 119 GB)
- Scheduled task `Nightly Bot Restart` at 4:00 AM daily (runs as user Shadow, highest privileges) → kills + relaunches bots before leak can exhaust commit
- Helper script: `C:\Users\Shadow\AppData\Local\bot_restart.ps1`; logs at `C:\Users\Shadow\AppData\Local\BotRestartLogs\`

**Why:** user runs long-overnight automation; real leak fix requires source access to the bots. Nightly restart is the KISS mitigation.

**How to apply:** if the user reports another DWM crash, slowness, or "low virtual memory" warnings, first check (a) is the nightly restart task still enabled and running, (b) did the bots grow past 90 GB anyway. If both fail, the leak accelerated — time to fix at source, not just restart more often. Possible tactic: add `--max-old-space-size=4096` to any node invocation inside the bats so each node process self-terminates at 4 GB heap.
