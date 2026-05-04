# Memory Index

- [User work context](user_work_context.md) — Python + ffmpeg video rendering pipelines, long jobs, large files
- [KISS-first optimization](feedback_kiss_optimization.md) — smallest change biggest dial, tradeoffs named, no overengineering
- [Retries are optimization](feedback_retries_are_optimization.md) — bounded retries + checkpointing matter for long-running jobs
- [Plain-language explanations](feedback_plain_language.md) — short sentences, everyday analogies, define jargon on first use
- [Explanation level — curious adult](feedback_explanation_level.md) — default register is L1b: simple, direct, adult-grade analogy, no walls of text
- [Codex audit loop for plans](feedback_codex_audit_loop.md) — non-trivial plans route through Codex before execution, expect multi-turn integration
- [Mandatory Shell+Cron+Monitor tri-pattern](feedback_mandatory_shell_cron_monitor.md) — preload Monitor + Cron alongside Shell for /auto, /repair, /prep; never shell-only
- [No mid-reasoning pivots](feedback_no_mid_reasoning_pivots.md) — never print hypotheses that later get overturned; user acts on first reading
- [Spacing for readability](feedback_spacing_for_readability.md) — double line breaks between list items; user has visual difficulty with dense text
- [ADHD + visual difficulty](user_adhd_and_visual.md) — scans first, uses strong visual anchors (====), bold headlines, consistent chunk structure
- [Rainbow top separator](feedback_rainbow_top_separator.md) — every response begins with 🟥🟧🟨🟩🟦🟪 row so user can find where answers start
- [DWM crash + bot-leak remediation](project_dwm_crash_remediation.md) — 4/21/26 DWM crash from commit exhaustion; pagefile retuned + nightly bot restart cron installed
- [Pick-from-options as default](feedback_pick_from_options.md) — show 3-4 labeled variants and let user pick; don't ask abstractly
- [Headline-then-detail structure](feedback_headline_then_detail.md) — every block leads with a bold headline that carries the whole point
- ["Push to git" implies setup permission](feedback_push_to_git_implies_setup.md) — "push to git" includes setting local user.email/user.name; don't gate on a separate ask
- [Autonomous engine, optional startup gate](feedback_startup_gate_autonomous_engine.md) — engine runs blind, no input() mid-pipeline; startup gate is optional (some scripts auto-detect from inputs)
- [Structural fix vs patch](feedback_structural_fix_vs_patch.md) — DONE only if next run, different input, no Claude in loop, doesn't hit same failure
