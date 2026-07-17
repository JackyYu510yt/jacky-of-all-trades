# Render PC one-shot setup

Turn a blank Shadow PC into a working render node with one command.

## On a blank PC (the whole ritual)

Open PowerShell and run:

```powershell
irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/render-setup/setup.ps1 | iex
```

It asks two questions:

1. **Which PC number is this?** (1 / 2 / 3) - picks the identity + watcher name
2. **Password?** - unlocks the identity keys sealed inside the payload

Then it does everything: Windows Update kill, Python + packages, Syncthing with
the PC's permanent identity, folder sync (staged: thumbnails first, then the
work folder), watcher config, autostart entries, watcher launch.

Safe to re-run - finished steps are skipped. Note: an already-installed
template folder is left untouched on re-run; to force-refresh it, delete
`Desktop\Compiled Binaries\Jacky Rush Render PC Template` first.

## Files

| File | What |
|---|---|
| `setup.ps1` | The one-shot installer a blank PC downloads and runs |
| `pack_payload.ps1` | Run on the farmer to (re)build `payload.enc` from the template + keys |
| `payload.enc` | Template + all identity keys, AES-256 locked with the password. Safe to host publicly. |

## Updating the template (new tools, fixed scripts)

1. Edit the MASTER template on the farmer:
   `C:\Users\Shadow\Desktop\Testing\Jacky Rush Render PC Template`
   (this is the copy pack_payload.ps1 reads - the path is set at its top)
2. Run `pack_payload.ps1`, type the same password
3. Re-upload `payload.enc` to the GitHub release (tag `render-setup-v1`)

Future setups now include the change. Already-running PCs: re-run setup or
apply the change by hand.

## Storage layout (two drives)

Shadow PCs: 256 GB SSD (C:) + purchased 1 TB HDD.

- **SSD (C:)** - scripts/tools: the template, Python, Syncthing, configs.
- **HDD** - all video bulk: `! Jacky Rush Output`, `! Thumbnails`,
  `! Jacky Rush Rendered`, physically at `D:\Shared Folder`.
- One junction makes it invisible: `Desktop\Compiled Binaries\Shared Folder`
  -> `D:\Shared Folder`. Every config keeps using the Desktop path.
- No HDD present -> setup warns and falls back to C:.

## Hard rules baked into setup.ps1 (do not "fix")

- Identity keys are planted BEFORE Syncthing ever starts; the script hard-stops
  if the computed device ID does not match the expected one for that PC number.
- Only `cert.pem` + `key.pem` are restored - never an index/database. A fresh
  index can only pull; an old index next to empty folders broadcasts deletions
  (versioning is off mesh-wide - deletions are permanent).
- `mats_output_path` in the watcher config points at `! Jacky Rush Output` on
  purpose (the watcher is a fork that kept the old key name).
- The watcher starts only AFTER the work folder is fully synced.
- Folder IDs `sjetj-h9jpa` / `xkrz4-rfveh` must match character-for-character.

## Mesh facts

| Machine | Device ID starts | Notes |
|---|---|---|
| Farmer (Orchestrator) | `XFLEVVM` | Wholesale Internet box, 173.208.165.122, survives everything |
| PC1 | `VYEHZ24` | Shadow |
| PC2 | `NSBTRAN` | Shadow |
| PC3 | `ZGSLY26` | Shadow |

The farmer + PC2 already trust these identities - a rebuilt PC reconnects with
zero changes on any other machine.
