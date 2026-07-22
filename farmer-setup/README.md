# Farmer (Orchestrator) one-shot rebuild

Turn a freshly reinstalled Wholesale Internet box back into THE farmer with one
command. The farmer is the heart of the render farm: it generates all the work,
holds the master template, keeps the mesh's fixed address, and is the only
machine that has the render PCs' identity keys.

## On a freshly reinstalled box (the whole ritual)

Open PowerShell and run:

```powershell
irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/farmer-setup/setup.ps1 | iex
```

It asks ONE question - the payload password - then does everything: Windows
Update kill, Python + packages, Syncthing with the farmer's permanent identity
AND the live mesh config, the orchestrator scripts, the master template, the
pc1/pc2/pc3 identity bundles, every scheduled task and autostart entry, the
desktop tools, Claude Code, Chrome Remote Desktop.

Safe to re-run - finished steps are skipped, existing folders are left alone.

## Files

| File | What |
|---|---|
| `setup.ps1` | The one-shot rebuild script a fresh box downloads and runs |
| `pack_payload.ps1` | Run on the live farmer to (re)build `payload.enc` |
| `payload.enc` | Everything irreplaceable, AES-256 locked. Safe to host publicly. Hosted as a GitHub release asset, tag `farmer-setup-v1` (same arrangement as `render-setup-v1`). |

Password handling is identical to render-setup: you type it when packing and
type it again when rebuilding. It is never stored anywhere.

## What's inside payload.enc

| Payload folder | Restored to | Why it's irreplaceable |
|---|---|---|
| `syncthing-identity\` | `%LOCALAPPDATA%\Syncthing` | The farmer's cert.pem + key.pem (device ID `XFLEVVM...`) **and the live config.xml** - the mesh's real folder/device list, which is AHEAD of what any README records (extra devices like the `jacky` home PC and dead-but-registered old boxes, plus the Claude Output / Mats Output / Transfer folders) |
| `render-pc-identities\` | `Desktop\render-pc-identities` | pc1/pc2/pc3 cert+key pairs - they exist ONLY on the farmer; lose them and no render PC can ever be rebuilt with its old identity |
| `Jacky Rush Render PC Template\` | `Desktop\Testing\Jacky Rush Render PC Template` | The MASTER template that `render-setup/pack_payload.ps1` reads |
| `Jacky Rush\` | `Desktop\Testing\Jacky Rush` | The orchestrator itself - farmer + stage 0-6 pipeline + workers + secrets (cookies.txt, proxies.txt, quota state). Logs, outputs, scratch and `_*` test dirs are deliberately NOT packed (9 GB of junk) |
| `Vercel\` | `Desktop\Testing\Vercel` | Render snapshot scanner (feeds the yt-dashboard via Supabase; creds come from the template's `_render_push_config.json`) |
| `jarvis\` | `Tinkering\jarvis` | Claude notes/strips overlay scripts |
| `stagger-dashboard\` | `Tinkering\stagger-dashboard` | Daily-quota rotator dashboard. Its git repo has **no remote** - this payload is the ONLY off-machine copy (.git history + .env.local included; node_modules and the 11 GB of test artifacts skipped) |
| `misc\` | various | Transcript-service Startup trio, `bot_restart.ps1`, stagger `supervisor.ps1`, `WinVDitto.exe`, ClipAngel |

## Hard rules baked into setup.ps1 (do not "fix")

- Identity keys + config.xml are planted BEFORE Syncthing ever starts; the
  script hard-stops if the computed device ID is not `XFLEVVM...`.
- Only `cert.pem` + `key.pem` + `config.xml` are restored - **never an
  index/database**. A fresh index can only pull; an old index next to empty
  folders broadcasts deletions mesh-wide (versioning is off - deletions are
  permanent).
- The static IP is verified but never changed by the script - reconfiguring a
  NIC over a remote session cuts you off. If it's wrong, the script prints the
  exact commands to run by hand.
- Folder paths get their `.stfolder` markers created before first start so the
  restored config.xml is accepted immediately.

## Machine facts (from the 2026-07 audit of the live farmer)

- **Identity**: `XFLEVVM-KVCRGNJ-L2K6ARD-LZHPH45-GZZZC4B-AVPCU5E-H6QGOGS-OQMJMQ7`,
  hostname WIN-1UEA9ID9M74.
- **Network**: static 173.208.165.122/29, gateway 173.208.165.121,
  DNS 192.187.107.16 + 69.30.209.16. The render PCs dial
  `tcp://173.208.165.122:22000` - this address must survive any rebuild.
- **Storage**: ONE 954 GB C: drive. `Desktop\Compiled Binaries\Shared Folder`
  is a REAL folder here - no HDD junction (unlike the render PCs and uploader).
- **OS**: Windows Server 2022 - no winget; setup.ps1 direct-downloads everything.
- **Syncthing folders** (live config, restored automatically): `sjetj-h9jpa`
  ! Jacky Rush Output, `xkrz4-rfveh` ! Thumbnails, `mxnjo-onfa4` Claude Output,
  `sgn6l-t4kpe` ! Mats Output, `prlxm-l5amr` Transfer.
- **Scheduled tasks**: RenderSnapshotScanner + CMDUnhideDaemon (enabled, at
  logon), Nightly Bot Restart + StaggerHelperSupervisor (recreated DISABLED -
  re-enable the stagger one after restoring the stagger-dashboard project;
  its state on the live box flips with stagger work).
- **Syncthing autostart**: the live box uses the official installer's "Start
  Syncthing at logon" task; a rebuild gets an HKCU Run key instead (same
  mechanism as the render PCs/uploader). setup.ps1 detects the task and never
  wires both.
- **Username**: the restored config.xml pins folder paths under
  `C:\Users\Shadow\...` - rebuild with the SAME username or fix the paths in
  the Syncthing GUI afterwards.
- **The farmer pipeline itself is started BY HAND** (`launch
  jacky_rush_farmer.bat` in the Jacky Rush folder) - it has no autostart on the
  live box, so the rebuild doesn't add one either.

## Updating the payload

1. Change whatever needs changing on the live farmer (scripts, template, config).
2. Run `farmer-setup/pack_payload.ps1`, type the same password.
3. Re-upload `payload.enc` to the GitHub release:
   ```powershell
   gh release upload farmer-setup-v1 payload.enc --clobber -R JackyYu510yt/jacky-of-all-trades
   ```

Re-pack after any mesh change (new device, new folder) - config.xml in the
payload is the only complete record of the mesh.

## After a rebuild - the by-hand checklist

Everything installable is installed by setup.ps1 (including chrome-for-testing
and stagger-dashboard's `npm install`). What's left is exactly the things a
script can't do - logins:

1. `gh auth login` (GitHub), `claude login` (Claude Code).
2. Chrome Remote Desktop - the script offers the one-paste link flow; if
   skipped, do it via https://remotedesktop.google.com/headless.
3. Log the gemini/aistudio/flow worker accounts back in (chrome-for-testing /
   Chrome). All browser profiles are gone after a rebuild - this is the real
   time cost of a wipe.
4. Re-enable the StaggerHelperSupervisor task if wanted.
5. Start the farmer when ready: `launch jacky_rush_farmer.bat`.

(AdsPower and Proxifier autostart on the old box but are believed unused -
they are deliberately NOT part of the rebuild. Install by hand if ever missed.)
