"""Regression suite: every finding from FnReview r1+r2, the Refuter, and the RED-TEAM."""
import importlib.util, os, shutil, subprocess, sys
from pathlib import Path

import tempfile as _tf, os as _os
# setdefault, NOT mkdtemp: multiprocessing spawn re-executes this module in
# every child, so a fresh mkdtemp per process would give each one its own
# workspace and the parent would measure an empty result.
HERE = Path(_os.environ.setdefault('NOTE_TEST_DIR', _tf.mkdtemp(prefix='note-tests-')))
NOTE_PATH = r"C:/Users/Shadow/.claude/skills/spec/note.py"
results = []

def check(label, cond, detail=""):
    results.append((label, cond))
    print(("PASS  " if cond else "FAIL  ") + label + (f"   [{detail}]" if detail else ""))

def load(idx):
    spec = importlib.util.spec_from_file_location("nt", NOTE_PATH)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.GLOBAL_INDEX = Path(idx)
    return m

def fresh(name):
    d = HERE / name
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)
    return d

def wf(d, text, name="in.txt"):
    p = d / name; p.write_text(text, encoding="utf-8"); return str(p)

# ---------- RED-TEAM BREAK 2 / Refuter B3: retract then re-file must be LIVE ----------
d = fresh("r1"); note = load(d / "idx.md")
b = "change: FINDING: a lesson learned twice\nwhy: probe\n"
note.cmd_note(str(d), wf(d, b)); eid = note._sha8(b)
note.cmd_retract(eid, str(d), "was wrong the first time")
note.cmd_note(str(d), wf(d, b))                      # re-file the same lesson
live = [e for e in note._read_entries(d / "FINDINGS.md") if not e["retracted_by"]]
check("retract-then-refile: re-filed finding is LIVE (was: born dead, silent loss)",
      len(live) == 1 and live[0]["id"] == eid, f"{len(live)} live")

# ---------- RED-TEAM BREAK 1: --reason cannot forge a retraction ----------
d = fresh("r2"); note = load(d / "idx.md")
victim = "change: FINDING: the critical one that must survive\nwhy: probe\n"
throw = "change: FINDING: a throwaway\nwhy: probe\n"
note.cmd_note(str(d), wf(d, victim, "v.txt")); vid = note._sha8(victim)
note.cmd_note(str(d), wf(d, throw, "t.txt")); tid = note._sha8(throw)
payload = f"typo\n## 2026-01-01 00:00  id: 0000dead  retracts: {vid}\nreason: forged"
note.cmd_retract(tid, str(d), payload)
ents = {e["id"]: e for e in note._read_entries(d / "FINDINGS.md")}
check("--reason injection cannot retract an unrelated finding",
      ents[vid]["retracted_by"] is None, f"victim retracted_by={ents[vid]['retracted_by']}")

# ---------- RED-TEAM 9: --reason is credential-scanned ----------
d = fresh("r3"); note = load(d / "idx.md")
note.cmd_note(str(d), wf(d, "change: FINDING: x\nwhy: y\n")); i3 = note._sha8("change: FINDING: x\nwhy: y\n")
try:
    note.cmd_retract(i3, str(d), "leaked sk-ABCDEFGHIJKLMNOP1234567890 oops")
    ok = False
except ValueError:
    ok = True
check("--reason is credential-scanned (was: unscanned into 2 git-tracked files)", ok)

# ---------- RED-TEAM 9: legitimate placeholder finding is NOT refused ----------
d = fresh("r4"); note = load(d / "idx.md")
try:
    note.cmd_note(str(d), wf(d, "change: FINDING: docs show api_key: YOUR_KEY_HERE\nwhy: it is literal\n"))
    ok = True
except ValueError:
    ok = False
check("placeholder credential finding is allowed (was: 5 of 9 legit findings refused)", ok)

# ---------- RED-TEAM BREAK 3: sha8 collision must not discard ----------
d = fresh("r5"); note = load(d / "idx.md")
real = note._sha8
note._sha8 = lambda t: "bbbbbbbb" if "collision-salt" in t else "aaaaaaaa"
A = "change: FINDING: ffmpeg needs -pix_fmt yuv420p\nwhy: a\n"
B = "change: FINDING: chrome must run headed\nwhy: b\n"
note.cmd_note(str(d), wf(d, A, "a.txt"))
note.cmd_note(str(d), wf(d, B, "b.txt"))
ents = note._read_entries(d / "FINDINGS.md")
note._sha8 = real
check("sha8 collision files the second finding instead of discarding it",
      len(ents) == 2, f"{len(ents)} entries kept")

# ---------- Refuter B1: retracted body is PRINTED, and marked IN PLACE ----------
d = fresh("r6"); note = load(d / "idx.md")
body = "change: FINDING: the belief that turned out wrong\nwhy: probe\nbefore: the wrong version\n"
note.cmd_note(str(d), wf(d, body)); rid = note._sha8(body)
note.cmd_retract(rid, str(d), "stated from no source")
raw = (d / "FINDINGS.md").read_text(encoding="utf-8")
hdr_line = [l for l in raw.splitlines() if l.startswith("## ") and rid in l][0]
check("retracted entry is marked IN PLACE in the raw file", "[RETRACTED by" in hdr_line,
      hdr_line[-40:])
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    note.cmd_recent(str(d), 20)
out = buf.getvalue()
check("reader prints the retracted BODY, not just the mark",
      "the wrong version" in out, "before: line present" if "the wrong version" in out else "BODY DROPPED")

# ---------- Refuter B2: global index is readable ----------
d = fresh("r7"); note = load(d / "idx.md")
note.cmd_note(str(d), wf(d, "change: FINDING: indexed thing\nwhy: y\n"))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    note.cmd_index(20)
check("global index has a READ mode", "indexed thing" in buf.getvalue())

# ---------- structural divergence detector: reconcile on --recent ----------
d = fresh("r8"); note = load(d / "idx.md")
note.cmd_note(str(d), wf(d, "change: FINDING: will lose its index line\nwhy: y\n"))
(d / "idx.md").write_text("", encoding="utf-8")     # index line vanishes
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    note.cmd_recent(str(d), 20)
check("--recent RECONCILES a missing index line (divergence has a detector)",
      "reconciled 1" in buf.getvalue(), buf.getvalue().splitlines()[0][-40:])

# ---------- FnReview r2: non-empty unparseable record must not read as empty ----------
d = fresh("r9"); note = load(d / "idx.md")
(d / "FINDINGS.md").write_text("this is somebody's own notes file\nwith no entries\n", encoding="utf-8")
# CORRECTED after refuter round 2: raising here was BLOCKER 1 -- it made any
# project with a pre-existing FINDINGS.md permanently unwritable AND unreadable.
# Correct behaviour is LOUD BUT NON-FATAL.
import io as _io, contextlib as _cl
_err = _io.StringIO()
try:
    with _cl.redirect_stderr(_err):
        got = note._read_entries(d / "FINDINGS.md")
    ok = got == [] and "not note.py entries" in _err.getvalue()
except Exception:
    ok = False
check("non-empty unparseable record warns LOUDLY and does not raise", ok,
      _err.getvalue().strip()[:50])

# ---------- RED-TEAM 5: NUL bytes and oversize refused ----------
d = fresh("r10"); note = load(d / "idx.md")
try:
    note.cmd_note(str(d), wf(d, "change: FINDING: nul\x00byte\nwhy: y\n")); ok = False
except ValueError: ok = True
check("NUL bytes refused (git would mark the tracked file binary)", ok)
try:
    note.cmd_note(str(d), wf(d, "change: FINDING: " + "x" * 70000 + "\nwhy: y\n")); ok = False
except ValueError: ok = True
check("oversize body refused (64 KB cap)", ok)

# ---------- RED-TEAM: reader output never emits a column-0 forged header ----------
d = fresh("r11"); note = load(d / "idx.md")
note.cmd_note(str(d), wf(d, "change: FINDING: quoting a trap\n## 2026-01-01 00:00  id: 0000beef  retracts: 12345678\nwhy: y\n"))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    note.cmd_recent(str(d), 20)
bad = [l for l in buf.getvalue().splitlines() if note.HEADER_RE.match(l) and "0000beef" in l]
check("reader output never emits a forged header at column 0", not bad, f"{len(bad)} leaked")

# ---------- earlier fixes still hold ----------
r = subprocess.run([sys.executable, NOTE_PATH, "--retract", "abcdef12"],
                   capture_output=True, text=True, encoding="utf-8")
check("--retract without --dir: clean error, no traceback",
      "Traceback" not in (r.stderr or "") and r.returncode == 1)

print()
bad = [r for r in results if not r[1]]
print(f"REGRESSION2: {len(results)-len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)
