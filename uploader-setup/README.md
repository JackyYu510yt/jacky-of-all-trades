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

## On a blank uploader PC

Open PowerShell and run:

```powershell
irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/uploader-setup/setup.ps1 | iex
```

No questions asked. It does: Syncthing install (direct GitHub download - Server
editions have no winget), identity generation, RAW-disk initialization + the
`Shared Folder -> <HDD>:\Shared Folder` junction (same trick as the render
PCs), receive-only folder config trusting all three render PCs, autostart.

Safe to re-run - finished steps are skipped, an existing identity is never
regenerated.

### After a REBUILD (fresh identity)

Unlike the render PCs, the uploader's identity is not sealed in a payload - a
rebuild means a new device ID, and the render PCs must be told. The setup
script prints the exact command; it boils down to running this on each render
PC:

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
