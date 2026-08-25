#!/usr/bin/env python3
"""Helper for the /spec skill -- safe file mechanics for SPEC.md logging.

Run from the project dir that holds SPEC.md. Subcommands:
  log    read a structured block (field lines) from stdin, stamp the date,
         prepend it newest-first under "## Change Log" via a lock-guarded
         atomic write, then advance the durable line-count marker. If the
         session is BOUND (see bind), the block goes to the bound spec file
         and a one-line pointer is prepended to SPEC.md.
  bind   bind this session to a specialized spec file: `bind SPEC-x.md --sid S`.
         Stored in .spec/binding-<sid>; log/status honor it. `bind --clear` unbinds.
  skip   arm a one-shot skip marker so the Stop guard releases once.
  status print the count of unlogged in-project edits (debug).

All subcommands accept `--sid <session-id>`. PASS IT ALWAYS in parallel-chat
folders: without it the active session is guessed as the one whose pending
trail was modified most recently — which cross-stamps markers when several
chats run at once (proven failure 2026-08-13). See prep-spec-system.txt.
"""
from __future__ import annotations

import datetime
import glob
import json
import os
import sys
import time
from pathlib import Path

LOCK_TIMEOUT = 5.0  # seconds, then fail open (proceed + warn)


def _norm(p: str) -> str:
    try:
        return os.path.normcase(os.path.realpath(p))
    except (OSError, ValueError):
        return os.path.normcase(os.path.abspath(p))


def _in_project(path: str, proj: str) -> bool:
    if not path:
        return False
    base = proj if proj.endswith(os.sep) else proj + os.sep
    return path == proj or path.startswith(base)


def _spec_dir(proj: str) -> Path:
    return Path(proj) / ".spec"


def _latest_session(proj: str):
    files = glob.glob(str(_spec_dir(proj) / "pending-*.jsonl"))
    if not files:
        return None
    latest = os.path.basename(max(files, key=os.path.getmtime))
    return latest[len("pending-"):-len(".jsonl")]


def _acquire_lock(proj: str):
    lock = _spec_dir(proj) / "lock"
    deadline = time.time() + LOCK_TIMEOUT
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return lock
        except FileExistsError:
            if time.time() > deadline:
                return None
            time.sleep(0.1)
        except OSError:
            return None


def _release_lock(lock):
    try:
        if lock:
            os.remove(lock)
    except OSError:
        pass


def _prepend_block(content: str, block: str) -> str:
    lines = content.splitlines(keepends=True)
    idx = None
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith("## change log"):
            idx = i
            break
    block_text = block.rstrip() + "\n\n"
    if idx is None:
        return content.rstrip() + "\n\n## Change Log\n\n" + block_text
    insert_at = idx + 1
    while insert_at < len(lines) and (
        lines[insert_at].strip().startswith("<!--") or lines[insert_at].strip() == ""
    ):
        insert_at += 1
    return "".join(lines[:insert_at]) + block_text + "".join(lines[insert_at:])


def _binding_target(proj: str, sid):
    """Return the bound spec filename for this session, or None (unbound/invalid)."""
    if not sid:
        return None
    f = _spec_dir(proj) / f"binding-{sid}"
    try:
        name = f.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not name or name == "SPEC.md":
        return None
    target = Path(proj) / name
    if not target.is_file():
        print(f"warning: bound spec '{name}' missing -- falling back to SPEC.md",
              file=sys.stderr)
        return None
    return name


def cmd_bind(proj: str, sid, args) -> int:
    spec_dir = _spec_dir(proj)
    sid = sid or _latest_session(proj)
    if not sid:
        print("bind failed: no session trail yet and no --sid given", file=sys.stderr)
        return 1
    if "--clear" in args:
        try:
            (spec_dir / f"binding-{sid}").unlink(missing_ok=True)
        except OSError as e:
            print(f"unbind failed: {e}", file=sys.stderr)
            return 1
        print(f"Session {sid} unbound (logs go to SPEC.md).")
        return 0
    names = [a for a in args[1:] if not a.startswith("--")
             and a != sid and not a.endswith(os.sep)]
    name = names[0] if names else ""
    if not name:
        print("usage: spec_tool.py bind <SPEC-file.md> [--sid S] | bind --clear [--sid S]",
              file=sys.stderr)
        return 1
    if not (Path(proj) / name).is_file():
        print(f"bind failed: {name} not found in {proj} -- create it first (INIT interview)",
              file=sys.stderr)
        return 1
    try:
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / f"binding-{sid}").write_text(name, encoding="utf-8")
    except OSError as e:
        print(f"bind failed: {e}", file=sys.stderr)
        return 1
    print(f"Session {sid} bound -> {name} (log blocks go there + pointer in SPEC.md).")
    return 0


def cmd_log(proj: str, sid_arg=None) -> int:
    # stdin is decoded with the LOCALE codepage by default (cp1252 on Windows), while every
    # read/write below pins utf-8. A block piped in as utf-8 therefore round-tripped as
    # double-encoded mojibake: an em dash arrived as three cp1252 chars and was written back
    # out as utf-8, so "--" became "a-EUR-\"". Measured 2026-08-05: 866 such sequences had
    # accumulated in one project's SPEC.md. Pin stdin to utf-8 to match the rest of the file.
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # non-reconfigurable stream (piped/redirected oddly) -> fall back to old behaviour
    raw = sys.stdin.read().strip()
    if not raw:
        print("nothing to log: no block text on stdin", file=sys.stderr)
        return 1
    spec = Path(proj) / "SPEC.md"
    if not spec.is_file():
        print("no SPEC.md here -- run /spec init first", file=sys.stderr)
        return 1

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    body = "\n".join("  " + ln.rstrip() for ln in raw.splitlines() if ln.strip())
    block = f"- date: {now}\n{body}"

    sid = sid_arg or _latest_session(proj)
    bound = _binding_target(proj, sid)
    spec_dir = _spec_dir(proj)
    lock = _acquire_lock(proj)
    warned = "" if lock else " (lock timeout -- wrote unlocked; check if parallel chats)"
    try:
        if bound:
            # Full block -> the session's own spec; one-line pointer -> shared SPEC.md.
            target = Path(proj) / bound
            content = target.read_text(encoding="utf-8")
            tmp = target.with_name(target.name + ".tmp")
            tmp.write_text(_prepend_block(content, block), encoding="utf-8")
            os.replace(str(tmp), str(target))
            title = next((ln.split(":", 1)[1].strip() for ln in raw.splitlines()
                          if ln.strip().lower().startswith("change:")), "(untitled)")
            pointer = f"- date: {now}\n  see: {bound} -- {title}"
            content = spec.read_text(encoding="utf-8")
            tmp = spec.with_name("SPEC.md.tmp")
            tmp.write_text(_prepend_block(content, pointer), encoding="utf-8")
            os.replace(str(tmp), str(spec))
        else:
            content = spec.read_text(encoding="utf-8")
            tmp = spec.with_name("SPEC.md.tmp")
            tmp.write_text(_prepend_block(content, block), encoding="utf-8")
            os.replace(str(tmp), str(spec))
        if sid:
            trail = spec_dir / f"pending-{sid}.jsonl"
            n = 0
            if trail.is_file():
                with open(trail, encoding="utf-8") as f:
                    n = sum(1 for _ in f)
            (spec_dir / f"logged-{sid}").write_text(str(n), encoding="utf-8")
    except OSError as e:
        print(f"log failed: {e}", file=sys.stderr)
        return 1
    finally:
        _release_lock(lock)
    dest = f"{bound} (+ pointer in SPEC.md)" if bound else "SPEC.md"
    print(f"Logged 1 block to {dest}{warned}.")
    return 0


def cmd_skip(proj: str, sid_arg=None) -> int:
    sid = sid_arg or _latest_session(proj) or "manual"
    spec_dir = _spec_dir(proj)
    try:
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / f"skip-{sid}").write_text("skip", encoding="utf-8")
    except OSError as e:
        print(f"skip failed: {e}", file=sys.stderr)
        return 1
    print(f"Skip armed (session {sid}). The next Stop is allowed once.")
    return 0


def cmd_status(proj: str, sid_arg=None) -> int:
    sid = sid_arg or _latest_session(proj)
    if not sid:
        print("No session trail yet -- nothing recorded.")
        return 0
    spec_dir = _spec_dir(proj)
    try:
        marker = int((spec_dir / f"logged-{sid}").read_text(encoding="utf-8").strip())
    except Exception:
        marker = 0
    trail = spec_dir / f"pending-{sid}.jsonl"
    proj_n = _norm(proj)
    count = 0
    if trail.is_file():
        with open(trail, encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                if i <= marker:
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    fact = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if fact.get("kind") == "edit" and _in_project(fact.get("target", ""), proj_n):
                    count += 1
    print(f"Session {sid}: {count} unlogged in-project edit(s).")
    return 0


def main() -> int:
    args = sys.argv[1:]
    cmd = args[0] if args else ""
    proj = os.getcwd()
    if "--dir" in args:
        i = args.index("--dir")
        if i + 1 < len(args):
            proj = args[i + 1]
    sid = None
    if "--sid" in args:
        i = args.index("--sid")
        if i + 1 < len(args):
            sid = args[i + 1]
    if cmd == "log":
        return cmd_log(proj, sid)
    if cmd == "bind":
        return cmd_bind(proj, sid, args)
    if cmd == "skip":
        return cmd_skip(proj, sid)
    if cmd == "status":
        return cmd_status(proj, sid)
    print("usage: spec_tool.py [log|bind|skip|status] [--sid SID] [--dir DIR]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
