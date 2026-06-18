"""
page_diag.py — headed Selenium page/state diagnostic tool (proxy-free).

Opens a URL on a chosen Chrome profile, captures a full forensic bundle
(DOM, innerText, URL/title/handles, console log, network/HAR, status+headers,
screenshot) on the initial page, clicks a target, handles any new tab,
captures the same bundle on the result, then builds a detection signature +
classifies the resulting state.

Network/console come from Chrome's DevTools logs (no proxy, no selenium-wire).

Usage (startup gate prompts for anything not given on the CLI):
  python page_diag.py --url https://example.com --click "css=a" \
      --profile fresh
  python page_diag.py --url ... --click "xpath=//button[1]" \
      --profile "Default" --error-text "Something went wrong" --yes

Run `python page_diag.py --help` for all flags.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    InvalidSelectorException,
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException,
)

LOG = logging.getLogger("page_diag")

# Phrases that flag a generic error state when no --error-text is supplied.
ERROR_DICTIONARY = [
    "something went wrong",
    "try again later",
    "try again",
    "an error occurred",
    "page not found",
    "temporarily unavailable",
    "service unavailable",
    "access denied",
    "forbidden",
    "unexpected error",
    "we're sorry",
    "this page isn't working",
    "internal server error",
]

CLICK_BY = {
    "css": By.CSS_SELECTOR,
    "xpath": By.XPATH,
    "link_text": By.LINK_TEXT,
    "partial_link_text": By.PARTIAL_LINK_TEXT,
}

WAIT_TIMEOUT = 15           # explicit wait for the click target (s)
QUIESCE_TIMEOUT = 8.0       # cap on the network-quiet wait (s)
QUIESCE_STABLE = 0.75       # how long resource count must hold steady (s)


# ───────────────────────── helpers ─────────────────────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path: Path, data) -> None:
    """Write bytes or str to a temp file, then rename — never a half file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    mode, enc = ("wb", None) if isinstance(data, (bytes, bytearray)) else ("w", "utf-8")
    with open(tmp, mode, encoding=enc) as fh:
        fh.write(data)
    os.replace(tmp, path)


def _setup_logging(run_dir: Path) -> None:
    LOG.setLevel(logging.INFO)
    LOG.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    LOG.addHandler(sh)
    fh = logging.FileHandler(run_dir / "run.log", encoding="utf-8")
    fh.setFormatter(fmt)
    LOG.addHandler(fh)


# ───────────────────── startup-gate config ─────────────────────
@dataclass
class ClickTarget:
    type: str          # css | xpath | link_text | partial_link_text
    value: str


@dataclass
class RunConfig:
    url: str
    click: ClickTarget
    user_data_dir: Optional[str]      # parent "User Data" (None for fresh)
    profile_directory: Optional[str]  # subfolder e.g. "Default" (None=fresh)
    copy_profile: bool
    error_text: Optional[str]
    auto_accept: bool


def list_chrome_profiles(user_data_dir: Path):
    """Read Local State -> [(folder, display_name)]. SAFE."""
    out = []
    local_state = Path(user_data_dir) / "Local State"
    try:
        data = json.loads(local_state.read_text(encoding="utf-8"))
        cache = data.get("profile", {}).get("info_cache", {})
        for folder, info in cache.items():
            out.append((folder, info.get("name", folder)))
    except Exception as e:  # noqa: BLE001 - listing is best-effort
        LOG.warning("could not read profiles from %s: %s", local_state, e)
    return sorted(out, key=lambda t: t[0])


def _default_user_data_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    return Path(local) / "Google" / "Chrome" / "User Data"


def _parse_click(raw: str) -> ClickTarget:
    """Accept 'css=...', 'xpath=...', 'link_text=...', or a bare CSS selector."""
    if "=" in raw:
        prefix, _, value = raw.partition("=")
        key = prefix.strip().lower()
        if key in CLICK_BY:
            return ClickTarget(key, value)
    return ClickTarget("css", raw)


def resolve_run_config(argv=None) -> RunConfig:
    """Startup gate. CLI flags pre-fill; prompt only for what's missing.
    Runs ONCE before the engine. RISKY (only place the user is asked)."""
    p = argparse.ArgumentParser(description="Headed Selenium page diagnostic.")
    p.add_argument("--url")
    p.add_argument("--click", help="css=..., xpath=..., link_text=..., or bare CSS")
    p.add_argument("--profile", help='profile folder (e.g. "Default"), "fresh", '
                                      'or "list" to print and exit')
    p.add_argument("--user-data-dir", help="override the Chrome User Data parent dir")
    p.add_argument("--copy-profile", action="store_true",
                   help="copy the profile to a temp dir (don't require Chrome closed)")
    p.add_argument("--error-text", help="known error phrase to anchor the signature")
    p.add_argument("--yes", action="store_true",
                   help="auto-accept the proposed signature (non-interactive)")
    a = p.parse_args(argv)

    udd_parent = Path(a.user_data_dir) if a.user_data_dir else _default_user_data_dir()

    if a.profile == "list":
        for folder, name in list_chrome_profiles(udd_parent):
            print(f"  {folder!r:18} -> {name}")
        sys.exit(0)

    # URL
    url = a.url or input("URL to open: ").strip()
    if not url:
        sys.exit("No URL given.")
    if not re.match(r"^[a-zA-Z]+://", url):
        url = "https://" + url

    # Click target
    click_raw = a.click or input("What to click (css=… / xpath=… / link_text=…): ").strip()
    if not click_raw:
        sys.exit("No click target given.")
    click = _parse_click(click_raw)

    # Profile
    profile = a.profile
    if profile is None:
        profiles = list_chrome_profiles(udd_parent)
        print("Available Chrome profiles:")
        print("  fresh  -> brand-new throwaway profile (no cookies/login)")
        for folder, name in profiles:
            print(f"  {folder!r:18} -> {name}")
        profile = input('Profile folder or "fresh": ').strip() or "fresh"

    if profile.lower() == "fresh":
        user_data_dir = None
        profile_directory = None
    else:
        user_data_dir = str(udd_parent)
        profile_directory = profile

    # Error text (optional)
    error_text = a.error_text
    if error_text is None and not a.yes:
        et = input("Known error text (blank to auto-scrape): ").strip()
        error_text = et or None

    return RunConfig(
        url=url,
        click=click,
        user_data_dir=user_data_dir,
        profile_directory=profile_directory,
        copy_profile=a.copy_profile,
        error_text=error_text,
        auto_accept=a.yes,
    )


# ───────────────────── engine: preflight + driver ─────────────────────
class PreflightError(RuntimeError):
    pass


def _chrome_running() -> bool:
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/NH"],
            capture_output=True, text=True, timeout=10,
        ).stdout.lower()
        return "chrome.exe" in out
    except Exception:  # noqa: BLE001 - if we can't tell, don't block
        return False


def preflight_checks(config: RunConfig) -> Path:
    """Verify env, resolve the profile, make the run dir. ENGINE. RISKY."""
    # selenium sanity
    import selenium
    if selenium.__version__ != "4.15.2":
        LOG.warning("selenium %s (designed for 4.15.2)", selenium.__version__)

    # profile lock handling
    if config.profile_directory and not config.copy_profile and _chrome_running():
        raise PreflightError(
            "Chrome appears to be running. Close ALL Chrome windows to reuse "
            f"profile {config.profile_directory!r}, or re-run with --copy-profile."
        )

    if config.profile_directory and config.copy_profile:
        src = Path(config.user_data_dir) / config.profile_directory
        dst_parent = Path.cwd() / "page-diag-runs" / "_profile_copy"
        if dst_parent.exists():
            shutil.rmtree(dst_parent, ignore_errors=True)
        dst = dst_parent / config.profile_directory
        LOG.info("copying profile %s -> %s", src, dst)
        # Skip giant/volatile caches and tolerate files Chrome holds locked —
        # a few skipped files must never crash the copy.
        skip_dirs = {"Cache", "Code Cache", "GPUCache", "Service Worker",
                     "GrShaderCache", "ShaderCache", "DawnGraphiteCache",
                     "DawnWebGPUCache", "component_crx_cache"}
        skipped = []

        def _copy(s, d):
            try:
                shutil.copy2(s, d)
            except (OSError, PermissionError) as e:  # locked DB, etc.
                skipped.append(f"{Path(s).name}: {type(e).__name__}")

        try:
            shutil.copytree(
                src, dst, dirs_exist_ok=True, copy_function=_copy,
                ignore=shutil.ignore_patterns(*skip_dirs))
        except shutil.Error as e:  # copytree aggregates per-file failures
            skipped.append(f"copytree: {len(e.args[0]) if e.args else '?'} files")
        if skipped:
            LOG.warning("profile copy skipped %d locked/cache item(s): %s",
                        len(skipped), skipped[:5])
        # strip lock files so Chrome will open the copy
        for lock in dst_parent.rglob("Singleton*"):
            try:
                lock.unlink()
            except OSError:
                pass
        config.user_data_dir = str(dst_parent)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path.cwd() / "page-diag-runs" / f"{stamp}-{secrets.token_hex(2)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def make_driver(config: RunConfig):
    """Build a headed Chrome with perf+browser logging. ENGINE. RISKY."""
    opts = Options()
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
    opts.add_experimental_option("perfLoggingPrefs", {"enableNetwork": True})
    opts.add_argument("--window-size=1366,900")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    if config.user_data_dir:
        opts.add_argument(f"--user-data-dir={config.user_data_dir}")
        if config.profile_directory:
            opts.add_argument(f"--profile-directory={config.profile_directory}")

    last = None
    for attempt in range(3):
        try:
            driver = webdriver.Chrome(options=opts)
            # precondition: perf log must be live
            driver.get("data:text/html,<title>preflight</title>")
            driver.get_log("performance")
            LOG.info("driver up (attempt %d)", attempt + 1)
            return driver
        except WebDriverException as e:
            last = e
            LOG.warning("driver start failed (attempt %d): %s", attempt + 1, e)
            time.sleep(1.5 * (attempt + 1))
    raise PreflightError(f"could not start Chrome driver: {last}")


# ───────────────────── engine: capture ─────────────────────
def _headers_to_har(headers: dict):
    return [{"name": str(k), "value": str(v)} for k, v in (headers or {}).items()]


def _build_network(perf_logs):
    """Assemble {har, xhr} from Chrome DevTools Network.* events."""
    reqs, order = {}, []
    for raw in perf_logs:
        try:
            msg = json.loads(raw["message"])["message"]
        except Exception:
            continue
        method = msg.get("method", "")
        params = msg.get("params", {})
        rid = params.get("requestId")
        if not rid:
            continue
        if method == "Network.requestWillBeSent":
            req = params.get("request", {})
            if rid not in reqs:
                order.append(rid)
                reqs[rid] = {"request": None, "response": None, "type": None,
                             "wallTime": params.get("wallTime"), "size": None}
            reqs[rid]["request"] = {
                "method": req.get("method", ""),
                "url": req.get("url", ""),
                "headers": req.get("headers", {}),
            }
            reqs[rid]["type"] = params.get("type") or reqs[rid]["type"]
        elif method == "Network.responseReceived" and rid in reqs:
            resp = params.get("response", {})
            reqs[rid]["response"] = {
                "status": resp.get("status"),
                "statusText": resp.get("statusText", ""),
                "headers": resp.get("headers", {}),
                "mimeType": resp.get("mimeType", ""),
            }
            reqs[rid]["type"] = params.get("type") or reqs[rid]["type"]
        elif method == "Network.loadingFinished" and rid in reqs:
            reqs[rid]["size"] = params.get("encodedDataLength")

    entries, xhr = [], []
    for rid in order:
        r = reqs[rid]
        if not r["request"]:
            continue
        started = ""
        if r["wallTime"]:
            try:
                started = datetime.fromtimestamp(r["wallTime"], timezone.utc).isoformat()
            except Exception:
                started = ""
        resp = r["response"] or {}
        entries.append({
            "startedDateTime": started,
            "time": 0,
            "request": {
                "method": r["request"]["method"],
                "url": r["request"]["url"],
                "httpVersion": "HTTP/1.1",
                "cookies": [],
                "headers": _headers_to_har(r["request"]["headers"]),
                "queryString": [],
                "headersSize": -1,
                "bodySize": -1,
            },
            "response": {
                "status": resp.get("status", 0),
                "statusText": resp.get("statusText", ""),
                "httpVersion": "HTTP/1.1",
                "cookies": [],
                "headers": _headers_to_har(resp.get("headers", {})),
                "content": {"size": r["size"] or 0, "mimeType": resp.get("mimeType", "")},
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": r["size"] or -1,
            },
            "cache": {},
            "timings": {"send": 0, "wait": 0, "receive": 0},
        })
        if (r["type"] or "") in ("XHR", "Fetch"):
            xhr.append({
                "url": r["request"]["url"],
                "method": r["request"]["method"],
                "type": r["type"],
                "status": resp.get("status"),
                "mimeType": resp.get("mimeType", ""),
                "response_headers": resp.get("headers", {}),
            })

    har = {"log": {"version": "1.2",
                   "creator": {"name": "page_diag", "version": "1.0"},
                   "entries": entries}}
    return har, xhr


def _wait_network_quiet(driver) -> None:
    """Wait until resource-timing count holds steady, capped. ENGINE."""
    deadline = time.monotonic() + QUIESCE_TIMEOUT
    last_count, stable_since = -1, time.monotonic()
    while time.monotonic() < deadline:
        try:
            count = driver.execute_script(
                "return performance.getEntriesByType('resource').length;")
        except WebDriverException:
            return
        if count != last_count:
            last_count, stable_since = count, time.monotonic()
        elif time.monotonic() - stable_since >= QUIESCE_STABLE:
            return
        time.sleep(0.15)


def capture_page(driver, label: str, dest_dir: Path) -> dict:
    """THE evidence kit. Writes 7 artifacts; never lets one miss sink the rest.
    ENGINE. RISKY."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    errors = {}

    def guard(name, fn):
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - per-artifact isolation is the point
            errors[name] = f"{type(e).__name__}: {e}"
            LOG.warning("[%s] capture '%s' failed: %s", label, name, e)

    _wait_network_quiet(driver)

    guard("screenshot.png",
          lambda: driver.save_screenshot(str(dest_dir / "screenshot.png")))
    guard("page.html",
          lambda: atomic_write(dest_dir / "page.html",
                               driver.execute_script(
                                   "return document.documentElement.outerHTML;") or ""))
    guard("body.txt",
          lambda: atomic_write(dest_dir / "body.txt",
                               driver.execute_script(
                                   "return document.body ? document.body.innerText : '';") or ""))

    meta = {"label": label, "captured_at": _now_iso()}
    guard("meta.json", lambda: meta.update({
        "url": driver.current_url,
        "title": driver.title,
        "window_handles": list(driver.window_handles),
        "active_handle": driver.current_window_handle,
        "handle_count": len(driver.window_handles),
    }))

    console = []
    guard("console.json", lambda: console.extend(driver.get_log("browser")))
    if "console.json" not in errors:
        atomic_write(dest_dir / "console.json", json.dumps(console, indent=2))

    har_holder = {}
    guard("network", lambda: har_holder.update(
        zip(("har", "xhr"), _build_network(driver.get_log("performance")))))
    if "network" not in errors:
        atomic_write(dest_dir / "network.har", json.dumps(har_holder["har"], indent=2))
        atomic_write(dest_dir / "xhr.json", json.dumps(har_holder["xhr"], indent=2))

    meta["console_error_count"] = sum(1 for e in console if e.get("level") == "SEVERE")
    meta["network_entry_count"] = len(har_holder.get("har", {}).get("log", {}).get("entries", []))
    meta["xhr_count"] = len(har_holder.get("xhr", []))
    meta["capture_errors"] = errors
    atomic_write(dest_dir / "meta.json", json.dumps(meta, indent=2))

    # M3: completeness sentinel — only after every artifact was attempted
    atomic_write(dest_dir / "_complete", _now_iso())
    LOG.info("[%s] captured -> %s (errors: %d, net: %d, console_sev: %d)",
             label, dest_dir, len(errors), meta["network_entry_count"],
             meta["console_error_count"])
    return meta


# ───────────────────── engine: interaction ─────────────────────
def wait_and_click(driver, target: ClickTarget) -> dict:
    """Explicit-wait for the element, click, detect a new tab. ENGINE. RISKY."""
    by = CLICK_BY.get(target.type)
    if by is None:
        raise ValueError(f"unknown click target type: {target.type}")
    handles_before = set(driver.window_handles)
    try:
        el = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((by, target.value)))
    except TimeoutException:
        LOG.error("click target never became clickable: %s=%s", target.type, target.value)
        return {"clicked": False, "reason": "timeout",
                "new_tab": False, "handles_after": list(handles_before)}
    except InvalidSelectorException as e:
        LOG.error("invalid selector: %s", e)
        return {"clicked": False, "reason": "invalid_selector",
                "new_tab": False, "handles_after": list(handles_before)}

    try:
        el.click()
    except (ElementClickInterceptedException, WebDriverException) as e:
        LOG.warning("native click failed (%s); trying JS click", type(e).__name__)
        driver.execute_script("arguments[0].click();", el)

    time.sleep(1.0)  # let a new tab register
    handles_after = set(driver.window_handles)
    new = handles_after - handles_before
    LOG.info("clicked %s=%s | new_tab=%s", target.type, target.value, bool(new))
    return {"clicked": True, "reason": "ok", "new_tab": bool(new),
            "new_handles": list(new), "handles_after": list(handles_after)}


def handle_new_tab(driver, click_result: dict) -> str:
    """If a new tab opened, switch to it. ENGINE. RISKY."""
    new = click_result.get("new_handles") or []
    if new:
        driver.switch_to.window(new[0])
        LOG.info("switched to new tab %s", new[0])
    return driver.current_window_handle


# ───────────────────── engine: fingerprint ─────────────────────
def _normalize_url(url: str) -> str:
    return re.sub(r"[?#].*$", "", url or "")


_HASH_RE = re.compile(r"(^|[-_])([0-9a-f]{6,}|[A-Za-z0-9]{8,})($|[-_])")


def _looks_hashed(token: str) -> bool:
    return bool(re.search(r"[0-9a-f]{6,}", token)) or token.startswith("css-") \
        or bool(re.match(r"^[A-Za-z]{1,3}[0-9A-Za-z]{5,}$", token)) and any(c.isdigit() for c in token)


def _find_dom_marker(driver, phrases) -> Optional[str]:
    """Prefer a stable id > data-/aria attr > text-anchored xpath. ENGINE."""
    # 1) an element containing an error phrase, with a stable id
    for phrase in phrases:
        try:
            els = driver.find_elements(
                By.XPATH,
                f"//*[contains(translate(normalize-space(.),"
                f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
                f"{_xpath_literal(phrase.lower())})]")
        except Exception:
            els = []
        for el in els[:5]:
            try:
                eid = el.get_attribute("id")
                if eid and not _looks_hashed(eid):
                    return f"css=#{eid}"
                for attr in ("data-testid", "data-test", "role", "aria-label", "name"):
                    val = el.get_attribute(attr)
                    if val and not _looks_hashed(val):
                        return f'css=[{attr}="{val}"]'
            except Exception:
                continue
    # 2) text-anchored xpath fallback
    if phrases:
        return f"xpath=//*[contains(normalize-space(.), {_xpath_literal(phrases[0])})]"
    return None


def _xpath_literal(s: str) -> str:
    """Safely quote a string for XPath (handles embedded quotes)."""
    if '"' not in s:
        return f'"{s}"'
    if "'" not in s:
        return f"'{s}'"
    parts = s.split('"')
    return "concat(" + ', \'"\', '.join(f'"{p}"' for p in parts) + ")"


def build_signature(step_dir: Path, driver, error_text: Optional[str]) -> dict:
    """Build URL+text+DOM fingerprint of the captured state. ENGINE. RISKY."""
    step_dir = Path(step_dir)
    meta = json.loads((step_dir / "meta.json").read_text(encoding="utf-8"))
    body = ""
    try:
        body = (step_dir / "body.txt").read_text(encoding="utf-8")
    except OSError:
        pass
    body_low = body.lower()

    if error_text:
        text_markers = [error_text]
        source = "user"
    else:
        text_markers = [p for p in ERROR_DICTIONARY if p in body_low]
        source = "dictionary"

    # Only anchor on markers that ACTUALLY appear on the captured page.
    present = [m for m in text_markers if m.lower() in body_low]
    if error_text and not present:
        LOG.warning("error_text %r not found on result page — signature will be weak",
                    error_text)

    dom_marker = None
    if present:
        try:
            dom_marker = _find_dom_marker(driver, present)
        except Exception as e:  # noqa: BLE001
            LOG.warning("dom marker search failed: %s", e)

    confidence = "high"
    if not present and not dom_marker:
        confidence = "low"
    elif not present or not dom_marker:
        confidence = "medium"

    sig = {
        "label": "error_state" if text_markers else "unknown_state",
        "url_pattern": _normalize_url(meta.get("url", "")),
        "text_markers": text_markers,
        "dom_marker": dom_marker,
        "source": source,
        "confidence": confidence,
        "built_at": _now_iso(),
    }
    LOG.info("signature: label=%s conf=%s text=%d dom=%s",
             sig["label"], confidence, len(text_markers), bool(dom_marker))
    return sig


def extract_state(source) -> dict:
    """Read {url,text,dom-presence-checker} from a live driver OR a saved dir.
    ENGINE/SAFE adapter."""
    if isinstance(source, (str, Path)):
        d = Path(source)
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        try:
            text = (d / "body.txt").read_text(encoding="utf-8")
        except OSError:
            text = ""
        html = ""
        try:
            html = (d / "page.html").read_text(encoding="utf-8")
        except OSError:
            pass
        return {"url": meta.get("url", ""), "text": text, "_html": html, "_driver": None}
    return {"url": source.current_url,
            "text": source.execute_script(
                "return document.body ? document.body.innerText : '';") or "",
            "_html": "", "_driver": source}


def _dom_marker_present(state: dict, dom_marker: Optional[str]) -> bool:
    if not dom_marker:
        return False
    kind, _, value = dom_marker.partition("=")
    drv = state.get("_driver")
    if drv is not None:
        by = By.CSS_SELECTOR if kind == "css" else By.XPATH
        try:
            return len(drv.find_elements(by, value)) > 0
        except Exception:
            return False
    # offline: best-effort substring check against saved HTML
    html = state.get("_html", "")
    if kind == "css" and value.startswith("#"):
        return f'id="{value[1:]}"' in html
    return False


def score_state(state: dict, signatures, threshold: float = 0.5) -> dict:
    """Pure scorer: which known signature does this state match? ENGINE. RISKY."""
    text_low = (state.get("text") or "").lower()
    url_norm = _normalize_url(state.get("url", ""))
    best = {"label": "unknown", "score": 0.0, "matched_factors": [], "is_match": False}
    for sig in signatures:
        factors, score = [], 0.0
        if sig.get("url_pattern") and sig["url_pattern"] == url_norm:
            score += 0.34
            factors.append("url")
        markers = sig.get("text_markers") or []
        if markers and all(m.lower() in text_low for m in markers):
            score += 0.33
            factors.append("text")
        elif markers and any(m.lower() in text_low for m in markers):
            score += 0.20
            factors.append("text_partial")
        if _dom_marker_present(state, sig.get("dom_marker")):
            score += 0.33
            factors.append("dom")
        if score > best["score"]:
            best = {"label": sig.get("label", "unknown"), "score": round(score, 3),
                    "matched_factors": factors, "is_match": score >= threshold}
    LOG.info("classify: label=%s score=%.2f factors=%s",
             best["label"], best["score"], best["matched_factors"])
    return best


# ───────────────────── orchestration ─────────────────────
def run_diagnosis(config: RunConfig, run_dir: Path) -> dict:
    """Ordered engine: driver -> capture -> click -> capture -> fingerprint."""
    summary = {"config": {**asdict(config)}, "run_dir": str(run_dir),
               "started_at": _now_iso()}
    driver = make_driver(config)
    try:
        LOG.info("opening %s", config.url)
        driver.get(config.url)
        cap1 = capture_page(driver, "step1-initial", run_dir / "step1-initial")
        summary["step1"] = cap1

        click_result = wait_and_click(driver, config.click)
        summary["click"] = click_result

        origin_handle = driver.current_window_handle
        handle_new_tab(driver, click_result)

        cap2 = capture_page(driver, "step2-after-click", run_dir / "step2-after-click")
        summary["step2"] = cap2

        # snapshot the original tab too if a new tab opened
        if click_result.get("new_tab"):
            try:
                driver.switch_to.window(origin_handle)
                capture_page(driver, "origin-tab",
                             run_dir / "step2-after-click" / "origin-tab")
            except WebDriverException as e:
                LOG.warning("origin-tab snapshot failed: %s", e)

        # fingerprint the result (switch back to the result tab)
        new = click_result.get("new_handles") or []
        if new:
            driver.switch_to.window(new[0])
        sig = build_signature(run_dir / "step2-after-click", driver, config.error_text)

        # confirm gate (post-engine; skipped with --yes or when error_text given)
        if not config.auto_accept and not config.error_text and sys.stdin.isatty():
            print("\nProposed signature:")
            print(json.dumps(sig, indent=2))
            edit = input("Accept? [Y/n, or type replacement error text]: ").strip()
            if edit and edit.lower() not in ("y", "yes"):
                sig["text_markers"] = [edit]
                sig["source"] = "user_confirmed"
        atomic_write(run_dir / "signature.json", json.dumps(sig, indent=2))

        state = extract_state(driver)
        result = score_state(state, [sig])
        atomic_write(run_dir / "classification.json", json.dumps(result, indent=2))
        summary["signature"] = sig
        summary["classification"] = result
        summary["status"] = "DONE"
    finally:
        summary["ended_at"] = _now_iso()
        atomic_write(run_dir / "run-summary.json", json.dumps(summary, indent=2))
        try:
            driver.quit()
        except Exception as e:  # noqa: BLE001 - never let quit mask a real error
            LOG.warning("driver.quit failed: %s", e)
    return summary


def main(argv=None) -> int:
    config = resolve_run_config(argv)
    try:
        run_dir = preflight_checks(config)
    except PreflightError as e:
        print(f"PREFLIGHT FAILED: {e}", file=sys.stderr)
        return 2
    _setup_logging(run_dir)
    LOG.info("run dir: %s", run_dir)
    try:
        summary = run_diagnosis(config, run_dir)
    except Exception as e:  # noqa: BLE001 - top-level guard, state already on disk
        LOG.exception("run failed: %s", e)
        return 1
    print(f"\nDONE -> {run_dir}")
    print(f"  state: {summary.get('classification', {}).get('label')} "
          f"(score {summary.get('classification', {}).get('score')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
