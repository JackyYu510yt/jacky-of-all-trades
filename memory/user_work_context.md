---
name: user_work_context
description: User's primary scripting domain — Python + ffmpeg video rendering pipelines, long-running jobs with large intermediate files
type: user
originSessionId: e603725b-6687-40da-af59-af62bed45597
---
User primarily writes Python scripts, often with ffmpeg subprocess calls, for video rendering pipelines. Typical traits of their work:

- Long-running renders (minutes to hours per job)
- Large intermediate and output files (GBs to 100+ GB)
- Batch processing of many clips
- Storage efficiency matters — disk is a real constraint
- Machine specs matter when optimizing (CPU cores, GPU presence for NVENC, free RAM, free disk)

Beyond video work, they also write general-purpose scripts where the same optimization principles apply.

How to apply: when discussing performance, parallelism, or disk usage in their scripts, default to reasoning about the whole pipeline (not a single function), weigh speed-vs-storage tradeoffs explicitly, and check whether recommendations fit the actual machine rather than offering generic advice.
