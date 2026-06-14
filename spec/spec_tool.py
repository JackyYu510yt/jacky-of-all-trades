#!/usr/bin/env python3
"""Helper for the /spec skill -- safe file mechanics for SPEC.md logging.

Run from the project dir that holds SPEC.md. Subcommands:
  log    read a structured block (field lines) from stdin, stamp the date,
         prepend it newest-first under "## Change Log" via a lock-guarded
         atomic write, then advance the durable line-count marker.
  skip   arm a one-shot skip marker so the Stop guard releases once.
  status print the count of unlogged in-project edits (debug).

Keeping the lock / atomic-write / marker logic here (tested Python) instead of
in skill prose means the guard/collector invariants hold deterministically.
The active session is the one whose pending trail was modified most recently
(you log right after editing, so that's this chat). See prep-spec-system.txt.
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


def cmd_log(proj: str) -> int:
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

    sid = _latest_session(proj)
    spec_dir = _spec_dir(proj)
    lock = _acquire_lock(proj)
    warned = "" if lock else " (lock timeout -- wrote unlocked; check if parallel chats)"
    try:
        content = spec.read_text(encoding="utf-8")
        new = _prepend_block(content, block)
        tmp = spec.with_name("SPEC.md.tmp")
        tmp.write_text(new, encoding="utf-8")
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
    print(f"Logged 1 block to SPEC.md{warned}.")
    return 0


def cmd_skip(proj: str) -> int:
    sid = _latest_session(proj) or "manual"
    spec_dir = _spec_dir(proj)
    try:
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / f"skip-{sid}").write_text("skip", encoding="utf-8")
    except OSError as e:
        print(f"skip failed: {e}", file=sys.stderr)
        return 1
    print(f"Skip armed (session {sid}). The next Stop is allowed once.")
    return 0


def cmd_status(proj: str) -> int:
    sid = _latest_session(proj)
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
    if cmd == "log":
        return cmd_log(proj)
    if cmd == "skip":
        return cmd_skip(proj)
    if cmd == "status":
        return cmd_status(proj)
    print("usage: spec_tool.py [log|skip|status] [--dir DIR]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
