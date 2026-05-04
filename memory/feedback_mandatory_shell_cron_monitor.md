---
name: Mandatory Shell+Cron+Monitor tri-pattern for autonomous work
description: For /auto, /repair, /prep, and any long-running or unattended task, preload Monitor and Cron alongside Shell via ToolSearch — never rely on shell alone
type: feedback
originSessionId: 7059bbb0-0e94-46a1-8a68-4dd1dee3dc1c
---
Shell + Cron + Monitor are a mandatory tri-pattern for autonomous work (/auto, /repair, /prep, any long-running or unattended job). At session start for these tasks, preload Monitor and Cron schemas via ToolSearch — do not fall back to shell-only.

**Why:** Shell alone gives one notification on exit. Monitor surfaces failures the moment they appear in logs — catch a 3-minute crash at minute 3, not at minute 15 when the background job finally exits. Cron schedules retries, periodic checkins, and unattended re-runs so long jobs self-heal without human intervention. Together they drastically improve detection latency and autonomy. Relying on shell alone throws away the lead time the other two tools provide. The auto skill defaults to Bash but does NOT preload Monitor or Cron — that gap is the bug this rule fixes.

**How to apply:** At the very start of /auto, /repair, /prep, or any autonomous task, immediately run `ToolSearch` with `select:Monitor,CronCreate,CronList,CronDelete` before launching any shell work. Whenever a long-running shell job is kicked off in the background, arm a Monitor on its log/output with a filter covering BOTH success and failure signatures (silence ≠ success — see Monitor schema's coverage rule). Use CronCreate for scheduled retries, periodic state checks, deferred re-runs, or recurring jobs. Three tools, one workflow — Shell launches, Monitor watches, Cron schedules.
