"""Smoke + edge test for the SPEC.md system hooks and helper."""
import json, os, subprocess, sys, tempfile, shutil
from pathlib import Path

PY = sys.executable
HOOKS = r"C:\Users\Shadow\.claude\hooks"
COLLECT = os.path.join(HOOKS, "spec-collect.py")
GUARD = os.path.join(HOOKS, "spec-guard.py")
TOOL = r"C:\Users\Shadow\.claude\skills\spec\spec_tool.py"
STATE = Path(os.path.expanduser("~")) / ".claude" / "state"

passed, failed = 0, 0
def check(name, cond):
    global passed, failed
    if cond:
        passed += 1; print(f"  PASS  {name}")
    else:
        failed += 1; print(f"  FAIL  {name}")

def run(script, payload, extra=None):
    args = [PY, script] + (extra or [])
    p = subprocess.run(args, input=json.dumps(payload).encode("utf-8"),
                       capture_output=True)
    return p.returncode, p.stdout.decode("utf-8","replace"), p.stderr.decode("utf-8","replace")

def run_tool(args, stdin_text="", cwd=None):
    p = subprocess.run([PY, TOOL] + args, input=stdin_text.encode("utf-8"),
                       capture_output=True, cwd=cwd)
    return p.returncode, p.stdout.decode("utf-8","replace"), p.stderr.decode("utf-8","replace")

SPEC_TEMPLATE = "# T — Spec\n\n## Goal\ng\n\n---\n\n## Change Log\n<!-- newest first -->\n"

def new_project(name="proj"):
    base = tempfile.mkdtemp()
    proj = os.path.join(base, name)
    os.makedirs(proj)
    Path(proj, "SPEC.md").write_text(SPEC_TEMPLATE, encoding="utf-8")
    return base, proj

def pending_lines(proj, sid):
    f = Path(proj, ".spec", f"pending-{sid}.jsonl")
    return f.read_text(encoding="utf-8").strip().splitlines() if f.is_file() else []

cleanup_dirs, cleanup_sids = [], []

print("== spec-collect ==")
base, proj = new_project(); cleanup_dirs.append(base)
sid = "testA"; cleanup_sids.append(sid)
# 1 in-project edit
run(COLLECT, {"tool_name":"Edit","session_id":sid,"cwd":proj,
              "tool_input":{"file_path":os.path.join(proj,"a.py")}})
ln = pending_lines(proj, sid)
check("edit recorded (1 line)", len(ln)==1 and json.loads(ln[0])["kind"]=="edit")
# bash context
run(COLLECT, {"tool_name":"Bash","session_id":sid,"cwd":proj,
              "tool_input":{"command":"ls -la"}})
ln = pending_lines(proj, sid)
check("bash recorded as context (2 lines)", len(ln)==2 and json.loads(ln[1])["kind"]=="context")
# read ignored
run(COLLECT, {"tool_name":"Read","session_id":sid,"cwd":proj,
              "tool_input":{"file_path":os.path.join(proj,"a.py")}})
check("read ignored (still 2 lines)", len(pending_lines(proj,sid))==2)
# no SPEC.md -> no-op
b2, _ = tempfile.mkdtemp(), None; cleanup_dirs.append(b2)
run(COLLECT, {"tool_name":"Edit","session_id":sid,"cwd":b2,
              "tool_input":{"file_path":os.path.join(b2,"x.py")}})
check("no SPEC.md -> no .spec dir", not Path(b2,".spec").exists())

print("== spec-guard ==")
# unlogged in-project edit -> block
rc,_,err = run(GUARD, {"session_id":sid,"cwd":proj})
check("blocks on unlogged edit (rc=2)", rc==2 and "unlogged" in err)
# stop_hook_active -> release
rc,_,_ = run(GUARD, {"session_id":sid,"cwd":proj,"stop_hook_active":True})
check("stop_hook_active releases (rc=0)", rc==0)

print("== spec_tool log + marker ==")
rc,out,err = run_tool(["log","--dir",proj], "change: add a.py\nwhy: testing the system\n")
spec_txt = Path(proj,"SPEC.md").read_text(encoding="utf-8")
marker = Path(proj,".spec",f"logged-{sid}").read_text(encoding="utf-8").strip()
check("log rc=0", rc==0)
check("block prepended with date+change", "date:" in spec_txt and "add a.py" in spec_txt)
check("block is under Change Log header",
      spec_txt.index("## Change Log") < spec_txt.index("add a.py"))
check("marker advanced to line count (2)", marker=="2")
# guard now allows
rc,_,_ = run(GUARD, {"session_id":sid,"cwd":proj})
check("guard allows after log (rc=0)", rc==0)
# new edit after marker -> block again
run(COLLECT, {"tool_name":"Edit","session_id":sid,"cwd":proj,
              "tool_input":{"file_path":os.path.join(proj,"b.py")}})
rc,_,_ = run(GUARD, {"session_id":sid,"cwd":proj})
check("new edit after marker blocks (rc=2)", rc==2)

print("== out-of-project edit ==")
base3, proj3 = new_project(); cleanup_dirs.append(base3)
sid3="testB"; cleanup_sids.append(sid3)
run(COLLECT, {"tool_name":"Edit","session_id":sid3,"cwd":proj3,
              "tool_input":{"file_path":r"C:\Windows\System32\nope.py"}})
rc,_,_ = run(GUARD, {"session_id":sid3,"cwd":proj3})
check("out-of-project edit not counted (rc=0)", rc==0)

print("== sibling-dir trap ==")
basS = tempfile.mkdtemp(); cleanup_dirs.append(basS)
projS = os.path.join(basS,"proj"); backup = os.path.join(basS,"proj-backup")
os.makedirs(projS); os.makedirs(backup)
Path(projS,"SPEC.md").write_text(SPEC_TEMPLATE, encoding="utf-8")
sidS="testC"; cleanup_sids.append(sidS)
run(COLLECT, {"tool_name":"Edit","session_id":sidS,"cwd":projS,
              "tool_input":{"file_path":os.path.join(backup,"x.py")}})
rc,_,_ = run(GUARD, {"session_id":sidS,"cwd":projS})
check("sibling proj-backup not counted as in-project (rc=0)", rc==0)

print("== skip escape hatch ==")
# proj still has unlogged b.py
rc,out,_ = run_tool(["skip","--dir",proj], "")
check("skip arms marker", rc==0 and Path(proj,".spec",f"skip-{sid}").is_file())
rc,_,_ = run(GUARD, {"session_id":sid,"cwd":proj})
check("guard releases on skip (rc=0)", rc==0)
check("skip marker consumed", not Path(proj,".spec",f"skip-{sid}").is_file())

# cleanup
for d in cleanup_dirs:
    shutil.rmtree(d, ignore_errors=True)
for s in cleanup_sids + [sid]:
    try: (STATE / f"spec-guard-streak-{s}.json").unlink()
    except OSError: pass

print(f"\n== RESULT: {passed} passed, {failed} failed ==")
sys.exit(1 if failed else 0)
