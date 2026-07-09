"""Stop hook: nudge Claude to consult /principles when declaring victory.

Reads the Stop-hook JSON payload on stdin, finds the last assistant message in
the transcript, and if it contains claim-words (done/fixed/verified/etc.)
without already engaging with principles, emits a blocking-decision JSON so
Claude is forced to verify before truly stopping.

Two reminder modes:
  - REMINDER_P4    : conversation contains an end goal + success condition
                     somewhere — nudge for the P4 audit only.
  - REMINDER_P2_P4 : conversation has no observable goal / success condition
                     stated — claim is unverifiable. Force P2 (state goal +
                     conditions) AND P4 (audit) before declaring done.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

# After this many CONSECUTIVE identical blocks from the same session, the
# hook gives up and passes through. Prevents infinite "DONE. → P4 checkpoint
# → DONE. → ..." loops when the assistant can't (or won't) find the escape
# pattern. The nudge has been delivered; further blocks just waste tokens.
MAX_CONSECUTIVE_BLOCKS = 3
STATE_DIR = Path.home() / ".claude" / "state"

CLAIM_RE = re.compile(
    r"\b(done|fixed|verified|works|tested|confirmed|complete)\b",
    re.IGNORECASE,
)
PRINCIPLES_RE = re.compile(
    # Match "P4 checkpoint" verbatim AND any P4/P2 verdict header like
    # "P4 — DONE", "P4 - PARTIAL", "P2 + P4: BLOCKED", "**P4 — UNCLEAR**".
    # Without this broader pattern, every "P4 — STATE" reply re-triggers
    # the hook because the prior verdict didn't match the strict literal.
    r"principles|P[24](?:\s*\+\s*P4)?\s*[—\-:]\s*(?:DONE|PARTIAL|BLOCKED|UNCLEAR)|P4 checkpoint|P2 \+ P4 checkpoint",
    re.IGNORECASE,
)
# A reply that already contains a Done:/Next: verdict block has done the
# audit work the hook is meant to enforce — don't double-prompt for it.
VERDICT_BLOCK_RE = re.compile(
    r"\bDone:.*?\bNext:",
    re.IGNORECASE | re.DOTALL,
)
GOAL_RE = re.compile(
    r"\b("
    r"end goal|success condition|success criteria|"
    r"done when|done means|"
    r"verify by|verified by|verify check|"
    r"MUST hold|must-hold|"
    r"task:|goal:|objective:|"
    r"acceptance criteria|"
    r"test_[a-z0-9_]+\.py passes|"
    r"exit 0|exits 0|"
    r"observable check"
    r")\b",
    re.IGNORECASE,
)

REMINDER_P4 = "P4 checkpoint."
REMINDER_P2_P4 = (
    "P2 + P4 checkpoint — no observable end goal or success condition was "
    "stated in this conversation. State the end goal as one observable "
    "sentence and a checkable success condition (a command exit, a file, "
    "a test pass, a metric threshold), then audit current state vs the "
    "goal before declaring done."
)


def last_assistant_text(transcript_path: str) -> str:
    try:
        with open(transcript_path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return ""

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "assistant":
            continue
        content = (entry.get("message") or {}).get("content") or []
        if isinstance(content, str):
            return content
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return " ".join(parts)
    return ""


def transcript_text(transcript_path: str) -> str:
    """Concatenate all user + assistant text from the transcript."""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return ""

    parts: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") not in ("user", "assistant"):
            continue
        content = (entry.get("message") or {}).get("content") or []
        if isinstance(content, str):
            parts.append(content)
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
    return " ".join(parts)


def _session_key(payload: dict, transcript_path: str) -> str:
    """Stable per-session key for the streak counter."""
    sid = payload.get("session_id") or transcript_path
    return hashlib.sha1(sid.encode("utf-8", "ignore")).hexdigest()[:16]


def _load_streak(key: str) -> tuple[str, int]:
    """Return (last_reminder, count) for this session, or ("", 0)."""
    f = STATE_DIR / f"principles-streak-{key}.json"
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return data.get("reminder", ""), int(data.get("count", 0))
    except (OSError, json.JSONDecodeError, ValueError):
        return "", 0


def _save_streak(key: str, reminder: str, count: int) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        f = STATE_DIR / f"principles-streak-{key}.json"
        f.write_text(json.dumps({"reminder": reminder, "count": count}),
                     encoding="utf-8")
    except OSError:
        pass


def _reset_streak(key: str) -> None:
    try:
        (STATE_DIR / f"principles-streak-{key}.json").unlink()
    except (OSError, FileNotFoundError):
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    transcript_path = payload.get("transcript_path")
    if not transcript_path:
        return 0

    text = last_assistant_text(transcript_path)
    if not text:
        return 0

    key = _session_key(payload, transcript_path)

    if PRINCIPLES_RE.search(text) or VERDICT_BLOCK_RE.search(text):
        _reset_streak(key)
        return 0

    if not CLAIM_RE.search(text):
        _reset_streak(key)
        return 0

    full = transcript_text(transcript_path)
    reminder = REMINDER_P4 if GOAL_RE.search(full) else REMINDER_P2_P4

    # Consecutive-block cap. If we've already blocked with this exact
    # reminder MAX_CONSECUTIVE_BLOCKS times in a row, the assistant is
    # stuck — stop blocking and let the turn through.
    last_reminder, count = _load_streak(key)
    if last_reminder == reminder and count >= MAX_CONSECUTIVE_BLOCKS:
        _reset_streak(key)
        return 0

    new_count = count + 1 if last_reminder == reminder else 1
    _save_streak(key, reminder, new_count)

    json.dump({"decision": "block", "reason": reminder}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
