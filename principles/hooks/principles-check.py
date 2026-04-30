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

import json
import re
import sys

CLAIM_RE = re.compile(
    r"\b(done|fixed|verified|works|tested|confirmed|complete)\b",
    re.IGNORECASE,
)
PRINCIPLES_RE = re.compile(
    r"principles|P4 checkpoint|P2 \+ P4 checkpoint",
    re.IGNORECASE,
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

    if PRINCIPLES_RE.search(text):
        return 0

    if not CLAIM_RE.search(text):
        return 0

    full = transcript_text(transcript_path)
    reminder = REMINDER_P4 if GOAL_RE.search(full) else REMINDER_P2_P4

    json.dump({"decision": "block", "reason": reminder}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
