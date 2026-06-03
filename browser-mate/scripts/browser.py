#!/usr/bin/env python3
"""browser-mate — non-destructive Chrome automation with configurable profiles.

Launches (or REUSES) a dedicated debug Chrome instance per named profile, each
with its own --user-data-dir and --remote-debugging-port, COEXISTING with the
user's main browser. It NEVER quits or kills the user's browser — that is the
whole reason this skill exists.

Subcommands:
  browser.py <profile>          ensure the profile's debug instance is up; print PORT
  browser.py launch <profile>   same as above (explicit)
  browser.py list               list configured profiles
  browser.py status [profile]   show up/down for one or all profiles
  browser.py stop <profile>     gracefully stop ONLY our instance (SIGTERM, never the user's)

Config: ~/.config/browser-mate/profiles.json  (created from the bundled example on
first run). Each profile: {binary, user_data_dir, port, default_url?}.

Security: the debug port binds to 127.0.0.1 only (Chrome default) and CDP has NO
auth — anyone local can drive it. Use on trusted machines only. user_data_dir MUST
be a dedicated dir, never the user's real Chrome profile.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

CONFIG = os.path.expanduser(os.environ.get("BROWSER_MATE_CONFIG",
                                           "~/.config/browser-mate/profiles.json"))
HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(os.path.dirname(HERE), "assets", "profiles.example.json")

# Dirs we must never point a profile at (the user's real browsers).
_FORBIDDEN = [os.path.expanduser(p) for p in (
    "~/Library/Application Support/Google/Chrome",
    "~/Library/Application Support/Google/Chrome Beta",
    "~/Library/Application Support/Google/Chrome Canary",
    "~/Library/Application Support/Chromium",
)]


def die(msg, code=1):
    print(f"browser-mate: {msg}", file=sys.stderr)
    sys.exit(code)


def load_config():
    if not os.path.exists(CONFIG):
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        shutil.copy(EXAMPLE, CONFIG)
        print(f"browser-mate: created config {CONFIG} (edit to taste)", file=sys.stderr)
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    profs = cfg.get("profiles", {})
    if not profs:
        die(f"no profiles in {CONFIG}")
    # validate uniqueness of ports and data dirs across profiles
    ports, dirs = {}, {}
    for name, p in profs.items():
        port = p.get("port")
        udd = os.path.expanduser(p.get("user_data_dir", ""))
        if port in ports:
            die(f"profiles '{name}' and '{ports[port]}' share port {port} — ports must be unique")
        if udd in dirs:
            die(f"profiles '{name}' and '{dirs[udd]}' share user_data_dir — must be unique")
        ports[port], dirs[udd] = name, name
    return cfg


def resolve(cfg, name):
    name = name or cfg.get("default")
    p = cfg.get("profiles", {}).get(name)
    if not p:
        die(f"unknown profile '{name}'. Configured: {', '.join(cfg.get('profiles', {}))}")
    binary = os.path.expanduser(p["binary"])
    udd = os.path.expanduser(p["user_data_dir"])
    port = int(p["port"])
    if not os.path.exists(binary):
        die(f"profile '{name}': binary not found: {binary}")
    if os.path.realpath(udd) in [os.path.realpath(f) for f in _FORBIDDEN]:
        die(f"profile '{name}': user_data_dir points at the real browser profile — refusing "
            f"(would corrupt/lock the user's browser). Use a dedicated dir.")
    return name, binary, udd, port, p.get("default_url")


def port_up(port):
    """Return the CDP /json/version dict if a Chrome debug endpoint answers, else None."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as r:
            return json.load(r)
    except Exception:
        return None


def _pids_for(udd, port):
    """PIDs of chrome processes started by US for this profile (match BOTH the
    dedicated user_data_dir AND our debug port — so we never match the user's
    browser). Returns a list of ints."""
    try:
        out = subprocess.run(["ps", "-ax", "-o", "pid=,command="],
                             capture_output=True, text=True).stdout
    except Exception:
        return []
    pids = []
    needle_dir = f"--user-data-dir={udd}"
    needle_port = f"--remote-debugging-port={port}"
    for line in out.splitlines():
        if needle_dir in line and needle_port in line:
            m = re.match(r"\s*(\d+)\s", line)
            if m:
                pids.append(int(m.group(1)))
    return pids


def ensure(cfg, name):
    name, binary, udd, port, url = resolve(cfg, name)
    info = port_up(port)
    if info:
        print(f"[browser-mate] reusing '{name}' on port {port} ({info.get('Browser','?')})",
              file=sys.stderr)
        print(port)
        return
    # not up. Refuse if the dir is locked by a NON-debug instance (never kill it).
    lock = os.path.join(udd, "SingletonLock")
    if os.path.exists(lock) and not _pids_for(udd, port):
        die(f"profile '{name}': user_data_dir is open in a non-debug Chrome (SingletonLock "
            f"present, no debug port). Refusing to kill it. Close that window or use another "
            f"profile/dir.")
    os.makedirs(udd, exist_ok=True)
    args = [binary, f"--remote-debugging-port={port}", f"--user-data-dir={udd}",
            "--no-first-run", "--no-default-browser-check"]
    if url:
        args.append(url)
    # launch detached; coexists with the user's browser (distinct user_data_dir)
    subprocess.Popen(args, start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):  # ~15s
        time.sleep(0.5)
        if port_up(port):
            print(f"[browser-mate] launched '{name}' on port {port} (data dir {udd})",
                  file=sys.stderr)
            print(port)
            return
    die(f"profile '{name}': launched but debug port {port} never came up")


def cmd_list(cfg):
    for name, p in cfg.get("profiles", {}).items():
        star = " (default)" if name == cfg.get("default") else ""
        print(f"{name}{star}: port {p.get('port')} · {p.get('binary')} · {p.get('user_data_dir')}")


def cmd_status(cfg, name=None):
    names = [name] if name else list(cfg.get("profiles", {}))
    for n in names:
        nm, binary, udd, port, url = resolve(cfg, n)
        up = port_up(port)
        print(f"{nm}: {'UP' if up else 'down'} (port {port})" + (f" — {up.get('Browser')}" if up else ""))


def cmd_stop(cfg, name):
    nm, binary, udd, port, url = resolve(cfg, name)
    pids = _pids_for(udd, port)
    if not pids:
        print(f"[browser-mate] '{nm}' not running under our control", file=sys.stderr)
        return
    for pid in pids:
        os.kill(pid, signal.SIGTERM)  # graceful, ONLY our matched instance
    print(f"[browser-mate] sent SIGTERM to {nm} (pids {pids})", file=sys.stderr)


def main():
    argv = sys.argv[1:]
    if not argv:
        die("usage: browser.py <profile> | launch <profile> | list | status [profile] | stop <profile>")
    cfg = load_config()
    head = argv[0]
    if head == "list":
        cmd_list(cfg)
    elif head == "status":
        cmd_status(cfg, argv[1] if len(argv) > 1 else None)
    elif head == "stop":
        if len(argv) < 2:
            die("stop needs a profile name")
        cmd_stop(cfg, argv[1])
    elif head == "launch":
        ensure(cfg, argv[1] if len(argv) > 1 else None)
    else:
        ensure(cfg, head)  # bare profile name


if __name__ == "__main__":
    main()
