"""Do two concurrent `--recent` reconciles double-append to the global index?"""
import importlib.util, io, contextlib, os, shutil, multiprocessing as mp
from pathlib import Path

import tempfile as _tf, os as _os
# setdefault, NOT mkdtemp: multiprocessing spawn re-executes this module in
# every child, so a fresh mkdtemp per process would give each one its own
# workspace and the parent would measure an empty result.
HERE = Path(_os.environ.setdefault('NOTE_TEST_DIR', _tf.mkdtemp(prefix='note-tests-')))
NOTE = r"C:/Users/Shadow/.claude/skills/spec/note.py"
PROJ = HERE / "recrace"
IDX = HERE / "recrace_idx.md"


def load():
    s = importlib.util.spec_from_file_location("nr", NOTE)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    m.GLOBAL_INDEX = IDX
    return m


def reader(_):
    m = load()
    with contextlib.redirect_stdout(io.StringIO()):
        m.cmd_recent(str(PROJ), 20)


if __name__ == "__main__":
    mp.freeze_support()
    if PROJ.exists():
        shutil.rmtree(PROJ)
    PROJ.mkdir(parents=True)
    if IDX.exists():
        IDX.unlink()
    m = load()
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(5):
            f = PROJ / f"f{i}.txt"
            f.write_text(f"change: FINDING: race probe {i}\nwhy: y\n", encoding="utf-8")
            m.cmd_note(str(PROJ), str(f))
    IDX.write_text("", encoding="utf-8")        # wipe -> all 5 need reconciling
    ps = [mp.Process(target=reader, args=(i,)) for i in range(6)]
    [p.start() for p in ps]
    [p.join() for p in ps]
    rows = [l for l in IDX.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
    ids = [r.split("|")[2].strip() for r in rows]
    print("6 concurrent --recent, 5 findings needing reconcile")
    print(f"  index rows written : {len(rows)}")
    print(f"  distinct ids       : {len(set(ids))}")
    print(f"  duplicate rows     : {len(rows) - len(set(ids))}")
    print(f"  findings LOST      : {5 - len(set(ids))}")
    if len(set(ids)) == 5 and len(rows) == 5:
        print("  VERDICT: clean")
    elif len(set(ids)) == 5:
        print("  VERDICT: DEGRADES — duplicate rows, zero loss (dedupe on read is TOCTOU)")
    else:
        print("  VERDICT: BREAKS — findings missing from the index")
