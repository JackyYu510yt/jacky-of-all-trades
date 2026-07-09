---
name: reference-ffmpeg-on-path
description: Canonical ffmpeg/ffprobe location now on persistent user PATH (C:\ffmpeg\bin)
metadata: 
  node_type: memory
  type: reference
  originSessionId: 38d36faf-480e-465e-aba9-84f8a457b900
---

A canonical ffmpeg 6.1.2 shared build (ffmpeg.exe + ffprobe.exe + DLLs) lives at `C:\ffmpeg\bin` and is on the **persistent user PATH** (added 2026-06-29). Before this, ffmpeg existed only bundled inside project folders (LosslessCut, ShareX, various `ffmpeg6\bin`) and was NOT on PATH — tools that shelled out to `ffmpeg`/`ffprobe` by name failed. Now they resolve. `winget` is NOT available on this box. Relates to [[user_work_context]] and [[reference_web_capture_skill]].
