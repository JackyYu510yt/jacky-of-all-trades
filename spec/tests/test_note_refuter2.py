"""Regression tests for refuter round 2: BLOCKER 1, BLOCKER 2, C2, C3."""
import contextlib, importlib.util, io, os, shutil, sys
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
    s = importlib.util.spec_from_file_location("n3", NOTE_PATH)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    m.GLOBAL_INDEX = Path(idx)
    return m

def fresh(name):
    d = HERE / name
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)
    return d

def wf(d, text, name="in.txt"):
    p = d / name; p.write_text(text, encoding="utf-8"); return str(p)

# ---- BLOCKER 1: a pre-existing foreign FINDINGS.md must not brick the project ----
d = fresh("b1"); note = load(d / "idx.md")
(d / "FINDINGS.md").write_text(
    "# Findings\n\n- the API is slow on Tuesdays\n- remember to purge the cache\n",
    encoding="utf-8")
err = io.StringIO(); rc = None
try:
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        rc = note.cmd_note(str(d), wf(d, "change: FINDING: coexists with foreign text\nwhy: y\n"))
    wrote = True
except Exception as exc:
    wrote = False; rc = repr(exc)
check("foreign FINDINGS.md: writing still WORKS (was: permanent denial of service)",
      wrote and rc == 0, str(rc))
check("foreign FINDINGS.md: the foreign lines are LEFT INTACT",
      "the API is slow on Tuesdays" in (d / "FINDINGS.md").read_text(encoding="utf-8"))
check("foreign FINDINGS.md: the skip is announced on stderr, not silent",
      "not note.py entries" in err.getvalue(), err.getvalue().strip()[:60])
out = io.StringIO(); rc2 = None
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        rc2 = note.cmd_recent(str(d), 20)
    read_ok = True
except Exception as exc:
    read_ok = False; rc2 = repr(exc)
check("foreign FINDINGS.md: reading still WORKS and shows the new finding",
      read_ok and rc2 == 0 and "coexists with foreign text" in out.getvalue(), str(rc2))

# ---- BLOCKER 2: retract -> refile -> retract must mark the LIVE entry ----
d = fresh("b2"); note = load(d / "idx.md")
body = "change: FINDING: a lesson filed, retracted, refiled, retracted\nwhy: y\n"
with contextlib.redirect_stdout(io.StringIO()):
    note.cmd_note(str(d), wf(d, body)); eid = note._sha8(body)
    note.cmd_retract(eid, str(d), "first retraction")
    note.cmd_note(str(d), wf(d, body))          # refile
    note.cmd_retract(eid, str(d), "second retraction")
raw = (d / "FINDINGS.md").read_text(encoding="utf-8").splitlines()
hdrs = [l for l in raw if l.startswith("## ") and f"id: {eid}" in l]
marks = [h.count("[RETRACTED by") for h in hdrs]
check("retract/refile/retract: each copy carries exactly ONE mark "
      "(was: one corpse got two, the live one got none)",
      len(hdrs) == 2 and marks == [1, 1], f"headers={len(hdrs)} marks={marks}")
with contextlib.redirect_stdout(io.StringIO()):
    live = [e for e in note._read_entries(d / "FINDINGS.md") if not e["retracted_by"]]
check("retract/refile/retract: reader and raw file AGREE (0 live)", len(live) == 0,
      f"{len(live)} live")

# ---- C3: a reconciled index row keeps the entry's ORIGINAL timestamp ----
d = fresh("c3"); idx = d / "idx.md"; note = load(idx)
with contextlib.redirect_stdout(io.StringIO()):
    note.cmd_note(str(d), wf(d, "change: FINDING: timestamp fidelity\nwhy: y\n"))
rec = d / "FINDINGS.md"
orig_ts = note._read_entries(rec)[0]["ts"]
rec.write_text(rec.read_text(encoding="utf-8").replace(orig_ts, "2026-01-02 09:15"),
               encoding="utf-8")
idx.write_text("", encoding="utf-8")
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    note.cmd_recent(str(d), 20)
row = [l for l in idx.read_text(encoding="utf-8").splitlines() if l.startswith("- ")][0]
check("reconciled index row keeps the ORIGINAL timestamp (was: stamped repair time)",
      "2026-01-02 09:15" in row, row.split("|")[0].strip())

# ---- C2: a read-only index must not break the READ ----
d = fresh("c2"); idx = d / "idx.md"; note = load(idx)
with contextlib.redirect_stdout(io.StringIO()):
    note.cmd_note(str(d), wf(d, "change: FINDING: read must survive a locked index\nwhy: y\n"))
idx.write_text("", encoding="utf-8")
os.system(f'attrib +R "{idx}" >nul 2>&1')
out, err = io.StringIO(), io.StringIO(); rc = None
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = note.cmd_recent(str(d), 20)
    ok = rc == 0 and "read must survive" in out.getvalue()
except Exception:
    ok = False
os.system(f'attrib -R "{idx}" >nul 2>&1')
check("read-only index: --recent still RETURNS the findings (was: exit 1, nothing)",
      ok, "deferred: " + ("yes" if "deferred" in err.getvalue() else "no"))

print()
bad = [r for r in results if not r[1]]
print(f"REGRESSION3: {len(results)-len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)
