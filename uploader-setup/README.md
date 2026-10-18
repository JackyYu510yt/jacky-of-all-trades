# Uploader PC one-shot setup

Turn a blank Windows box into the fleet's upload station with one command.

The uploader is the end of the pipeline: finished videos flow from the render
PCs into this machine, get uploaded, then deleted - and the delete flows BACK
to the render PC that made the video, wiping its copy too.

## The origin-tagged sync (how it works)

```
PC1 ──┐
PC2 ──┼── jr-rendered, send & receive ──> Uploader (send & receive)
PC3 ──┘   (each PC .stignore-filtered      Desktop\Compiled Binaries\Shared Folder\! Jacky Rush Rendered
           to its own "* - PCx.mp4")

Farmer <── xkrz4-rfveh ──> Uploader (send & receive, two-way)
                           Desktop\Compiled Binaries\Shared Folder\! Thumbnails
```

- Each render PC shares its local `! Jacky Rush Rendered` folder (where the
  watcher drops finished videos) with the uploader, Syncthing folder ID
  `jr-rendered`, **send & receive**.
- The watcher tags every final filename with its origin (`Title - PC2.mp4`),
  and each render PC carries a `.stignore` that syncs ONLY its own tag:
  ```
  !(?i)**/* - PC2.mp4
  *
  ```
  So: deleting an uploaded video on the uploader deletes it on the origin
  render PC (post-upload cleanup, fleet-wide) - but render PCs never download
  each other's videos, because everyone else's tags are on their ignore list.
- **NEVER delete the `.stignore` file on a render PC.** It is the ONLY thing
  preventing that PC from downloading every other PC's videos. If it goes
  missing, re-run `render-setup/share-rendered-to-uploader.ps1` to restore it.
- The render PCs do NOT share this folder with each other or the farmer - only
  with the uploader.
- The farmer shares `! Thumbnails` (folder ID `xkrz4-rfveh`, the same one the
  render PCs get) directly with the uploader, **send & receive** on purpose:
  deleting a thumbnail anywhere deletes it everywhere (farmer + render PCs +
  uploader). That's the intended cleanup flow - delete after upload and the
  whole fleet forgets it. Versioning is off mesh-wide, so those deletes are
  permanent; upload FIRST, delete second.

## Moving the uploader to a new box (same identity, picks up where it left off)

The uploader's identity IS sealed in a payload now (`payload.enc` on the
`uploader-setup-v1` release, same AES-256 lock as the render payload). A new
box that unlocks it comes back as `MSZZ6T4` - every render PC, vast rig and
the farmer reconnect with zero changes on their side.

| Where | What |
|---|---|
| `pack_uploader_payload.ps1` | Run on the LIVE uploader. Seals Syncthing identity + full config.xml (whole device roster incl. the vast pool) + the Syncthing binary, `C:\Tools` (reaper + its config), the checksum guard, the 3 scheduled tasks, pip freeze, user PATH, Run keys, small app settings. `-Upload` publishes it. **Re-run whenever the uploader's setup changes.** |
| `migrate-source.ps1 -Prepare` | Old box. Opens SMB (445) to the Tailscale range on the Tailscale adapter only, so the new box can copy from it. |
| `setup.ps1` | New box, elevated. Payload password -> installs Python 3.11.9 + exact pip set, Chrome, Firefox, Tailscale, VS Code, WinRAR 7.23, Process Hacker 2.39; logs into Tailscale; junctions storage; copies from the old box; restores identity, tools, tasks; attaches WSL. |
| `migrate-source.ps1 -Cutover` | Old box, when setup.ps1 asks. Stops + disables Syncthing, the reaper and the checksum guard, closes Chrome/AdsPower/WSL, drops an `INERT.txt` marker that setup.ps1 waits for. |
| `migrate-source.ps1 -Undo` | Rollback - only before the new box has started Syncthing. |

Copy is two passes over Tailscale: pass 1 (old box still uploading) moves the
videos + Desktop/Downloads/Documents/`C:\ffmpeg`; pass 2 (after cutover)
mirrors the videos exactly and takes the in-use data: Chrome `User Data`,
AdsPower (program, `adspower_global`, `C:\` + `D:\.ADSPOWER_GLOBAL`),
ClipAngel history, the WSL Ubuntu disk.

**The videos must be copied, not re-synced** - ones delivered by vast rigs
that no longer exist live only on the uploader.

**Never let two boxes run Syncthing with the same identity.** That is what
`-Cutover` is for; setup.ps1 will not take the identity over until the old box
reports INERT (or you confirm it is permanently off).

What cannot come across (machine-bound encryption): Chrome site logins
(profiles, bookmarks, extensions do come - sign in again) and AdsPower's
login (log in; profiles + cookies return from AdsPower's cloud). Not copied
on purpose: the provider's `C:\ip.bat` first-boot script, the Recycle Bin,
`D:\ck6yil9f8vb3iopl`.

```powershell
# OLD box (elevated)
$m = 'https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/uploader-setup/migrate-source.ps1'
& ([scriptblock]::Create((irm $m))) -Prepare
# NEW box (elevated) - follow its prompts; it tells you when to run -Cutover on the old box
irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/uploader-setup/setup.ps1 | iex
```

If WSL had to be installed, setup asks for a reboot - re-run it after; done
steps are skipped.

## On a blank uploader PC (fresh identity)

Open an elevated PowerShell, run the same `setup.ps1` line, and press Enter
at the password prompt. It does: Syncthing install (direct GitHub download -
Server editions have no winget), identity generation, RAW-disk
initialization + the `Shared Folder -> <HDD>:\Shared Folder` junction (same
trick as the render PCs), send-receive folder config trusting the render PCs
and the farmer, autostart. Run `trust-render-pcs.ps1` afterwards for the vast
pool.

Safe to re-run - finished steps are skipped, an existing identity is never
regenerated.

### After a REBUILD with a fresh identity

A fresh identity means a new device ID, and the render PCs must be told. The
setup script prints the exact command; it boils down to running this on each
render PC:

```powershell
$u = 'https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/render-setup/share-rendered-to-uploader.ps1'
& ([scriptblock]::Create((irm $u))) -UploaderId 'THE-NEW-DEVICE-ID'
```

The FARMER must also be told (it feeds the thumbnails folder). On the farmer:

```powershell
$exe = "$env:LOCALAPPDATA\Programs\Syncthing\syncthing.exe"
& $exe cli config devices add --device-id 'THE-NEW-DEVICE-ID' --name 'Uploader'
& $exe cli config folders xkrz4-rfveh devices add --device-id 'THE-NEW-DEVICE-ID'
```

## Adding a NEW render PC to the pipeline

1. On the render PC:
   `irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/render-setup/share-rendered-to-uploader.ps1 | iex`
   (it prints the render PC's device ID at the end)
2. On the uploader, trust that ID and attach it to the folder:
   ```powershell
   $exe = "$env:LOCALAPPDATA\Programs\Syncthing\syncthing.exe"
   & $exe cli config devices add --device-id 'THE-RENDER-PC-ID' --name 'Render PCx'
   & $exe cli config folders jr-rendered devices add --device-id 'THE-RENDER-PC-ID'
   ```
3. Also add the new ID to the `$RenderPCs` list at the top of
   `uploader-setup/setup.ps1` so future rebuilds include it.

## Rules of the road (upload workflow)

- **Deleting a video here deletes it on the origin render PC too** - that's
  the intended post-upload cleanup: delete once, the whole fleet forgets it.
- **Upload FIRST, delete second.** Versioning is off mesh-wide - a delete is
  permanent everywhere. Deleting a video you haven't uploaded yet kills the
  only copies in existence.
- **Deletes on a render PC also propagate here.** Same rule, other direction.
- Bulk data lives on the HDD via the junction; keep an eye on free space with
  big batches anyway.

## Mesh facts (uploader side)

| Machine | Device ID starts | Role |
|---|---|---|
| Uploader | `MSZZ6T4` | send-receive `jr-rendered` + send-receive `xkrz4-rfveh` |
| PC1 | `VYEHZ24` | send-receive `jr-rendered`, .stignore-filtered to `* - PC1.mp4` |
| PC2 | `NSBTRAN` | send-receive `jr-rendered`, .stignore-filtered to `* - PC2.mp4` |
| PC3 | `ZGSLY26` | send-receive `jr-rendered`, .stignore-filtered to `* - PC3.mp4` |
| Farmer | `XFLEVVM` | feeds `xkrz4-rfveh` (Thumbnails) |

The uploader does NOT participate in the farmer's `sjetj-h9jpa` (Output)
folder - it only ever sees finished videos and thumbnails.
