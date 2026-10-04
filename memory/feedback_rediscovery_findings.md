---
name: feedback_rediscovery_findings
description: "When a skill investigation reveals existing infrastructure already solves what looked like a new build, write that as a finding immediately, unprompted — don't wait to be asked"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9c9bcce0-9ce8-4782-9088-c45372010dd7
  modified: 2026-09-17T17:34:58.354Z
---

A "rediscovery" — investigating a problem and finding the fix already exists
somewhere in the codebase, just not reachable/wired/enabled — is itself a
keeper-test finding (per [[feedback_evidence_first_error_recon]] and the
global CLAUDE.md "Findings get written down" rule) and must be noted the
moment it's found, not only when the user happens to ask.

**Why:** 2026-09-17, Jacky Production Factory session — investigating a
"rent cheap, remember bad hosts" gate for community-tier vast.ai rigs found
the entire mechanism (boot-preflight self-destruct, host_memory.py 2-strike
auto-block, unaffected price/speed ranking) already built and live; the only
gap was `config.json`'s `allowed_hosting_types` excluding community hosts
before they ever reached the existing net. That "it already exists" fact is
exactly the kind of thing expensive to re-derive and cheap to write down —
confirmed by the user explicitly: "for any 'rediscoveries' like this... add
to findings so we don't have to stumble across it again."

**How to apply:** Any time investigation (mine, or a skill I'm running —
/auto, /repair, /deep-audit, /error-recon) turns up "X already does this, it
was just never wired/enabled/reachable" — or the inverse, "I assumed X
needed building but it's redundant with Y" — write it as a finding via
`note.py` immediately, unprompted, same as any other keeper-test finding.
Do this by default going forward, not just when the user flags a specific
instance. This generalizes the existing global CLAUDE.md capture rule; it
does not replace it — the keeper test ("would a future run act on this
differently for having read it") still applies, so routine "yep it worked as
expected" checks still don't qualify.
