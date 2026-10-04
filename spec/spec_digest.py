#!/usr/bin/env python3
"""spec_digest.py — generate/refresh a digest of SPEC.md into the project's CLAUDE.md.

Why this exists (2026-08-29): SPEC.md carried the whole project record and NOBODY read
it — a fresh chat auto-loads CLAUDE.md, never SPEC.md ("manual — there is no auto-load",
spec SKILL.md). This tool writes a generated, deterministic digest of SPEC.md between
exact markers in CLAUDE.md, so the record reaches every fresh session automatically.

Three modes:
  python spec_digest.py <dir>            generate/refresh <dir>/CLAUDE.md from <dir>/SPEC.md
  python spec_digest.py --check <dir>    FRESH (exit 0) / STALE (exit 3) / NOTHING-TO-CHECK
                                         (exit 4, no SPEC.md and no digest) — recomputes the
                                         SPEC.md hash NOW; never trusts the stamp alone
  (PostToolUse JSON on stdin, no args)   hook mode: after any tool call that touched a
                                         SPEC.md, refresh that project's digest. Appends a
                                         provenance line to digest-hook.log on every
                                         relevant event; all errors go to digest-errors.log
                                         and the hook still exits 0 — it is a recorder,
                                         never a gate (user rule 2026-08-29).

Determinism rule: nothing wall-clock ever lands in CLAUDE.md — the stamp is SPEC.md's
content hash + SPEC.md's own mtime, so re-running on an unchanged SPEC.md is byte-identical.

Concurrency rules (RED-TEAM 2026-08-29): the stamp is hashed from the SAME single raw
read the digest summarizes (B2); CLAUDE.md writes re-read just before the atomic swap and
retry once if another writer landed mid-build (B1); a structural refusal (bad encoding,
corrupt markers) leaves a one-line breadcrumb at <dir>/.spec/digest-blocked.txt that
--check surfaces and a later successful regen clears (B4).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MARK_BEGIN = "<!-- SPEC-DIGEST:BEGIN (auto-generated from SPEC.md by spec_digest.py - do not hand-edit) -->"
MARK_END = "<!-- SPEC-DIGEST:END -->"
HOOK_LOG = Path.home() / ".claude" / "skills" / "spec" / "digest-hook.log"
ERR_LOG = Path.home() / ".claude" / "skills" / "spec" / "digest-errors.log"
NOTHING_REASON = "no SPEC.md here — nothing to digest"


def resolve_spec_path(project_dir: Path) -> Path:
    """<project>/Spec/SPEC.md if it exists there (2026-09-17 file-layout
    convention), else the legacy <project>/SPEC.md — so old and reorganized
    projects both resolve correctly. Never guesses which layout a project
    uses beyond checking what's actually on disk."""
    in_spec_folder = project_dir / "Spec" / "SPEC.md"
    if in_spec_folder.is_file():
        return in_spec_folder
    return project_dir / "SPEC.md"


# ── unit 1: parse + build ────────────────────────────────────────────────────

def parse_spec(text: str) -> dict:
    """SPEC.md content -> {heading_key: body}. heading_key = text after '## ', lowercased, stripped.
    Sections run until the next '## ' line. Tolerant: missing sections are simply absent keys.
    Must not crash on ANY text input (empty file, no headings, weird unicode)."""
    sections = {}
    originals = {}  # heading_key -> original heading text, for display
    key = None
    body_lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            if key is not None:
                sections[key] = "\n".join(body_lines)
            heading = line[3:].strip()
            key = heading.lower()
            originals[key] = heading
            body_lines = []
        elif key is not None:
            body_lines.append(line)
    if key is not None:
        sections[key] = "\n".join(body_lines)
    if originals:
        # Reserved companion key (dict, not str): original-cased headings.
        # build_digest falls back to the lowercased key if it is absent.
        sections["_original_headings"] = originals
    return sections


def build_digest(sections: dict, sha8: str, spec_mtime_iso: str, check_dir_hint: str = ".") -> str:
    """Return the FULL digest block string, MARK_BEGIN line first, MARK_END line last.
    DETERMINISTIC: no wall-clock calls, no randomness — same inputs, byte-identical output.
    (sha8 and spec_mtime_iso are computed by the caller.)"""

    def one_line(s: str, limit: int) -> str:
        s = " ".join(s.split())  # collapse all whitespace -> one physical line
        # Defang quoted marker text (FnReview F3, 2026-08-29): SPEC content quoting the
        # markers must never survive into the block, or this write creates a 2-marker
        # CLAUDE.md that wedges every future run. A digest is a summary; defusing the
        # quote is fidelity enough.
        s = s.replace("SPEC-DIGEST:BEGIN", "SPEC-DIGEST-BEGIN")
        s = s.replace("SPEC-DIGEST:END", "SPEC-DIGEST-END")
        if len(s) > limit:
            return s[:limit] + "..."
        return s

    def table_rows(body: str) -> list:
        """Markdown table -> list of cell-lists. rows[0] is the header row."""
        rows = []
        for ln in body.splitlines():
            s = ln.strip()
            if not s.startswith("|"):
                continue
            if re.fullmatch(r"\|[\s:\-|]*\|?", s):
                continue  # separator row
            rows.append([c.strip() for c in s.strip("|").split("|")])
        return rows

    originals = sections.get("_original_headings")
    if not isinstance(originals, dict):
        originals = {}

    closed = []
    open_ = []

    # Goal
    goal_body = sections.get("goal", "")
    goal = one_line(goal_body, 400) if isinstance(goal_body, str) else ""
    if not goal:
        goal = "(no goal section)"

    # Build State rows: closed vs open, decided on the STATE column's LEADING token
    body = sections.get("build state")
    if isinstance(body, str):
        bs_rows = table_rows(body)
        bs_header = bs_rows[0] if bs_rows else []
        state_idx = next(
            (i for i, c in enumerate(bs_header)
             if "state" in c.lower() or "status" in c.lower()), 1
        )
        for cells in bs_rows[1:]:
            if len(cells) < 2:
                continue  # malformed row: skip it, not the section
            state_cell = cells[state_idx] if state_idx < len(cells) else ""
            # LEADING token only (FnReview round 2, 2026-08-29): a search would close
            # the canonical "UNVERIFIED (was: LIVE, <date>)" row — the one the table
            # exists to distrust. \W* still admits markdown-bolded "**LIVE**" cells
            # (real case: the Production Factory's Build State). "done" kept: generic
            # SPEC.md files aren't guaranteed the canonical state vocabulary.
            if re.match(r"\W*(live|done)\b", state_cell.lower()):
                closed.append(one_line("- Build State: " + " — ".join(cells[:2]), 400))
            else:
                # A SPEC'D / BUILT / WIRED / UNVERIFIED deliverable is OPEN work —
                # the goal is "what is closed AND what is open", not closed-only
                # (gap surfaced by the ghostsvc UNVERIFIED test, 2026-08-29).
                open_.append(one_line("- Build State: " + " — ".join(cells[:2]) + " — not closed", 400))

    # Open (1): Assumptions & Unknowns bullets (continuation lines joined)
    body = sections.get("assumptions & unknowns")
    if isinstance(body, str):
        bullet = None
        for ln in body.splitlines():
            if ln.lstrip().startswith("- "):
                if bullet:
                    open_.append("- " + one_line(bullet, 200))
                bullet = ln.lstrip()[2:]
            elif bullet is not None and ln.strip():
                bullet += " " + ln.strip()
        if bullet:
            open_.append("- " + one_line(bullet, 200))

    # Closed (2) / Open (2): blueprint milestone/phase sections
    for key, sec_body in sections.items():
        if not isinstance(sec_body, str) or key == "_original_headings":
            continue
        if not re.match(r"(milestone|phase)\b", key):  # \b excludes "phases (blueprint)"
            continue
        heading = originals.get(key, key)
        if re.search(r"^\s*STATUS:.*\bDONE\b", sec_body, re.MULTILINE):
            closed.append(one_line("- " + heading + ": DONE", 400))
        else:
            open_.append(one_line("- " + heading + ": not marked done", 400))

    # Closed (3) / Open (3): Runs in this project table
    body = sections.get("runs in this project")
    if isinstance(body, str):
        rows = table_rows(body)
        header = rows[0] if rows else []
        folder_idx = next(
            (i for i, c in enumerate(header) if "folder" in c.lower()), 1
        )
        for cells in rows[1:]:
            if len(cells) < 2:
                continue  # malformed row: skip it, not the section
            folder = cells[folder_idx] if folder_idx < len(cells) else cells[0]
            last = cells[-1]
            if last.startswith("DONE"):
                closed.append(one_line("- Run " + folder + ": DONE", 400))
            else:
                open_.append(one_line("- Run " + folder + ": " + one_line(last, 120), 400))

    # Recently learned: Change Log entries, sorted by date string DESC, first 5
    entries = []
    body = sections.get("change log")
    if isinstance(body, str):
        date = None
        change = None
        for ln in body.splitlines():
            m = re.match(r"-\s*date:\s*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)\s*$", ln.strip())
            if m:
                if date is not None and change is not None:
                    entries.append((date, change))
                date, change = m.group(1), None
                continue
            m = re.match(r"\s+change:\s*(.+)", ln)
            if m and date is not None and change is None:
                change = m.group(1).strip()
        if date is not None and change is not None:
            entries.append((date, change))
    entries.sort(key=lambda e: e[0], reverse=True)  # stable: ties keep file order
    recent = ["- " + d + " — " + one_line(c, 200) for d, c in entries[:5]]

    lines = [
        MARK_BEGIN,
        "## Project state — digest of SPEC.md (auto-generated)",
        "",
        "Source: SPEC.md sha256:" + sha8 + " (SPEC.md last modified " + spec_mtime_iso + ")",
        (r'Freshness: run `python "C:\Users\Shadow\.claude\skills\spec\spec_digest.py" --check '
         + check_dir_hint
         + "` — STALE means this summary is out of date: read SPEC.md directly."),
        "",
        "**Goal:** " + goal,
        "",
        "**Closed (done / live):**",
    ]
    lines.extend(closed if closed else ["- (nothing recorded as closed)"])
    lines.append("")
    lines.append("**Open / unproven:**")
    lines.extend(open_ if open_ else ["- (nothing recorded as open)"])
    lines.append("")
    lines.append("**Recently learned (newest Change Log entries first):**")
    lines.extend(recent if recent else ["- (no change log entries)"])
    lines.append("")
    lines.append("Full record: SPEC.md — this digest is a pointer with a summary, not a copy.")
    lines.append(MARK_END)
    return "\n".join(lines)


# ── unit 2: hash + anchored atomic write + freshness ─────────────────────────

def sha8_of_bytes(raw: bytes) -> str:
    """First 8 hex chars of sha256 of raw bytes. The single hashing definition —
    generation hashes the exact bytes it summarized (RED-TEAM B2)."""
    return hashlib.sha256(raw).hexdigest()[:8]


def sha8_of(path) -> str:
    """First 8 hex chars of sha256 of the file's RAW BYTES. path: pathlib.Path."""
    return sha8_of_bytes(path.read_bytes())


def _read_claude(claude_path):
    """One definition of the CLAUDE.md read (strict utf-8, newline='') used by BOTH
    the initial read and the pre-swap CAS re-read, so the two can never diverge in
    decode behavior. Returns None if the file does not exist. Strict decode
    (FnReview F2): errors='replace' on a read-modify-write would permanently
    mangle every undecodable byte file-wide on the next real write."""
    if not claude_path.exists():
        return None
    try:
        with open(claude_path, "r", encoding="utf-8", newline="") as f:
            return f.read()
    except UnicodeDecodeError as e:
        raise ValueError(
            f"{claude_path} is not valid utf-8 ({e}) — refusing to rewrite; "
            "fix the file's encoding or regenerate it as utf-8"
        )


def write_digest(claude_path, block: str) -> bool:
    """Insert/replace the digest block in CLAUDE.md atomically. Loud ValueError on
    marker corruption (anchored-edit discipline: a moved or duplicated anchor fails
    loudly instead of corrupting the file). CAS-guarded (RED-TEAM B1): re-reads just
    before the atomic swap; if a human or another session saved the file mid-build,
    rebuilds once from the fresh bytes, then refuses loudly."""
    block = block.rstrip("\n")
    # Backstop to build-time defanging (FnReview F3): a block carrying extra marker
    # text would write a file that wedges every future run — refuse before writing.
    if block.count(MARK_BEGIN) != 1 or block.count(MARK_END) != 1:
        raise ValueError(
            "refusing to write: digest block does not contain exactly one marker pair"
        )

    for _attempt in range(2):
        old_content = _read_claude(claude_path)

        if old_content is None:
            new_content = block + "\n"
        else:
            n_begin = old_content.count(MARK_BEGIN)
            n_end = old_content.count(MARK_END)

            if n_begin == 0 and n_end == 0:
                new_content = old_content.rstrip("\n") + "\n\n" + block + "\n"
            elif n_begin == 1 and n_end == 1:
                begin_idx = old_content.index(MARK_BEGIN)
                end_idx = old_content.index(MARK_END)
                if end_idx < begin_idx:
                    raise ValueError(
                        f"digest markers corrupted in {claude_path}: "
                        f"{MARK_END!r} appears before {MARK_BEGIN!r} — refusing to write"
                    )
                # Full-line requirement (FnReview F1): a marker knocked mid-line by a hand
                # edit still counts 1/1, and span replacement would silently delete the
                # adjacent same-line text. Any placement corruption refuses loudly instead.
                for _idx, _mark in ((begin_idx, MARK_BEGIN), (end_idx, MARK_END)):
                    _ls = old_content.rfind("\n", 0, _idx) + 1
                    _le = old_content.find("\n", _idx)
                    if _le == -1:
                        _le = len(old_content)
                    if old_content[_ls:_le].strip() != _mark:
                        raise ValueError(
                            f"digest marker not on its own line in {claude_path} — "
                            "refusing to write (a mid-line marker would silently delete "
                            "adjacent text)"
                        )
                # Span: start of the BEGIN line through end of the END line (newline after
                # the END line, if any, is preserved as part of the surrounding content).
                span_start = old_content.rfind("\n", 0, begin_idx) + 1
                nl_after_end = old_content.find("\n", end_idx + len(MARK_END))
                span_end = len(old_content) if nl_after_end == -1 else nl_after_end
                new_content = old_content[:span_start] + block + old_content[span_end:]
            else:
                raise ValueError(
                    f"digest markers corrupted in {claude_path}: "
                    f"found {n_begin} BEGIN and {n_end} END markers "
                    f"(expected exactly one of each) — refusing to write"
                )

        if new_content == old_content:
            return False

        # CAS guard (RED-TEAM B1): another writer (a human's editor save, a second
        # session's hook) may have landed while new_content was built. Re-read; a
        # change means our new_content was built on dead bytes — loop rebuilds from
        # the fresh state exactly once. The residual race window is the microseconds
        # between this re-read and os.replace — accepted (no portable file locking).
        if _read_claude(claude_path) != old_content:
            continue

        # Atomic: temp file in the SAME directory, then os.replace. Hidden-ish prefix
        # (RED-TEAM D1): a crashed run's leftover must not glob-match CLAUDE.md*.
        fd, tmp_path = tempfile.mkstemp(
            prefix=".spec-digest-", suffix=".tmp", dir=str(claude_path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
            os.replace(tmp_path, str(claude_path))
        except OSError:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass  # temp file already gone or locked; original error still surfaces
            raise
        return True

    raise ValueError(
        f"{claude_path} changed twice while the digest was being written — "
        "refusing after one rebuild; rerun when the file is quiet"
    )


def _blocked_crumb_path(project_dir):
    return project_dir / ".spec" / "digest-blocked.txt"


def _read_crumb(project_dir) -> str:
    try:
        p = _blocked_crumb_path(project_dir)
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        pass
    return ""


def check_fresh(project_dir) -> tuple:
    """(fresh, reason) — recomputes SPEC.md's hash NOW; never trusts the stamp alone.
    Surfaces the digest-blocked breadcrumb (RED-TEAM B4) so a refusal recorded by the
    hook is visible to whoever runs --check."""
    spec_path = resolve_spec_path(project_dir)
    claude_path = project_dir / "CLAUDE.md"
    crumb = _read_crumb(project_dir)
    suffix = f" [digest-blocked: {crumb[:200]}]" if crumb else ""

    if not spec_path.exists():
        # RED-TEAM B3: a digest with no SPEC.md behind it is ORPHANED — never FRESH.
        try:
            has_digest = claude_path.exists() and MARK_BEGIN in claude_path.read_text(
                encoding="utf-8", errors="replace")
        except OSError:
            has_digest = False
        if has_digest:
            return (False, "SPEC.md is missing but a digest exists — orphaned digest; "
                           "restore SPEC.md or delete the block" + suffix)
        return (True, NOTHING_REASON)

    if not claude_path.exists():
        return (False, "no digest / no stamp" + suffix)

    try:
        with open(claude_path, "r", encoding="utf-8", errors="replace", newline="") as f:
            content = f.read()
    except OSError as e:
        return (False, f"cannot read {claude_path}: {e}" + suffix)

    if content.count(MARK_BEGIN) != 1 or content.count(MARK_END) != 1:
        return (False, "no digest / no stamp" + suffix)
    begin_idx = content.index(MARK_BEGIN)
    end_idx = content.index(MARK_END)
    if end_idx < begin_idx:
        return (False, "no digest / no stamp" + suffix)

    span = content[begin_idx: end_idx + len(MARK_END)]
    m = re.search(r"SPEC\.md sha256:([0-9a-f]{8})", span)
    if m is None:
        return (False, "no digest / no stamp" + suffix)
    stamped = m.group(1)

    try:
        current = sha8_of(spec_path)
    except OSError as e:
        return (False, f"cannot hash {spec_path}: {e}" + suffix)

    if current != stamped:
        return (False, f"SPEC.md changed since digest: {current} vs stamped {stamped}" + suffix)
    return (True, "digest matches SPEC.md" + suffix)


# ── unit 3: entry points (CLI generate / CLI check / PostToolUse hook) ───────

def _build_block_from_disk(spec):
    """ONE raw read of SPEC.md — the stamp is the hash of the exact bytes summarized
    (RED-TEAM B2: three separate reads let a concurrent writer produce a
    FRESH-certified digest of bytes that were never summarized). The mtime is read
    after and is cosmetic display only — the hash governs staleness."""
    raw = spec.read_bytes()
    sha8 = sha8_of_bytes(raw)
    text = raw.decode("utf-8", errors="replace")
    mtime_iso = datetime.fromtimestamp(spec.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%S")
    return build_digest(parse_spec(text), sha8, mtime_iso, ".")


def _clear_crumb(project_dir):
    try:
        p = _blocked_crumb_path(project_dir)
        if p.exists():
            p.unlink()
    except OSError:
        pass


def _note_blocked(project_dir, reason: str) -> bool:
    """Overwrite the one-line breadcrumb; True when this exact reason was already
    recorded — the caller then skips duplicate log appends (RED-TEAM B4/D2: a poison
    CLAUDE.md must not grow the logs forever)."""
    line = " ".join(reason.split())[:300]
    try:
        p = _blocked_crumb_path(project_dir)
        if p.exists() and p.read_text(encoding="utf-8", errors="replace").strip() == line:
            return True
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(line + "\n", encoding="utf-8")
    except OSError:
        pass
    return False


def generate(project_dir) -> int:
    spec = resolve_spec_path(project_dir)
    if not spec.is_file():
        print(f"ERROR: no SPEC.md found in {project_dir}")
        return 2
    block = _build_block_from_disk(spec)
    changed = write_digest(project_dir / "CLAUDE.md", block)
    _clear_crumb(project_dir)
    print(f"{'regenerated' if changed else 'unchanged'}: {project_dir / 'CLAUDE.md'}")
    return 0


def hook_main() -> int:
    try:
        def _log(path, line):
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("not a JSON object")
        except Exception:
            # !r keeps the log one physical line — a raw snippet with an embedded
            # newline would wrap the entry and break line-scoped log reads.
            _log(ERR_LOG, f"{now} ERROR unparseable stdin ({raw[:80]!r})")
            return 0

        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input") or {}
        session_id = str(data.get("session_id") or "-")[:40]

        target_dir = None
        if tool_name in ("Edit", "Write", "NotebookEdit"):
            target = tool_input.get("file_path") or tool_input.get("notebook_path")
            if not target or Path(target).name.lower() != "spec.md":
                return 0
            target_dir = Path(target).parent
            # 2026-09-17 file-layout convention: SPEC.md may live in
            # <project>/Spec/SPEC.md — the digest still belongs in the
            # project root's CLAUDE.md, not in Spec/.
            if target_dir.name == "Spec":
                target_dir = target_dir.parent
        elif tool_name in ("Bash", "PowerShell"):
            command = (tool_input.get("command") or "").lower()
            cwd_val = data.get("cwd")
            if not cwd_val:
                return 0  # RED-TEAM U2: never guess a target directory
            cwd = Path(cwd_val)
            if ("spec.md" in command or "spec_tool.py" in command) and resolve_spec_path(cwd).is_file():
                target_dir = cwd
            else:
                return 0
        else:
            return 0

        fresh, _ = check_fresh(target_dir)
        if fresh:
            action = "fresh"
        else:
            spec = resolve_spec_path(target_dir)
            block = _build_block_from_disk(spec)
            try:
                write_digest(target_dir / "CLAUDE.md", block)
            except ValueError as ve:
                # Structural refusal (encoding / markers / CAS give-up): leave the
                # breadcrumb --check surfaces; dedupe repeat failures (RED-TEAM B4).
                already = _note_blocked(target_dir, str(ve))
                if already:
                    return 0  # same refusal already on record — no new information
                _log(ERR_LOG, f"{now} BLOCKED {str(target_dir)!r} {ve!r}")
                action = "blocked"
            else:
                _clear_crumb(target_dir)
                action = "regenerated"

        # !r on the dir (FnReview round 2): a payload path with an embedded newline
        # passes the basename gate and would wrap this one-line provenance entry.
        # session_id included (refuter concern, 2026-08-29): lets a later reader
        # attribute cross-session firings from the log alone.
        _log(HOOK_LOG, f"{now} {session_id} {tool_name} {str(target_dir)!r} {action}")
        return 0
    except Exception as exc:
        try:
            ERR_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(ERR_LOG, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} ERROR {exc!r}\n")
        except Exception:
            pass
        return 0


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 2 and argv[0] == "--check":
        fresh, reason = check_fresh(Path(argv[1]))
        if fresh and reason == NOTHING_REASON:
            # RED-TEAM B3: "nothing to inspect" must never read as a FRESH pass.
            print("NOTHING-TO-CHECK: " + reason)
            return 4
        print(("FRESH: " if fresh else "STALE: ") + reason)
        return 0 if fresh else 3
    if len(argv) == 1:
        return generate(Path(argv[0]))
    if not argv:
        if not sys.stdin.isatty():
            return hook_main()
        print("usage: spec_digest.py <dir> | --check <dir> | (hook mode: PostToolUse JSON on stdin)")
        return 1
    print("usage: spec_digest.py <dir> | --check <dir> | (hook mode: PostToolUse JSON on stdin)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
