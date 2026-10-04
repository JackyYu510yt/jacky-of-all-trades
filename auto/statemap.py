#!/usr/bin/env python3
"""statemap.py - what state is every code file in? READ-ONLY, any project.

    statemap.py <ABS project root> [--all] [--no-procs] [--json <out>]
    statemap.py <ABS project root> --why <path to one file>

WHY THIS EXISTS (2026-08-30, user directive)
--------------------------------------------
Documents rot. A project accumulates one document per day, each true when typed
and none marked stale, and the answer to "is this thing live?" becomes a pile of
plausible competing answers. On 2026-08-30 that cost a whole finished, tested
image lane: it sat on disk, unplugged, and NOT ONE of 34 documents mentioned it.
It was found by asking the machine which files the running program actually
loads, and noticing what was missing from the answer.

So this asks the machine. It reads the disk every time and cannot go stale.

THE FOUR STATES
  ON              reachable from something that actually starts: a running
                  process, a launcher script, a package.json entry
  BUILT BUT OFF   substantial code nothing reaches -- finished and unplugged.
                  THE CATEGORY THAT BITES. Look here before building anything.
  TEST / PROBE    scratch by name or location; safe to ignore
  ABANDONED       a dead copy sitting beside a live file, or parked in a
                  graveyard directory
  (THIN)          small, referenced by nothing, no entry point -- noise

REACHABILITY IS A FLOOR, NEVER A TOTAL. Runtime-built paths (a module imported
from a string assembled at run time), OS-started daemons that no launcher in the
tree names, and anything a remote machine invokes are all INVISIBLE to a static
read. A file listed BUILT BUT OFF is a candidate for investigation, never a
proven-dead file. Nothing here authorises a delete.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

CODE_EXT = {".py", ".mjs", ".js", ".bat", ".cmd", ".ps1", ".sh"}
PY_EXT = {".py"}
LAUNCHER_EXT = {".bat", ".cmd", ".ps1", ".sh"}

SKIP_DIRS = {
    "__pycache__", "node_modules", ".git", ".hg", ".svn", ".idea", ".vscode",
    "venv", ".venv", "env", ".env", "site-packages", "dist", "build", ".tox",
    "extensions", "ffmpeg", "ffmpeg6", ".mypy_cache", ".pytest_cache", "egg-info",
}

# A file whose NAME or directory says "scratch". Deliberately conservative:
# `check_*` and `monitor_*` are NOT here -- they are real tools in real projects,
# and a false TEST label hides a live file, which is the expensive direction.
TEST_PREFIX = ("test_", "tests_", "smoke_", "probe_", "poc_", "repro_",
               "scratch_", "tmp_", "temp_", "try_", "experiment_", "demo_",
               "example_", "sample_", "bench_", "debug_", "spike_")
TEST_SUFFIX = ("_test", "_tests", "_smoke", "_probe", "_poc", "_experiment",
               "_scratch", "_demo", "_bench", "_spike", ".test", ".spec")
TEST_DIRS = {"test", "tests", "_test", "_tests", "smoke", "_smoke", "probes",
             "_probes", "examples", "_examples", "scratch", "_scratch",
             "sandbox", "_sandbox", "spec", "__tests__"}

DEAD_DIRS = {"_archive", "archive", "_old", "old", "_backup", "backup", "_bak",
             "_parked", "parked", "_dead", "_dead_lane", "_quarantine",
             "quarantine", "_revert", "_deprecated", "deprecated", "_legacy",
             "legacy", "_graveyard", "_superseded", "_retired"}
DEAD_MARK = (".bak", ".old", ".orig", ".backup", ".save", ".prev")

# stem -> the stem it is a variant OF.  foo_old / foo_v2 / foo copy / foo (1)
VARIANT_RE = re.compile(
    r"^(?P<base>.+?)"
    r"(?:[ _.\-]*\(\d+\)"
    r"|[ _.\-]+(?:copy|old|new|orig|original|bak|backup|prev|previous|final|"
    r"fixed|broken|legacy|deprecated|dead|unused|v\d+|\d+))$",
    re.IGNORECASE)

# a bare string that names a script -- how spawned children are referenced
SPAWN_RE = re.compile(r"""['"]([\w./\\ -]+\.(?:py|mjs|js|bat|cmd|ps1|sh))['"]""")
JS_IMPORT_RE = re.compile(
    r"""(?:import[^'"]*from\s*|import\s*|require\s*\(\s*)['"]([^'"]+)['"]""")

SUBSTANTIAL_LINES = 40


# --------------------------------------------------------------- the file walk

def is_reparse(p: str) -> bool:
    """Junction / symlink / mount point. Never followed.

    A junction points OUTSIDE the tree being measured -- following one walks live
    data, counts the same file twice under two names, and (when the target is
    gone) raises WinError 3 mid-walk. Observed on the first live run:
    `_smoke/repointed/.../chrome_profiles` is a junction to a deleted target.
    """
    try:
        st = os.lstat(p)
    except OSError:
        return True                     # unreadable -> do not descend
    return bool(getattr(st, "st_file_attributes", 0) & 0x400)  # REPARSE_POINT


GRAVEYARDS: dict[str, int] = {}          # relpath -> files inside, not scanned


def _tree(root: Path):
    """os.walk with the skip list, junctions AND graveyards pruned.

    `Path.rglob` is deliberately not used anywhere: it descends junctions and
    raises FileNotFoundError mid-iteration on a broken one, killing the scan
    (observed on the first live run against the factory).

    A GRAVEYARD (`_archive/`, `_revert-lane/`, `_parked/`...) is counted and
    named, never enumerated. Listing its contents file-by-file put 763 rows in
    ABANDONED on the first live run and buried the dozen dead copies sitting in
    LIVE territory -- which are the only ones anyone can act on. A deliberate
    graveyard is not a finding; a corpse next to a working file is.
    """
    for dp, dn, fn in os.walk(root):
        keep = []
        for d in dn:
            full = os.path.join(dp, d)
            low = d.lower()
            if low in SKIP_DIRS or low.endswith("egg-info") or is_reparse(full):
                continue
            if low in DEAD_DIRS:
                n = sum(len(f) for _, _, f in os.walk(full))
                GRAVEYARDS[os.path.relpath(full, root).replace("\\", "/")] = n
                continue
            keep.append(d)
        dn[:] = keep
        yield dp, fn


def walk(root: Path) -> list[Path]:
    return [Path(dp) / f
            for dp, fn in _tree(root) for f in fn
            if Path(f).suffix.lower() in CODE_EXT]


def find_named(root: Path, name: str) -> list[Path]:
    return [Path(dp) / f
            for dp, fn in _tree(root) for f in fn if f.lower() == name]


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def describe(path: Path, src: str) -> str:
    """The file's own first line about itself. Never invented."""
    ext = path.suffix.lower()
    if ext in PY_EXT:
        try:
            doc = ast.get_docstring(ast.parse(src))
            if doc:
                first = next((l.strip() for l in doc.splitlines() if l.strip()), "")
                if first:
                    return first
        except (SyntaxError, ValueError, RecursionError):
            pass
    for line in src.splitlines()[:15]:
        s = line.strip()
        if not s or s.startswith("#!") or "coding:" in s:
            continue
        for mark in ("#", "//", "REM ", "::", "<#", "/*", '"""', "'''"):
            if s.upper().startswith(mark.upper()):
                s = s[len(mark):].strip(" *#/-")
                return s[:100] if s else ""
        break
    return ""


# ------------------------------------------------------------------ the graph

def build_index(files: list[Path], root: Path) -> tuple[dict, dict]:
    by_stem: dict[str, list[Path]] = {}
    by_rel: dict[str, Path] = {}
    for f in files:
        by_stem.setdefault(f.stem.lower(), []).append(f)
        by_rel[str(f.relative_to(root)).lower().replace("\\", "/")] = f
    return by_stem, by_rel


def resolve(name: str, origin: Path, by_stem: dict, by_rel: dict) -> Path | None:
    """A reference -> a file in this tree, or None. Same-directory wins."""
    name = name.strip().replace("\\", "/").lstrip("./")
    if not name:
        return None
    key = name.lower()
    if key in by_rel:
        return by_rel[key]
    stem = Path(key).stem
    cands = by_stem.get(stem)
    if not cands:
        return None
    same = [c for c in cands if c.parent == origin.parent]
    if same:
        return same[0]
    return cands[0] if len(cands) == 1 else cands[0]


def refs_of(path: Path, src: str, by_stem: dict, by_rel: dict) -> set[Path]:
    out: set[Path] = set()
    ext = path.suffix.lower()
    if ext in PY_EXT:
        try:
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        out.add(a.name.replace(".", "/"))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        out.add(node.module.replace(".", "/"))
        except (SyntaxError, ValueError, RecursionError):
            pass
    elif ext in {".mjs", ".js"}:
        out.update(m.group(1) for m in JS_IMPORT_RE.finditer(src))
    out.update(m.group(1) for m in SPAWN_RE.finditer(src))
    hits = set()
    for name in out:
        tgt = resolve(str(name), path, by_stem, by_rel)
        if tgt and tgt != path:
            hits.add(tgt)
    return hits


# ------------------------------------------------------------- entry points

def running_procs(root: Path) -> list[tuple[Path, str]]:
    """Files named on the command line of a LIVE process. The strongest signal."""
    out = []
    try:
        if sys.platform == "win32":
            cp = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 "Get-CimInstance Win32_Process | "
                 "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=45)
            rows = json.loads(cp.stdout or "[]")
            rows = rows if isinstance(rows, list) else [rows]
            procs = [(str(r.get("ProcessId", "")), r.get("CommandLine") or "")
                     for r in rows]
        else:
            cp = subprocess.run(["ps", "-eo", "pid=,args="],
                                capture_output=True, text=True, timeout=45)
            procs = [(l.split(None, 1)[0], l.split(None, 1)[1])
                     for l in cp.stdout.splitlines() if l.split(None, 1)[1:]]
    except (OSError, ValueError, subprocess.SubprocessError):
        return []
    rl = str(root).lower()
    for pid, cmd in procs:
        low = cmd.lower()
        if rl not in low:
            continue
        for m in re.finditer(r"[\w:/\\ .()'-]+?\.(?:py|mjs|js|bat|cmd|ps1|sh)", cmd):
            cand = Path(m.group(0).strip().strip("'\""))
            if cand.is_file() and rl in str(cand.resolve()).lower():
                out.append((cand.resolve(), f"pid {pid}"))
    return out


def entry_points(root: Path, files: list[Path], by_stem, by_rel,
                 use_procs: bool) -> list[tuple[Path, str]]:
    eps: dict[Path, str] = {}
    if use_procs:
        for p, why in running_procs(root):
            eps.setdefault(p, f"running ({why})")
    for f in files:                                  # a launcher IS an entry
        if f.suffix.lower() not in LAUNCHER_EXT:
            continue
        # ...unless it is itself parked. A .bat inside _archive/ starts nothing;
        # counting it dragged 100+ dead files into ON on the first live run.
        if dead_reason(f, root, {}) or is_test(f, root):
            continue
        eps.setdefault(f, "launcher")
    for pj in find_named(root, "package.json"):
        try:
            data = json.loads(read(pj) or "{}")
        except ValueError:
            continue
        cands = []
        for key in ("main", "module"):
            if isinstance(data.get(key), str):
                cands.append(data[key])
        for key in ("bin", "scripts"):
            v = data.get(key)
            if isinstance(v, dict):
                cands.extend(x for x in v.values() if isinstance(x, str))
            elif isinstance(v, str):
                cands.append(v)
        for c in cands:
            for m in re.finditer(r"[\w./\\-]+\.(?:mjs|js|py)", c):
                tgt = resolve(m.group(0), pj, by_stem, by_rel)
                if tgt:
                    eps.setdefault(tgt, "package.json")
    return sorted(eps.items(), key=lambda kv: (kv[1], str(kv[0])))


# ------------------------------------------------------------ classification

def is_test(path: Path, root: Path) -> bool:
    stem = path.stem.lower()
    if stem.startswith(TEST_PREFIX) or stem.endswith(TEST_SUFFIX):
        return True
    parts = {p.lower() for p in path.relative_to(root).parts[:-1]}
    return bool(parts & TEST_DIRS)


def dead_reason(path: Path, root: Path, on_stems: dict) -> str:
    parts = [p.lower() for p in path.relative_to(root).parts[:-1]]
    for p in parts:
        if p in DEAD_DIRS:
            return f"in {p}/"
    low = path.name.lower()
    for mark in DEAD_MARK:
        if mark in low or low.endswith("~"):
            return f"{mark} copy"
    m = VARIANT_RE.match(path.stem)
    if m:
        base = m.group("base").strip().lower()
        live = on_stems.get(base)
        if live:
            try:
                rel = live.relative_to(root)
            except ValueError:
                rel = live
            return f"variant of LIVE {rel}"
    return ""


def classify(rec: dict, root: Path, on_stems: dict) -> str:
    if rec["on"]:
        return "ON"
    reason = dead_reason(rec["path"], root, on_stems)
    if reason:
        rec["dead_reason"] = reason
        return "ABANDONED"
    if is_test(rec["path"], root):
        return "TEST/PROBE"
    if rec["lines"] < SUBSTANTIAL_LINES and not rec["importers"]:
        return "THIN"
    # THE DISTINCTION THAT MAKES THIS CATEGORY WORTH READING (fixed 2026-08-30,
    # first live run): a hand-run CLI tool has `__main__` and zero importers --
    # that is its NORMAL, healthy state, not an anomaly. Calling it "built but
    # off" put 1,347 files in the one category that is supposed to be rare, and
    # buried the real finds. An IMPORTABLE module (no `__main__`) that nothing
    # imports is the genuinely anomalous shape: written to be wired in, never
    # wired in. That is the Gemini-lane shape this tool exists to surface.
    if rec["has_main"] and not rec["importers"]:
        return "STANDALONE"
    return "BUILT-BUT-OFF" if not rec["importers"] else "THIN"


# ------------------------------------------------------------------- the scan

def scan(root: Path, use_procs: bool) -> dict:
    files = walk(root)
    by_stem, by_rel = build_index(files, root)

    src_of, recs = {}, {}
    for f in files:
        s = read(f)
        src_of[f] = s
        try:
            mtime = os.lstat(f).st_mtime
        except OSError:
            # One unreadable file must never take the whole board down: the board
            # is most needed on exactly the messy trees that contain one.
            mtime = 0.0
        desc = describe(f, s)
        recs[f] = {
            "path": f, "lines": s.count("\n") + 1 if s else 0,
            "desc": desc,
            "has_main": "__main__" in s or "if __name__" in s,
            "has_doc": bool(desc),
            "mtime": mtime,
            "importers": [], "on": False, "why_on": "", "dead_reason": "",
        }

    graph = {f: refs_of(f, src_of[f], by_stem, by_rel) for f in files}
    for f, tgts in graph.items():
        for t in tgts:
            if t in recs:
                recs[t]["importers"].append(f)

    eps = entry_points(root, files, by_stem, by_rel, use_procs)
    stack = [(p, w) for p, w in eps if p in recs]
    seen = set()
    while stack:
        p, why = stack.pop()
        if p in seen:
            continue
        seen.add(p)
        recs[p]["on"] = True
        recs[p]["why_on"] = why
        for t in graph.get(p, ()):
            if t not in seen:
                stack.append((t, f"via {p.name}"))

    on_stems = {p.stem.lower(): p for p in seen}
    for f, r in recs.items():
        r["state"] = classify(r, root, on_stems)

    # THE RANKING SIGNAL. A dark file that pulls in OTHER dark files is not a
    # loose offcut -- it is the head of a whole unplugged subsystem, and that is
    # the shape worth seeing first. `gemini_lane.py` scores 6: an orchestrator
    # composing six modules, reached by nothing. Recency alone buried it.
    for f, r in recs.items():
        r["off_imports"] = sum(1 for t in graph.get(f, ())
                               if t in recs and not recs[t]["on"])
    return {"root": root, "recs": recs, "eps": eps, "graph": graph,
            "files": files}


# ------------------------------------------------------------------ rendering

def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p)


def age(mtime: float) -> str:
    d = (time.time() - mtime) / 86400
    return f"{int(d)}d" if d >= 1 else "today"


def render(res: dict, show_all: bool) -> None:
    root, recs, eps = res["root"], res["recs"], res["eps"]
    print(f"STATE BOARD - {root}")
    print(f"read live at {time.strftime('%Y-%m-%d %H:%M')}   READ-ONLY, nothing moved")
    print("=" * 100)

    if not eps:
        print("!! NO ENTRY POINTS FOUND - no running process, no launcher, no")
        print("!! package.json entry names a file in this tree. Everything below")
        print("!! is therefore unreachable BY MEASUREMENT FAILURE, not by fact.")
        print("!! Treat the whole board as UNKNOWN until an entry point is named.")
    else:
        print(f"entry points ({len(eps)}) - everything ON is reachable from these:")
        for p, why in eps[:25]:
            print(f"   [{why[:22]:<22}] {rel(p, root)}")
        if len(eps) > 25:
            print(f"   ... and {len(eps)-25} more")
    print("-" * 100)

    order = ["ON", "BUILT-BUT-OFF", "STANDALONE", "TEST/PROBE", "ABANDONED",
             "THIN"]
    blurb = {
        "ON": "the running system loads these",
        "BUILT-BUT-OFF": "finished code nothing loads  <-- LOOK HERE BEFORE BUILDING",
        "STANDALONE": "run by hand: has __main__, imported by nobody (normal for a tool)",
        "TEST/PROBE": "scratch by name or folder; safe to ignore",
        "ABANDONED": "a dead copy beside a live file, or parked in a graveyard",
        "THIN": "small, nothing references them, no entry point",
    }
    caps = {"ON": 0 if show_all else 15,
            "BUILT-BUT-OFF": 0 if show_all else 12,
            "STANDALONE": 0 if show_all else 8,
            "TEST/PROBE": 0 if show_all else 8,
            "ABANDONED": 0 if show_all else 12, "THIN": 0 if show_all else 5}

    groups: dict[str, list] = {k: [] for k in order}
    for r in recs.values():
        groups[r["state"]].append(r)

    for state in order:
        if state == "BUILT-BUT-OFF":
            # subsystem heads first, then recency -- never recency alone
            rows = sorted(groups[state],
                          key=lambda r: (-r["off_imports"], -r["mtime"]))
        else:
            rows = sorted(groups[state], key=lambda r: -r["mtime"])
        if not rows:
            continue
        print(f"\n{state}   {len(rows)} files   - {blurb[state]}")
        if state == "BUILT-BUT-OFF":
            per_top: dict[str, int] = {}
            for r in rows:
                top = rel(r["path"], root).split("/")[0]
                per_top[top] = per_top.get(top, 0) + 1
            spread = "  ".join(f"{k}:{v}" for k, v in
                               sorted(per_top.items(), key=lambda kv: -kv[1])[:8])
            print(f"   by folder:  {spread}")
            print("   ranked by how many OTHER dark files each one pulls in "
                  "(a subsystem head, not an offcut):")
        cap = caps[state] or len(rows)
        for r in rows[:cap]:
            print(f"   {rel(r['path'], root)[:66]:<66} {r['desc'][:60]}")
            if state == "BUILT-BUT-OFF":
                tests = [i for i in r["importers"] if is_test(i, root)]
                print(f"       pulls in {r['off_imports']} other dark file(s)"
                      f" · {r['lines']} lines · importers {len(r['importers'])}"
                      f" · tests naming it {len(tests)}"
                      f" · touched {age(r['mtime'])}")
            elif state == "ABANDONED" and r["dead_reason"]:
                print(f"       {r['dead_reason']}")
        if cap < len(rows):
            print(f"   ... and {len(rows)-cap} more   (--all to list every one)")

    if GRAVEYARDS:
        tot = sum(GRAVEYARDS.values())
        print(f"\nGRAVEYARDS   {len(GRAVEYARDS)} dirs, {tot} files - counted, "
              f"NOT scanned (deliberate parking, not a finding)")
        for d, n in sorted(GRAVEYARDS.items(), key=lambda kv: -kv[1])[:8]:
            print(f"   {d[:70]:<70} {n} files")

    print("\n" + "-" * 100)
    print("  ".join(f"{k}:{len(groups[k])}" for k in order)
          + f"   TOTAL:{len(recs)}")
    print("REACHABILITY IS A FLOOR. Runtime-built paths, OS-started daemons and")
    print("remote invocations are invisible to a static read. BUILT-BUT-OFF means")
    print("'nothing here reaches it' - it is a lead to investigate, never a")
    print("licence to delete.")


def render_why(res: dict, target: str) -> int:
    root, recs = res["root"], res["recs"]
    t = Path(target)
    if not t.is_absolute():
        cands = [p for p in recs if p.name.lower() == t.name.lower()]
    else:
        cands = [p for p in recs if p == t.resolve()]
    if not cands:
        print(f"not a code file under {root}: {target}")
        return 1
    for p in cands:
        r = recs[p]
        print(f"\n{rel(p, root)}")
        print(f"  state ........ {r['state']}")
        if r["on"]:
            print(f"  reached ...... {r['why_on']}")
        else:
            print("  reached ...... NO - no entry point reaches it")
        if r["dead_reason"]:
            print(f"  dead because . {r['dead_reason']}")
        print(f"  size ......... {r['lines']} lines"
              f"{', has __main__' if r['has_main'] else ''}")
        print(f"  touched ...... {age(r['mtime'])} ago")
        print(f"  description .. {r['desc'] or '(the file says nothing about itself)'}")
        imps = r["importers"]
        print(f"  imported by .. {len(imps)}")
        for i in imps[:12]:
            print(f"       {'ON ' if recs[i]['on'] else 'off'} {rel(i, root)}")
        outs = res["graph"].get(p, ())
        print(f"  it imports ... {len(outs)}")
        for o in sorted(outs, key=lambda x: str(x))[:12]:
            print(f"       {'ON ' if recs[o]['on'] else 'off'} {rel(o, root)}")
    return 0


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 0
    root = Path(args[0])
    if not root.is_absolute():
        raise ValueError(f"project root must be ABSOLUTE, got {args[0]!r}")
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")

    res = scan(root, use_procs="--no-procs" not in argv)

    if "--why" in argv:
        i = argv.index("--why")
        if i + 1 >= len(argv):
            raise ValueError("--why needs a file path")
        return render_why(res, argv[i + 1])

    render(res, show_all="--all" in argv)

    if "--json" in argv:
        out = Path(argv[argv.index("--json") + 1])
        payload = {
            "root": str(root), "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "entry_points": [[rel(p, root), w] for p, w in res["eps"]],
            "files": [
                {"path": rel(r["path"], root), "state": r["state"],
                 "desc": r["desc"], "lines": r["lines"],
                 "importers": len(r["importers"]), "mtime": r["mtime"],
                 "dead_reason": r["dead_reason"]}
                for r in res["recs"].values()],
        }
        out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        print(f"\njson -> {out}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, OSError) as exc:
        print(f"statemap failed: {exc}", file=sys.stderr)
        sys.exit(1)
