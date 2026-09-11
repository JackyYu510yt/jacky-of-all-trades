#!/usr/bin/env python3
"""lanes.py -- LANES.md, the replacement for ACTIVE-LANES.md.

    python lanes.py claim   --folder <ABS folder> --files "<what's claimed>" --session <id>
    python lanes.py release --session <id>
    python lanes.py read

prep-auto-rebuild.txt Milestone 3. One line per LIVE run, nothing else:

    <started ISO> | <session-id> | <folder> | <files claimed>

No status prose, no evidence, no finding IDs -- those live in FINDINGS.md and
SPEC.md now (Milestone 1). This file answers exactly one question: "is anyone
else working in this folder on these files right now?"

SELF-EXPIRY ON READ (Phase 3.2). A row is dropped, and the file rewritten
without it, when EITHER holds:
  - it is older than 24h (the same staleness rule ACTIVE-LANES.md used, now
    actually computable because `started` is a full ISO timestamp, not a
    bare date), OR
  - its session marker -- <folder>/auto-runs/.session-<session-id> -- no
    longer exists. That marker is written at slug-freeze and deleted at
    terminal verdict (see the auto skill's Session marker section), so its
    absence means the run that claimed this row already ended (cleanly) or
    the session died before it could release its own row (crashed). Either
    way, the row is stale.

This makes `read` self-cleaning: every read is also a garbage-collection
pass, so a crashed session's claim doesn't linger for 24h the way a bare-date
board could not detect at all.

LOCKING. Same mutex discipline as note.py's FINDINGS.md/UNIVERSAL_FINDINGS.md
(a sentinel byte far past EOF, so writers exclude each other and readers are
never blocked) -- imported directly from note.py rather than re-implemented,
so the two files can never drift on lock behavior.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

NOTE_PY_DIR = Path.home() / ".claude" / "skills" / "spec"
if str(NOTE_PY_DIR) not in sys.path:
    sys.path.insert(0, str(NOTE_PY_DIR))
import note  # noqa: E402  (path must be set first) -- reused for _Lock only

LANES_PATH = Path.home() / ".claude" / "LANES.md"
STALE_AFTER = datetime.timedelta(hours=24)

HEADER = """# LANES -- who is working where, right now

One line per LIVE run: started | session-id | folder | files claimed.
Nothing else -- no status prose, no evidence, no finding IDs (those live in
FINDINGS.md and SPEC.md). Self-expiring: every `read` drops any row older
than 24h or whose session has already ended, and rewrites the file without
it. See ~/.claude/skills/auto/lanes.py.
"""


def _now() -> datetime.datetime:
    return datetime.datetime.now()


def _fmt(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _parse_ts(s: str) -> datetime.datetime | None:
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def _parse_rows(text: str) -> list[tuple[str, str, str, str]]:
    """Only lines starting with '- ' are rows. This is deliberately narrower
    than 'contains a pipe' -- the header's own prose describes the format
    using pipes ("started | session-id | folder | files claimed"), and a
    looser match would parse that description AS a row (caught by this
    file's own test suite: the header line was silently counted as two
    phantom entries before this fix)."""
    rows = []
    for line in text.splitlines():
        if not line.startswith("- "):
            continue
        raw = line[2:]
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) >= 4:
            rows.append((parts[0], parts[1], parts[2], "|".join(parts[3:])))
    return rows


def _marker_path(folder: str, session_id: str) -> Path:
    return Path(folder) / "auto-runs" / f".session-{session_id}"


def _is_stale(row: tuple[str, str, str, str], now: datetime.datetime) -> tuple[bool, str]:
    started_s, session_id, folder, _files = row
    ts = _parse_ts(started_s)
    if ts is not None and (now - ts) > STALE_AFTER:
        return True, f"older than 24h (started {started_s})"
    marker = _marker_path(folder, session_id)
    if not marker.is_file():
        return True, f"session marker gone ({marker})"
    return False, ""


def _rewrite(rows: list[tuple[str, str, str, str]]) -> None:
    body = "\n".join(f"- {s} | {sid} | {f} | {files}" for s, sid, f, files in rows)
    text = HEADER + ("\n" + body + "\n" if body else "\n")
    LANES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with note._Lock(LANES_PATH) as lk:
        lk.rewrite(text, tag="lanes")


def read(gc: bool = True) -> list[tuple[str, str, str, str]]:
    """Read live rows. When gc=True (the default), drop stale rows and
    rewrite the file -- this IS the self-expiry mechanism (Phase 3.2)."""
    if not LANES_PATH.is_file():
        return []
    text = LANES_PATH.read_text(encoding="utf-8", errors="replace")
    rows = _parse_rows(text)
    if not gc:
        return rows
    now = _now()
    survivors = []
    dropped = []
    for row in rows:
        stale, reason = _is_stale(row, now)
        if stale:
            dropped.append((row, reason))
        else:
            survivors.append(row)
    if dropped:
        _rewrite(survivors)
    return survivors


def claim(folder: str, files: str, session_id: str) -> None:
    folder_p = Path(folder)
    if not folder_p.is_absolute():
        raise ValueError(f"--folder must be ABSOLUTE, got {folder!r}")
    # Read first (this also GCs stale rows) so a claim never sits on top of
    # rows this same call would have expired anyway.
    rows = read(gc=True)
    rows = [r for r in rows if r[1] != session_id]  # one row per session
    rows.append((_fmt(_now()), session_id, str(folder_p), files))
    _rewrite(rows)


def release(session_id: str) -> bool:
    """Returns True if a row was actually removed (never raises if absent --
    releasing an already-gone row is a legal no-op, same idempotency
    discipline as promote.py)."""
    rows = read(gc=False)  # don't GC here -- we want an exact count of what we remove
    kept = [r for r in rows if r[1] != session_id]
    if len(kept) == len(rows):
        return False
    _rewrite(kept)
    return True


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: lanes.py claim --folder F --files \"...\" --session S | "
              "release --session S | read", file=sys.stderr)
        return 2
    cmd = argv[0]

    def _opt(flag: str) -> str | None:
        return argv[argv.index(flag) + 1] if flag in argv else None

    try:
        if cmd == "claim":
            folder, files, session_id = _opt("--folder"), _opt("--files"), _opt("--session")
            if not (folder and files is not None and session_id):
                print("usage: lanes.py claim --folder F --files \"...\" --session S",
                      file=sys.stderr)
                return 2
            claim(folder, files, session_id)
            print(f"claimed: {folder} (session {session_id})")
            return 0
        if cmd == "release":
            session_id = _opt("--session")
            if not session_id:
                print("usage: lanes.py release --session S", file=sys.stderr)
                return 2
            removed = release(session_id)
            print(f"released session {session_id}" if removed
                  else f"session {session_id} had no row (already released)")
            return 0
        if cmd == "read":
            rows = read(gc=True)
            if not rows:
                print("LANES.md: no live rows")
                return 0
            print(f"LANES.md: {len(rows)} live row(s)")
            for s, sid, folder, files in rows:
                print(f"  {s} | {sid} | {folder} | {files}")
            return 0
    except (ValueError, OSError) as exc:
        print(f"lanes.py failed: {exc}", file=sys.stderr)
        return 1
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
