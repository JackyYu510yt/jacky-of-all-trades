"""Open (or reuse) a NAMED Chrome profile and prove which window is really that profile.

Mirrors adspower-open's verify step: nothing continues unless the window is verified.

  python chrome_profile.py list
  python chrome_profile.py open "<profile name | directory e.g. Profile 1>" [--url https://studio.youtube.com/]

Verify rule: Chrome shares ONE process for every profile, so (unlike AdsPower) the data folder can't
find the window. Instead each Chrome window's toolbar profile button carries the profile's own name
(read through UI Automation, not from the page), and that must equal the requested profile EXACTLY
("Account Checks" can never pass for "Account Checks 2"). Candidate windows are the ones with that
label; if more than one is open the caller must say which (--hwnd), never guessed.

Prints JSON {hwnd, profile, directory, window_title, already_open, verified:true} or exits 2 with
'VERIFY FAILED: <what was found>'. No automation flags, no debugging port: a plain launch.
"""
import argparse, json, os, re, subprocess, sys, time

SC = os.path.join(os.path.expanduser("~"), ".claude", "skills", "google-login", "screen_control.ps1")
LOCAL_STATE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Local State")
CHROME = next((p for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe") if os.path.exists(p)), None)

UIA = r'''
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$out=@()
foreach($h in %HWNDS%){
  try{
    $root=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$h)
    $cond=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)
    $names=@(); foreach($b in $root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$cond)){ $names+=$b.Current.Name }
    $out+=[pscustomobject]@{hwnd=$h;buttons=$names}
  }catch{}
}
$out | ConvertTo-Json -Depth 4 -Compress
'''


def ps(cmd):
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout


def profiles():
    j = json.load(open(LOCAL_STATE, encoding="utf-8"))
    return {d: v.get("name", d) for d, v in j["profile"]["info_cache"].items()}


def resolve(q):
    ps_ = profiles()
    exact = [d for d, n in ps_.items() if n == q or d == q]
    if len(exact) == 1:
        return exact[0], ps_[exact[0]]
    part = [d for d, n in ps_.items() if q.lower() in n.lower()]
    if len(part) == 1:
        return part[0], ps_[part[0]]
    sys.exit(f"VERIFY FAILED: profile '{q}' matches {[ps_[d] for d in (exact or part)] or 'nothing'}; profiles: {list(ps_.values())}")


def chrome_windows():
    out = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", SC, "list"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    return [(int(m.group(1)), m.group(2)) for m in re.finditer(r"^(\d+) \| (.*Google Chrome)\s*$", out, re.M)]


def window_profiles(wins):
    if not wins:
        return {}
    js = ps(UIA.replace("%HWNDS%", ",".join(str(h) for h, _ in wins)))
    if not js.strip():
        return {}
    data = json.loads(js)
    data = data if isinstance(data, list) else [data]
    names = set(profiles().values())
    res = {}
    for d in data:
        b = d["buttons"] if isinstance(d["buttons"], list) else [d["buttons"]]
        hit = [n for n in b if n in names]
        res[int(d["hwnd"])] = hit[0] if len(hit) == 1 else None
    return res


def find(name):
    wins = chrome_windows()
    wp = window_profiles(wins)
    return [(h, t) for h, t in wins if wp.get(h) == name]


def cmd_open(a):
    d, name = resolve(a.profile)
    if a.hwnd:
        m = [(h, t) for h, t in chrome_windows() if h == a.hwnd]
        if not m or window_profiles(m).get(a.hwnd) != name:
            sys.exit(f"VERIFY FAILED: hwnd {a.hwnd} is not a window of profile '{name}'")
        cand, already = m, True
    else:
        cand = find(name)
        already = bool(cand)
        if not cand:
            if not CHROME:
                sys.exit("VERIFY FAILED: chrome.exe not found")
            subprocess.Popen([CHROME, f"--profile-directory={d}", a.url or "https://studio.youtube.com/"])
            for _ in range(20):
                time.sleep(1)
                cand = find(name)
                if cand:
                    break
    if not cand:
        sys.exit(f"VERIFY FAILED: opened profile '{name}' ({d}) but no Chrome window shows that profile name")
    if len(cand) > 1:
        sys.exit(f"VERIFY FAILED: profile '{name}' has {len(cand)} windows {cand}; close extras or pass --hwnd")
    h, title = cand[0]
    print(json.dumps({"hwnd": h, "profile": name, "directory": d, "window_title": title,
                      "already_open": already, "verified": True}))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="c", required=True)
    sp.add_parser("list")
    o = sp.add_parser("open"); o.add_argument("profile"); o.add_argument("--url"); o.add_argument("--hwnd", type=int)
    a = ap.parse_args()
    if a.c == "list":
        for d, n in profiles().items():
            print(f"{d} | {n}")
    else:
        cmd_open(a)


if __name__ == "__main__":
    main()
