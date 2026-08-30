import os, sys, shutil, time, importlib.util, multiprocessing as mp
import tempfile as _tf, os as _os
HERE = _os.environ.setdefault('NOTE_TEST_DIR', _tf.mkdtemp(prefix='note-tests-'))
PROJ = os.path.join(HERE, "conc")
NOTE = r"C:/Users/Shadow/.claude/skills/spec/note.py"
N_PROC, N_EACH = 6, 150

def load():
    spec = importlib.util.spec_from_file_location("note", NOTE)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.GLOBAL_INDEX = __import__('pathlib').Path(HERE)/'conc_index.md'
    return m

def worker(w):
    note = load()
    for i in range(N_EACH):
        p = os.path.join(PROJ, f"f_{w}_{i}.txt")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(f"change: FINDING: worker {w} finding {i}\nwhy: concurrency probe\n")
        try:
            note.cmd_note(PROJ, p)
        except Exception as e:
            print(f"WORKER {w} ERR {e}", file=sys.stderr)
        os.remove(p)

def run(label):
    if os.path.isdir(PROJ): shutil.rmtree(PROJ)
    os.makedirs(PROJ)
    ix = os.path.join(HERE, "conc_index.md")
    if os.path.exists(ix): os.remove(ix)
    t0 = time.time()
    ps = [mp.Process(target=worker, args=(w,)) for w in range(N_PROC)]
    [p.start() for p in ps]; [p.join() for p in ps]
    dur = time.time() - t0
    rec = os.path.join(PROJ, "FINDINGS.md")
    with open(rec, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    idx = os.path.join(HERE, "conc_index.md")
    with open(idx, encoding="utf-8", errors="replace") as fh:
        irows = [l for l in fh.read().splitlines() if l.startswith("- ")]
    iids = set(r.split("|")[2].strip() for r in irows if len(r.split("|")) > 3)
    heads = [l for l in lines if l.startswith("## ") and " id: " in l]
    bodies = [l for l in lines if l.startswith("change: FINDING: worker")]
    expected = N_PROC * N_EACH
    ok = (len(heads) == expected and len(bodies) == expected
          and len(iids) == expected)
    print(f"{label}: expected={expected} record={len(heads)} bodies={len(bodies)} "
          f"INDEX={len(iids)} LOST={expected-len(heads)} "
          f"{'PASS' if ok else 'FAIL'}  ({dur:.1f}s)")
    return ok

if __name__ == "__main__":
    mp.freeze_support()
    r1 = run("run 1")
    r2 = run("run 2")
    print("GATE:", "PASS (both runs 900/900)" if (r1 and r2) else "FAIL")
    sys.exit(0 if (r1 and r2) else 1)
