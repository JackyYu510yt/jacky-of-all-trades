#!/usr/bin/env python3
"""note.py — write a FINDING to disk the moment it lands, from any folder.

    note.py --dir <ABS project root> --file <path to finding text>
    note.py --recent <ABS project root> [--limit N]
    note.py --index [--limit N]
    note.py --retract <id> --dir <ABS project root> --reason "<why>"

Writes <project>/FINDINGS.md plus one line in the GLOBAL index at
~/.claude/FINDINGS.md. Never touches SPEC.md -- that keeps exactly one writer
(spec_tool.py, driven by /auto at terminal verdict). Division of labour:

    SPEC.md ## Change Log   what a RUN learned          (writer: spec_tool.py)
    <project>/FINDINGS.md   what a CONVERSATION learned (writer: this file)
    ~/.claude/FINDINGS.md   the cross-folder index      (writer: this file)

WHY EACH MECHANISM EXISTS -- every one traces to a measurement on this machine,
not to a guess:

  LOCKED WRITES. 6 processes x 150 plain `open(path,"a")` appends lost 184 of
  900 lines (20.4%), silently, exit 0 -- MSVCRT append is seek-then-write, not
  an atomic OS append. With the lock below: 900/900, twice.

  THE LOCK SITS ON A SENTINEL BYTE PAST EOF, NOT ON BYTE 0. msvcrt locks are
  MANDATORY on Windows (probed: a plain read of a byte-0-locked file raises
  PermissionError 13). Locking byte 0 therefore blocks every READER. Writers
  only need to agree on *some* byte, so they agree on one no reader will ever
  touch. Readers are never blocked and need no retry machinery at all.

  BUDGET IN TIME, NOT TRIES. 400 tight retries elapse in 1.01 ms; one locked
  append+fsync holds 9.03 ms; six writers need ~77 ms of patience. A count
  budget gave 1 ms and starved every waiter.

  --file, NOT stdin. A PowerShell pipe prepends a BOM, which lands on the first
  field and makes `change:` parse as a mangled key.

  RECORD FIRST, INDEX SECOND, and `--recent` RECONCILES. If the index write
  fails after the record write, the finding exists but is invisible
  cross-folder; the reader repairs that divergence every time it runs, so the
  gap has a detector rather than waiting for a byte-identical resubmission.
"""
from __future__ import annotations

import datetime
import hashlib
import os
import re
import sys
import time
from pathlib import Path

GLOBAL_INDEX = Path.home() / ".claude" / "FINDINGS.md"
RECORD_NAME = "FINDINGS.md"

# Sidecar index for findings tagged `scope: universal` in their body -- a
# lesson that holds for a project that does not exist yet (names no project
# file). Additive only: it is never a substitute for the record/index above,
# and existing entries are never rewritten to add this tag retroactively --
# see UNIVERSAL_RE and cmd_universal. Auto-rebuild M1, prep-auto-rebuild.txt
# Phase 1.1 Step 1, decided 2026-09-10.
UNIVERSAL_INDEX = Path.home() / ".claude" / "UNIVERSAL_FINDINGS.md"

UNIVERSAL_HEADER = """# UNIVERSAL FINDINGS — travel to every project, regardless of folder

One line per finding whose lesson holds for a project that does not exist
yet (it names no project file). Populated two ways: (1) automatically, when
a finding's body contains a `scope: universal` line, at note-write time;
(2) by hand, for pre-existing findings backfilled once on 2026-09-10 (see
that date's entries below and Skills/FINDINGS.md id 7d123949 for the method).
Never edited by hand after that -- only appended, under the same lock as the
global index.

    python ~/.claude/skills/spec/note.py --universal   <- read THIS file
"""

# A `scope:` field line in a finding body, same shape as `context:` / `why:`.
# Only "universal" is ever written to the sidecar; "local" (or an absent
# field) is the default and needs no entry anywhere.
SCOPE_RE = re.compile(r"^scope:\s*(universal|local)\s*$", re.IGNORECASE | re.MULTILINE)

# The mutex byte. Far past any real EOF, so it is a pure rendezvous point that
# no reader ever touches. Writers agree on it; that is all a mutex needs.
LOCK_BYTE = 1 << 40

# Derived, not chosen by feel: one locked append+fsync was measured at 9.03 ms,
# so six concurrent writers need ~77 ms. 5 s is ~65x that -- a ceiling that only
# a genuinely wedged writer can reach, not an expected wait. (30 s was ~390x and
# could stall a write that is supposed to be instantaneous.)
LOCK_TIMEOUT = 5.0
LOCK_DELAY_START = 0.001
LOCK_DELAY_MAX = 0.05

BANNED_PARTS = {"_archive", "node_modules", ".git", "_smoke", "__pycache__"}

# An entry header, only ever at column 0. A finding BODY containing a line that
# matched this could forge a header -- including a tombstone that hides an
# unrelated real finding. Neutralized on write (see _neutralize) rather than
# refused, so no legitimate finding is ever rejected.
HEADER_RE = re.compile(r"^##\s+(\S+ \S+)\s+id:\s*([0-9a-f]{8})\s*(.*)$")

# Refuse to persist anything key-shaped. FINDINGS.md is git-TRACKED in at least
# one repo here (Jacky Rush: .gitignore is `*` then `!*.md`), and that repo's
# own header says do not push without a secret scan first.
SECRET_RE = re.compile(
    r"(api[_-]?key|secret[_-]?\w*|password|passwd|token|bearer)\s*[:=]\s*\S{8,}"
    r"|\b(sk|xoxb|xoxp|gho|ghp|ghu|ghs|github_pat|npm)[-_][A-Za-z0-9_]{16,}"
    r"|\bAKIA[0-9A-Z]{16}\b"
    r"|\bAIza[0-9A-Za-z_-]{30,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"      # JWT
    r"|\b[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s/@]{6,}@",                          # url creds
    re.IGNORECASE,
)

# Obvious non-secrets that would otherwise trip SECRET_RE. Without this, a
# finding ABOUT credential handling ("the docs show api_key: YOUR_KEY_HERE")
# is refused with no recourse, and the writer's only move is to distort the
# finding until the regex stops firing -- which is worse than the risk.
PLACEHOLDER_RE = re.compile(
    r"your[_-]?\w*|example|placeholder|redacted|dummy|sample|xxx+|\.\.\.|"
    r"<[^>]+>|\bfake\b|\bhunter2\b|changeme|test[_-]?key",
    re.IGNORECASE,
)

MAX_BODY_BYTES = 64 * 1024   # a finding is a lesson, not a log dump

GLOBAL_HEADER = """# FINDINGS — global index (all projects)

One line per finding: when | project | id | summary. The per-project
FINDINGS.md holds the full entry; this file exists so a session working in
folder A can discover what was learned in folder B.

    python ~/.claude/skills/spec/note.py --index            <- read THIS file
    python ~/.claude/skills/spec/note.py --recent <project> <- read one project

APPEND-ONLY, UNDER A LOCK. Never rewrite this file by hand. Measured on this
machine 2026-08-30: six concurrent plain appends lost 20.4% of lines silently.
"""


def _sha8(text: str) -> str:
    return hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()[:8]


def _normalize(text: str) -> str:
    """Collapse whitespace + lowercase so reflow is not a new finding.

    Honest limit: catches reformatting, NOT rewording. The same lesson in
    different words next week gets a second entry. Stated rather than papered
    over -- a fuzzy match would silently EAT distinct findings, which is worse
    than a duplicate you can see.
    """
    return " ".join(text.split()).lower()


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _resolve_dir(raw: str) -> Path:
    """Absolute, real, existing project root -- or refuse loudly.

    A relative --dir resolves against whatever cwd the caller holds, and agent
    threads reset cwd between calls, so it is refused rather than silently
    filing a finding under the wrong project.
    """
    if raw is None:
        raise ValueError("--dir is required")
    p = Path(raw)
    if not p.is_absolute():
        raise ValueError(f"--dir must be ABSOLUTE, got {raw!r}")
    try:
        p = p.resolve(strict=True)
    except (OSError, ValueError) as exc:
        raise ValueError(f"--dir does not exist: {raw!r} ({exc})") from exc
    if not p.is_dir():
        raise ValueError(f"--dir is not a directory: {p}")
    banned = BANNED_PARTS.intersection({part.lower() for part in p.parts})
    if banned:
        raise ValueError(f"refusing to write inside {sorted(banned)[0]!r}: {p}")
    return p


class _Lock:
    """Exclusive writer mutex on a sentinel byte past EOF. Readers unaffected."""

    def __init__(self, path: Path):
        self.path = path
        self.fd = -1

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(str(self.path),
                          os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o644)
        deadline = time.monotonic() + LOCK_TIMEOUT
        delay = LOCK_DELAY_START
        while True:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    os.lseek(self.fd, LOCK_BYTE, os.SEEK_SET)
                    msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.fd, fcntl.LOCK_EX)
                return self
            except OSError:
                # The ONLY class recovered by waiting is contention. Anything
                # that never clears still surfaces loud at the deadline.
                if time.monotonic() >= deadline:
                    os.close(self.fd)
                    raise OSError(
                        f"could not lock {self.path} within {LOCK_TIMEOUT}s "
                        "(another writer is wedged)"
                    ) from None
                time.sleep(delay)
                delay = min(delay * 1.5, LOCK_DELAY_MAX)

    def __exit__(self, *exc):
        try:
            if sys.platform == "win32":
                import msvcrt
                os.lseek(self.fd, LOCK_BYTE, os.SEEK_SET)
                msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)
        return False

    def append(self, text: str) -> None:
        data = text.encode("utf-8")
        os.lseek(self.fd, 0, os.SEEK_END)
        written = os.write(self.fd, data)
        if written != len(data):
            # A short write (disk full after a partial) returns a count instead
            # of raising; unchecked, fsync succeeds and a truncated finding is
            # reported as filed.
            raise OSError(f"short write to {self.path}: {written}/{len(data)} bytes")
        os.fsync(self.fd)

    def rewrite(self, text: str, tag: str = "bak") -> None:
        """Whole-file replace. Safe ONLY because we hold the writer mutex.

        The safety copy is named per-operation: a single fixed `.bak` was
        overwritten by the next retraction, so it protected exactly one step of
        history. Residual, stated: truncate-then-write leaves an empty file if
        the process dies inside that window; the copy is the recovery.
        """
        data = text.encode("utf-8")
        bak = self.path.with_suffix(self.path.suffix + f".{tag}.bak")
        try:
            bak.write_bytes(self.path.read_bytes())
        except OSError:
            pass  # best-effort safety copy; never blocks the retraction
        os.lseek(self.fd, 0, os.SEEK_SET)
        os.truncate(self.fd, 0)
        written = os.write(self.fd, data)
        if written != len(data):
            raise OSError(f"short rewrite of {self.path}: {written}/{len(data)}")
        os.fsync(self.fd)


def _append(path: Path, text: str) -> None:
    with _Lock(path) as lk:
        lk.append(text)


def _guard_secret(text: str, where: str) -> None:
    hit = SECRET_RE.search(text)
    if hit and not PLACEHOLDER_RE.search(hit.group(0)):
        raise ValueError(
            f"refusing to write a credential-shaped string in {where} "
            f"({hit.group(0)[:24]}...). FINDINGS.md is git-tracked in some "
            "projects here. Rewrite it as a placeholder (YOUR_KEY / <redacted>)."
        )


def _neutralize(body: str) -> str:
    """Make it impossible for a finding BODY to parse as an entry header.

    One leading space suffices -- HEADER_RE anchors at column 0 -- and it keeps
    the author's text intact, which refusing the write would not.
    """
    return "\n".join(" " + ln if HEADER_RE.match(ln) else ln
                     for ln in body.splitlines())


def _summary(body: str) -> str:
    """One-line summary for the index row.

    Pipes are stripped: the index is pipe-delimited, and a finding quoting a
    pipe table (which the standing rule invites, for traps) would otherwise
    forge extra fields and let a lookup match an id that was never indexed.
    """
    text = ""
    for line in body.splitlines():
        if line.lower().startswith("change:"):
            text = line[len("change:"):].strip()
            break
    else:
        text = next((l.strip() for l in body.splitlines() if l.strip()), "(no summary)")
    return text.replace("|", "/")[:160] or "(no summary)"


def _read_entries(record: Path) -> list[dict]:
    """Parse <project>/FINDINGS.md, resolving retractions. Newest last.

    A missing file legitimately means "no findings yet" -> []. An UNREADABLE one
    does NOT: the OSError propagates, because reporting a locked or denied
    record as an empty project manufactures an absence-of-data claim out of a
    swallowed exception.
    """
    if not record.is_file():
        return []
    text = record.read_text(encoding="utf-8", errors="replace")
    entries: list[dict] = []
    order: list[dict] = []
    pending_tomb: dict | None = None
    current: dict | None = None
    for lineno, line in enumerate(text.splitlines()):
        head = HEADER_RE.match(line)
        if head:
            ts, eid, tail = head.group(1), head.group(2), head.group(3)
            # Only the tail BEFORE any bracketed mark is directive-bearing. The
            # in-place [RETRACTED …] mark lives in the same line, so scanning the
            # whole tail let mark text be read as a `retracts:` directive.
            retracts = re.search(r"retracts:\s*([0-9a-f]{8})", tail.split("[", 1)[0])
            if retracts:
                # A tombstone kills the most recent matching entry ABOVE it, and
                # only that one. Applying it to every entry with the id made a
                # re-filed correction invisible forever -- and corrections are
                # the top category this tool exists to keep.
                target = retracts.group(1)
                victim = next((e for e in reversed(order)
                               if e["id"] == target and not e["retracted_by"]), None)
                pending_tomb = {"by": eid, "victim": victim}
                if victim is not None:
                    victim["retracted_by"] = eid
                current = None
                continue
            current = {"id": eid, "ts": ts, "body": [], "retracted_by": None,
                       "retract_reason": "", "header": line, "lineno": lineno}
            entries.append(current)
            order.append(current)
            pending_tomb = None
            continue
        if pending_tomb is not None and line.startswith("reason:"):
            if pending_tomb["victim"] is not None:
                pending_tomb["victim"]["retract_reason"] = line[len("reason:"):].strip()
            pending_tomb = None
            continue
        if current is not None:
            current["body"].append(line)
    if text.strip() and not entries:
        # Non-empty but nothing parsed: a hand-written or foreign FINDINGS.md,
        # which plenty of repos already have. Saying "no findings" silently
        # would manufacture an absence; RAISING was worse -- it made such a
        # project permanently unwritable AND unreadable, with no adopt path and
        # no message telling the operator what to do. Be LOUD, never fatal:
        # note.py only ever appends, so its entries coexist with foreign text.
        print(f"note: {record} has {len(text.splitlines())} line(s) of content "
              "that are not note.py entries — they are left untouched and are "
              "NOT included below; new findings append after them.",
              file=sys.stderr)
    return entries


def _index_rows() -> list[tuple[str, str, str, str]]:
    if not GLOBAL_INDEX.is_file():
        return []
    rows = []
    for line in GLOBAL_INDEX.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("- "):
            continue
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) >= 4:
            rows.append((parts[0], parts[1], parts[2], "|".join(parts[3:])))
    return rows


def _index_has(project: Path, eid: str) -> bool:
    """Match the parsed (project, id) fields -- never a raw substring.

    A substring test for "| <id> |" was spoofable by a finding whose summary
    quoted a pipe table, which defeated the divergence repair.
    """
    return any(r[1] == str(project) and r[2] == eid for r in _index_rows())


def _index_append(project: Path, eid: str, summary: str, dedupe: bool = False,
                  ts: str | None = None) -> bool:
    """Append one index row. `dedupe` re-checks INSIDE the lock.

    The check has to happen under the mutex: six sessions running `--recent` on
    the same project at once each saw the row missing and each appended it
    (measured: 5 duplicate rows, zero loss). Checking outside the lock is a
    check-then-act race; checking inside it is not.
    """
    GLOBAL_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with _Lock(GLOBAL_INDEX) as lk:
        if dedupe and _index_has(project, eid):
            return False
        need_header = os.fstat(lk.fd).st_size == 0
        # Leading newline: a writer killed mid-append leaves bytes with no
        # trailing newline, and the next row would otherwise fuse onto it.
        lk.append(("" if need_header else "\n").join(
            ([GLOBAL_HEADER] if need_header else [""])
            # A reconciled row carries the entry's ORIGINAL timestamp. Stamping
            # _now() silently turned the index's "when" column into "when it was
            # repaired", which is not what the column says it means.
            + [f"- {ts or _now()} | {project} | {eid} | {summary}"]) + "\n")
        return True


def _universal_has(project: Path, eid: str) -> bool:
    if not UNIVERSAL_INDEX.is_file():
        return False
    needle = f"| {project} | {eid} |"
    return any(needle in line
               for line in UNIVERSAL_INDEX.read_text(encoding="utf-8", errors="replace").splitlines())


def _universal_append(project: Path, eid: str, summary: str, ts: str | None = None) -> bool:
    """Append one row. Dedupe check happens INSIDE the lock -- same race as _index_append."""
    UNIVERSAL_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with _Lock(UNIVERSAL_INDEX) as lk:
        if _universal_has(project, eid):
            return False
        need_header = os.fstat(lk.fd).st_size == 0
        lk.append(("" if need_header else "\n").join(
            ([UNIVERSAL_HEADER] if need_header else [""])
            + [f"- {ts or _now()} | {project} | {eid} | {summary}"]) + "\n")
        return True


def cmd_universal() -> int:
    if not UNIVERSAL_INDEX.is_file():
        print(f"no universal findings yet: {UNIVERSAL_INDEX}")
        return 0
    text = UNIVERSAL_INDEX.read_text(encoding="utf-8", errors="replace")
    rows = [ln for ln in text.splitlines() if ln.startswith("- ")]
    print(f"{len(rows)} universal finding(s)  ({UNIVERSAL_INDEX})")
    for row in rows:
        print(row)
    return 0


def cmd_tag_universal(eid: str, target_dir: str) -> int:
    """Backfill: mark an EXISTING finding as scope:universal without touching its body.

    The original entry in <project>/FINDINGS.md is never rewritten -- this only
    appends a row to the sidecar (UNIVERSAL_INDEX). A human confirms each id
    before tagging (prep-auto-rebuild.txt Phase 1.1 Step 2): the any/every/all
    pattern in a context: line finds CANDIDATES, not answers -- several here
    read general but name project-specific files once the body is actually read.
    """
    project = _resolve_dir(target_dir)
    entries = _read_entries(project / RECORD_NAME)
    match = next((e for e in entries if e["id"] == eid), None)
    if match is None:
        raise ValueError(f"no finding with id {eid} in {project / RECORD_NAME}")
    if match["retracted_by"]:
        raise ValueError(f"{eid} is retracted; refusing to tag a dead finding as universal")
    summary = _summary("\n".join(match["body"]))
    if _universal_append(project, eid, summary, ts=match["ts"]):
        print(f"tagged universal: {eid} -> {UNIVERSAL_INDEX}")
    else:
        print(f"already tagged universal: {eid}")
    return 0


def cmd_note(target_dir: str, file_path: str) -> int:
    project = _resolve_dir(target_dir)
    src = Path(file_path)
    if not src.is_file():
        raise ValueError(f"--file not found: {file_path}")
    body = src.read_text(encoding="utf-8-sig", errors="strict").strip()
    if not body:
        raise ValueError(f"--file is empty: {file_path}")
    if "\x00" in body:
        # A NUL makes git classify the file as binary, which kills diffs on a
        # tracked FINDINGS.md forever.
        raise ValueError("--file contains NUL bytes; findings must be text")
    if len(body.encode("utf-8")) > MAX_BODY_BYTES:
        raise ValueError(
            f"--file is {len(body.encode('utf-8'))} bytes, over the "
            f"{MAX_BODY_BYTES}-byte cap. A finding is a lesson, not a log dump."
        )
    _guard_secret(body, "the finding body")

    eid = _sha8(body)
    record = project / RECORD_NAME

    for entry in _read_entries(record):
        if entry["id"] != eid or entry["retracted_by"]:
            continue
        # An id match is NOT proof of the same finding: sha8 is 32 bits, so two
        # genuinely different findings collide at ~1.2% per 10k in one project.
        # Comparing ids alone silently DISCARDED the second one while printing
        # success. Compare the bodies; on a real collision, salt and file it.
        if _normalize("\n".join(entry["body"])) != _normalize(body):
            eid = _sha8(body + f"\ncollision-salt: {_now()}")
            print(f"sha8 collision with an existing finding — filing as {eid}")
            break
        if _index_has(project, eid):
            print(f"duplicate: skipped (id {eid} already in {record})")
            return 0
        _index_append(project, eid, _summary(body))
        print(f"repaired {eid}: record had it, global index did not")
        return 0

    _append(record, f"\n## {_now()}  id: {eid}\n{_neutralize(body)}\n")   # record FIRST
    try:
        _index_append(project, eid, _summary(body))                       # index SECOND
    except OSError as exc:
        # Be precise about what survived. "note failed" alone invites the caller
        # to reword and re-file, which creates a second entry for one lesson.
        raise OSError(
            f"record WRITTEN ({eid} in {record}) but the global index failed: {exc}. "
            "Retry with the SAME --file to repair the index; do not reword."
        ) from None
    scope_match = SCOPE_RE.search(body)
    if scope_match and scope_match.group(1).lower() == "universal":
        try:
            _universal_append(project, eid, _summary(body))
            print(f"noted {eid} -> {record}  (also tagged universal)")
        except OSError as exc:
            # The finding is already safely recorded+indexed above; the
            # universal tag is a convenience, never a reason to fail the note.
            print(f"noted {eid} -> {record}  (universal tag deferred: {exc})")
        return 0
    print(f"noted {eid} -> {record}")
    return 0


def _reconcile(project: Path, entries: list[dict]) -> int:
    """Index anything the record has and the index lacks.

    This is the DETECTOR for record/index divergence. Without it the gap only
    healed if the identical finding happened to be submitted again, which is a
    band-aid: nothing would ever notice a finding that stayed invisible.
    """
    fixed = 0
    for e in entries:
        if e["retracted_by"] or _index_has(project, e["id"]):
            continue
        try:
            if _index_append(project, e["id"], _summary("\n".join(e["body"])),
                             dedupe=True, ts=e["ts"]):
                fixed += 1
        except OSError as exc:
            # Reading must never fail because a REPAIR could not be written.
            # A read-only or locked index used to make --recent exit 1 and show
            # nothing, which breaks the read half of the goal to fix a
            # bookkeeping gap.
            print(f"note: index repair deferred ({exc})", file=sys.stderr)
            return fixed
    return fixed


def cmd_recent(target_dir: str, limit: int) -> int:
    project = _resolve_dir(target_dir)
    entries = _read_entries(project / RECORD_NAME)
    live = [e for e in entries if not e["retracted_by"]]
    dead = [e for e in entries if e["retracted_by"]]
    if not entries:
        print(f"no findings recorded for {project}")
        return 0
    repaired = _reconcile(project, entries)
    shown = live[-limit:]
    print(f"{len(live)} live finding(s) for {project}"
          + (f" — showing {len(shown)}" if len(shown) < len(live) else "")
          + (f"  ({len(dead)} retracted)" if dead else "")
          + (f"  [reconciled {repaired} missing index line(s)]" if repaired else ""))
    # Body lines are INDENTED on output, never .strip()ed. Stripping removed the
    # very leading space _neutralize added, so a forged header that was safely
    # neutralized on disk came back at column 0 in the text the agent reads.
    for entry in reversed(shown):
        print(f"\n## {entry['ts']}  id: {entry['id']}")
        print("\n".join("    " + b for b in entry["body"]).rstrip())
    for entry in dead[-limit:]:
        # The BODY is printed too. Showing only the mark would tell a future
        # session that something was wrong without ever saying WHAT -- which is
        # the dead-belief-survives failure this whole tool exists to stop.
        print(f"\n## {entry['ts']}  id: {entry['id']}  [RETRACTED by "
              f"{entry['retracted_by']}] {entry['retract_reason']}")
        print("\n".join("  | " + b for b in entry["body"]).rstrip())
    return 0


def _project_for(path: Path) -> Path | None:
    """Nearest ancestor holding a FINDINGS.md. None means no record exists yet."""
    start = path if path.is_dir() else path.parent
    try:
        start = start.resolve()
    except OSError:
        return None
    for cand in [start, *start.parents]:
        if (cand / RECORD_NAME).is_file():
            return cand
    return None


def cmd_for(raw: str, limit: int) -> int:
    """Every note naming this FILE -- the lookup you run when something misbehaves.

    Matching is by BASENAME on purpose: a note written against `fetch.py` must still
    be found after the file moves. The cost is that a common name can match a note
    about a different file, so the project and the full body are always printed --
    never just a summary -- and the caller judges.

    An ABSENT FINDINGS.md and a PRESENT one with no match are DIFFERENT answers and
    print differently. Collapsing them would report "nothing known" for a project
    that was simply never recorded in -- an absence-of-data claim manufactured out
    of an absence of records.
    """
    target = Path(raw)
    # Same refusal as _resolve_dir, for the same reason: a path resolved against
    # an arbitrary cwd silently answers 'no record' for the WRONG place, which
    # manufactures an absence-of-data claim -- the exact failure this tool exists
    # to prevent. Refuse loudly instead of guessing.
    if not target.is_absolute():
        hint = "  (that looks like a git-bash path -- Windows Python needs C:\\... form)" if raw.startswith("/") else ""
        raise ValueError(f"--for must be an ABSOLUTE path, got {raw!r}{hint}")
    try:
        target = target.resolve()
    except OSError:
        pass
    name = target.name
    if not name:
        raise ValueError("--for needs a file path, not a directory root")
    needle = name.lower()

    project = _project_for(target)
    if project is None:
        print(f"no {RECORD_NAME} in {target.parent} or any parent -- this project "
              f"has no findings record yet (NOT the same as 'nothing known "
              f"about {name}')")
    else:
        entries = _read_entries(project / RECORD_NAME)   # unreadable -> raises
        hits = [e for e in entries if needle in "\n".join(e["body"]).lower()]
        live = [e for e in hits if not e["retracted_by"]]
        dead = [e for e in hits if e["retracted_by"]]
        print(f"{len(live)} live note(s) naming {name} in {project}"
              + (f"  ({len(dead)} retracted)" if dead else ""))
        for entry in reversed(live[-limit:]):
            print(f"\n## {entry['ts']}  id: {entry['id']}")
            print("\n".join("    " + b for b in entry["body"]).rstrip())
        for entry in dead[-limit:]:
            # The retracted body prints too: a future session needs to know WHAT
            # was wrong, not merely that something was.
            print(f"\n## {entry['ts']}  id: {entry['id']}  [RETRACTED by "
                  f"{entry['retracted_by']}] {entry['retract_reason']}")
            print("\n".join("  | " + b for b in entry["body"]).rstrip())

    # Cross-folder leg: a note about this file may have been filed against a
    # DIFFERENT project (shared code, or a file that moved between roots).
    rows = [r for r in _index_rows()
            if needle in r[3].lower() and (project is None or r[1] != str(project))]
    if rows:
        print(f"\nalso named in {len(rows)} finding(s) filed under other projects:")
        for ts, proj, eid, summary in rows[-limit:]:
            print(f"  {ts}  {eid}  {summary}")
            print(f"      -> note.py --recent \"{proj}\"")
    return 0


def cmd_index(limit: int) -> int:
    rows = _index_rows()
    if not rows:
        print(f"global index is empty or absent: {GLOBAL_INDEX}")
        return 0
    print(f"{len(rows)} finding(s) across all projects  ({GLOBAL_INDEX})")
    by_proj: dict[str, list] = {}
    for ts, proj, eid, summary in rows:
        by_proj.setdefault(proj, []).append((ts, eid, summary))
    for proj, items in by_proj.items():
        print(f"\n{proj}   ({len(items)})")
        for ts, eid, summary in items[-limit:]:
            print(f"  {ts}  {eid}  {summary}")
    return 0


def cmd_retract(eid: str, target_dir: str, reason: str) -> int:
    """Mark the finding dead IN PLACE and append a tombstone for provenance.

    The in-place mark is a whole-file rewrite, which is normally the lost-update
    shape the lock exists to prevent -- it is safe here only because it happens
    while holding the writer mutex, and because readers never contend for it.
    """
    project = _resolve_dir(target_dir)
    record = project / RECORD_NAME
    if not reason.strip():
        raise ValueError("--reason is required: say what was wrong about it")
    # --reason is the OTHER write path into these files, and it was reaching disk
    # unscanned and unneutralized: a reason containing a newline plus a forged
    # `## ... retracts: <id>` line could retract an unrelated finding, and a
    # credential pasted here landed in two git-tracked files. Collapse to one
    # line first, then apply exactly the guards the body gets.
    reason = " ".join(reason.split())
    _guard_secret(reason, "--reason")
    reason = _neutralize(reason)
    entries = _read_entries(record)
    live = [e for e in entries if e["id"] == eid and not e["retracted_by"]]
    if not live:
        if any(e["id"] == eid for e in entries):
            print(f"already retracted: {eid}")
            return 0
        raise ValueError(f"no finding with id {eid} in {record}")
    target = live[-1]
    tomb_id = _sha8(f"retract {eid} {reason} {_now()}")
    # The mark carries the tombstone ID ONLY -- no free text. Embedding the
    # reason here put caller-supplied text inside a header line, and header
    # tails are where `retracts:` directives are read from: a reason mentioning
    # `retracts: <id>` turned this entry's own header into a tombstone against
    # an unrelated finding. The reason lives on the tombstone's `reason:` line,
    # which is only ever consumed as text.
    mark = f"  [RETRACTED by {tomb_id}]"
    with _Lock(record) as lk:
        # Re-parse INSIDE the lock and mark by LINE INDEX. A substring replace
        # of the bare header was wrong twice over: a bare header is a PREFIX of
        # an already-marked one, so `replace(..., 1)` hit an earlier, already-
        # dead copy and left the live one unmarked; and it gave the file two
        # independent rules for one fact (the parser binds "most recent live
        # entry above"; the replace bound "first substring"). Only the parser is
        # consulted on read, so the mark could silently disagree with it.
        fresh = _read_entries(record)
        live_now = [e for e in fresh if e["id"] == eid and not e["retracted_by"]]
        if not live_now:
            raise ValueError(f"{eid} was retracted by another writer; nothing to do")
        tgt = live_now[-1]
        lines = record.read_text(encoding="utf-8", errors="replace").splitlines()
        i = tgt["lineno"]
        if not (0 <= i < len(lines) and lines[i] == tgt["header"]):
            raise ValueError(f"record shifted under us; retry the retraction of {eid}")
        lines[i] = lines[i] + mark
        text = "\n".join(lines) + "\n"
        text += (f"\n## {_now()}  id: {tomb_id}  retracts: {eid}\n"
                 f"reason: {reason}\n")
        lk.rewrite(text, tag=tomb_id)
    _index_append(project, tomb_id, f"RETRACTS {eid} — {reason.strip()[:120]}")
    print(f"retracted {eid} (marked in place; tombstone {tomb_id}) -> {record}")
    return 0


def _arg(argv: list[str], flag: str, default: str | None = None) -> str | None:
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            return argv[i + 1]
        if default is not None:
            return default
        raise ValueError(f"{flag} needs a value")
    return default


USAGE = (
    "usage:\n"
    "  note.py --dir <ABS project> --file <finding.txt>   (--file may include a\n"
    "                                    'scope: universal' line -- see below)\n"
    "  note.py --recent <ABS project> [--limit N]\n"
    "  note.py --index [--limit N]\n"
    "  note.py --retract <id> --dir <ABS project> --reason \"<why>\"\n"
    "  note.py --for <path to a file> [--limit N]\n"
    "  note.py --universal                                (read the universal sidecar)\n"
    "  note.py --tag-universal <id> --dir <ABS project>    (backfill an existing finding)\n"
)


def main(argv: list[str]) -> int:
    if not argv or "--help" in argv or "-h" in argv:
        print(USAGE)
        return 0
    try:
        limit = int(_arg(argv, "--limit", "20"))
        if limit <= 0:
            # `live[-0:]` is the WHOLE list, so --limit 0 silently dumped every
            # entry into the caller's context -- the opposite of what it says.
            raise ValueError("--limit must be a positive integer")
        if "--index" in argv:
            return cmd_index(limit)
        if "--for" in argv:
            return cmd_for(_arg(argv, "--for"), limit)
        if "--recent" in argv:
            return cmd_recent(_arg(argv, "--recent"), limit)
        if "--retract" in argv:
            return cmd_retract(_arg(argv, "--retract"), _arg(argv, "--dir"),
                               _arg(argv, "--reason", ""))
        if "--universal" in argv:
            return cmd_universal()
        if "--tag-universal" in argv:
            return cmd_tag_universal(_arg(argv, "--tag-universal"), _arg(argv, "--dir"))
        target, src = _arg(argv, "--dir"), _arg(argv, "--file")
        if not target or not src:
            print(USAGE, file=sys.stderr)
            return 2
        return cmd_note(target, src)
    # TypeError is in the tuple deliberately: a missing flag value used to reach
    # Path(None) and exit via an unreadable traceback, which met "always surface
    # a failure" only by accident.
    except (ValueError, TypeError, OSError, UnicodeError) as exc:
        print(f"note failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
