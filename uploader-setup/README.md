# Uploader PC one-shot setup

Turn a blank Windows box into the fleet's upload station with one command.

The uploader is the end of the pipeline: finished videos flow **one way** from
the render PCs into this machine, where they get uploaded and deleted.

## The one-way sync (how it works)

```
PC1 ──┐
PC2 ──┼── send-only ──>  Uploader (receive-only)
PC3 ──┘                  Desktop\Compiled Binaries\Shared Folder\! Jacky Rush Rendered
```

- Each render PC shares its local `! Jacky Rush Rendered` folder (where the
  watcher drops finished videos) as **send-only**, Syncthing folder ID
  `jr-rendered`.
- The uploader holds the same folder ID as **receive-only**. Send-only +
  receive-only = strictly one-way; nothing on the uploader ever flows back.
- The render PCs do NOT share this folder with each other or the farmer - only
  with the uploader. (Their GUIs may show the folder as "out of sync" because
  they see each other's files via the uploader but never pull them. Cosmetic;
  ignore.)

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

- **Deleting an uploaded video on the uploader is safe** - receive-only keeps
  local deletes local; the file will NOT come back on its own.
- **Never click "Revert Local Changes"** in the uploader's Syncthing GUI
  (127.0.0.1:8384) - that re-downloads everything you deleted after uploading.
- **Deletes on a render PC DO propagate here.** If a render PC cleans up its
  Rendered folder before the uploader has uploaded the file, the file is gone
  on both ends (versioning is off mesh-wide - deletions are permanent).
  Upload first, clean up second.
- Bulk data lives on the HDD via the junction; keep an eye on free space with
  big batches anyway.

## Mesh facts (uploader side)

| Machine | Device ID starts | Role |
|---|---|---|
| Uploader | `MSZZ6T4` | receive-only `jr-rendered` |
| PC1 | `VYEHZ24` | send-only `jr-rendered` |
| PC2 | `NSBTRAN` | send-only `jr-rendered` |
| PC3 | `ZGSLY26` | send-only `jr-rendered` |

The uploader does NOT participate in the farmer's `sjetj-h9jpa` (Output) or
`xkrz4-rfveh` (Thumbnails) folders - it only ever sees finished videos.
