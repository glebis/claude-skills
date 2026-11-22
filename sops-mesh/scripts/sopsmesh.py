#!/usr/bin/env python3
"""sopsmesh — per-machine age keys + SOPS secrets, shared across macOS, Linux and Windows.

Model
  * Every machine has its OWN private key, kept in the best store the platform offers
    (Secure Enclave, macOS Keychain, Windows Credential Manager, libsecret, or a 0600 file).
    Private keys are never copied, never synced, never printed.
  * Public keys travel through a shared folder (Syncthing, git, anything): <mesh>/recipients/*.pub
  * A new public key only becomes a recipient after a human APPROVES it on an admin machine.
    Approvals live in the local config dir, outside the shared folder, so a peer that can write
    to the shared folder cannot grant itself access.
  * Agents get secrets via `sopsmesh run -- <cmd>`: values are injected as env vars into one
    child process; the child never sees how to reach the key.

Standard library only. Python 3.8+.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import re
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import uuid
from pathlib import Path

VERSION = "0.1.0"
SERVICE = os.environ.get("SOPSMESH_SERVICE", "sopsmesh-age")  # Keychain service / Credential Manager target / libsecret attr (override only for tests)
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
PUB_RE = re.compile(r"^age1[0-9a-z]{20,}$")
SECRET_RE = re.compile(r"^AGE-SECRET-KEY-1[0-9A-Z]+$")
SECRET_EXT = (".yaml", ".yml", ".json", ".env")

IS_MAC = sys.platform == "darwin"
IS_WIN = os.name == "nt"
IS_LINUX = sys.platform.startswith("linux")

BACKENDS = {
    "se":        "macOS Secure Enclave (key can't leave the chip; password/Touch ID on every use)",
    "keychain":  "macOS Keychain (encrypted at rest; released without a prompt)",
    "credman":   "Windows Credential Manager (DPAPI, tied to your Windows login)",
    "libsecret": "Linux Secret Service / GNOME Keyring / KWallet (needs a desktop session)",
    "file":      "0600 file (headless Linux/servers: weakest, protect the account)",
}


# ───────────────────────────── small helpers ─────────────────────────────

def die(msg: str, code: int = 1) -> "NoReturn":  # type: ignore[name-defined]
    print(f"✗ {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg: str) -> None:
    print(msg, file=sys.stderr)


def config_dir() -> Path:
    if IS_WIN:
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "sopsmesh"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "sopsmesh"


def extra_path() -> str:
    """PATH with the usual install locations added (brew, ~/.local/bin, scoop)."""
    dirs = [os.environ.get("PATH", "")]
    for d in ("/opt/homebrew/bin", "/usr/local/bin", str(Path.home() / ".local" / "bin"),
              str(Path.home() / "scoop" / "shims"), str(Path.home() / "go" / "bin")):
        if d not in dirs[0]:
            dirs.append(d)
    return os.pathsep.join(dirs)


def which(tool: str) -> str | None:
    return shutil.which(tool, path=extra_path())


def need(tool: str) -> str:
    p = which(tool)
    if not p:
        die(f"{tool} not found. Run `sopsmesh doctor` for install commands.")
    return p


def run_quiet(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    env = kw.pop("env", None) or {**os.environ, "PATH": extra_path()}
    return subprocess.run(cmd, capture_output=True, text=True, env=env, **kw)


def tool_version(tool: str) -> str | None:
    p = which(tool)
    if not p:
        return None
    for flag in ("--version", "version"):
        r = run_quiet([p, flag])
        out = (r.stdout or r.stderr).strip().splitlines()
        if r.returncode == 0 and out:
            return out[0][:60]
    return "installed"


def load_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_private(p: Path, text: str) -> None:
    """Write a file readable only by the current user."""
    p.parent.mkdir(parents=True, exist_ok=True)
    if not IS_WIN:
        os.chmod(p.parent, 0o700)
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        # %APPDATA% is per-user, but inherited ACLs can still grant Administrators/SYSTEM or others.
        # Strip inheritance and grant only the current user (icacls ships with Windows).
        p.write_text(text, encoding="utf-8")
        user = os.environ.get("USERNAME")
        if user:
            r = subprocess.run(["icacls", str(p), "/inheritance:r", "/grant:r", f"{user}:F"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                info(f"⚠ could not restrict access to {p}: {r.stderr.strip()[:120]}")


def short(pub: str) -> str:
    return f"{pub[:12]}…{pub[-6:]}"


def py_cmd() -> list[str]:
    return [sys.executable, str(Path(__file__).resolve())]


# ───────────────────────────── local machine config ─────────────────────────────

def local_cfg_path() -> Path:
    return config_dir() / "config.json"


def load_local() -> dict:
    return load_json(local_cfg_path(), {})


def save_local(cfg: dict) -> None:
    write_private(local_cfg_path(), json.dumps(cfg, indent=2))


def approvals_path() -> Path:
    return config_dir() / "approved.json"


def load_approvals(mesh_id: str) -> dict[str, str]:
    return load_json(approvals_path(), {}).get(mesh_id, {})


def save_approvals(mesh_id: str, approved: dict[str, str]) -> None:
    allm = load_json(approvals_path(), {})
    allm[mesh_id] = dict(sorted(approved.items()))
    write_private(approvals_path(), json.dumps(allm, indent=2))


# ───────────────────────────── platform detection ─────────────────────────────

def detect() -> dict:
    d = {"os": "macos" if IS_MAC else "windows" if IS_WIN else "linux" if IS_LINUX else sys.platform,
         "arch": platform.machine().lower(), "hostname": socket.gethostname().split(".")[0]}
    if IS_MAC:
        d["macos_version"] = platform.mac_ver()[0]
        # Apple Silicon always has a Secure Enclave; Intel Macs only with a T2 chip.
        d["secure_enclave"] = d["arch"] == "arm64" or "T2" in run_quiet(
            ["system_profiler", "SPiBridgeDataType"]).stdout
    if IS_LINUX:
        d["desktop_session"] = bool(os.environ.get("DBUS_SESSION_BUS_ADDRESS")) and bool(
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        d["tpm"] = Path("/dev/tpmrm0").exists()
        try:
            d["distro"] = dict(l.split("=", 1) for l in Path("/etc/os-release").read_text().splitlines()
                               if "=" in l).get("PRETTY_NAME", "").strip('"')
        except OSError:
            pass
    return d


def available_backends(d: dict) -> list[str]:
    out = []
    if d["os"] == "macos":
        if d.get("secure_enclave"):
            out.append("se")
        out.append("keychain")
    elif d["os"] == "windows":
        out.append("credman")
    elif d["os"] == "linux":
        if which("secret-tool") and d.get("desktop_session"):
            out.append("libsecret")
    out.append("file")
    return out


def choose_backend(os_name: str, kind: str, human_present: bool, secure_enclave: bool = True,
                   desktop: bool = False) -> tuple[str, str]:
    """Recommend a key store for one machine. Returns (backend, why).

    Policy: prefer a store where the key cannot be copied (SE); then one that is encrypted by the OS
    and tied to the user's login; a plain file only where nothing else exists (headless servers).
    A hardware-bound key that asks for a password is useless on a machine nobody sits at.
    """
    if kind == "ci":
        return "ci", "CI runner: put the private key in the CI secret store as SOPS_AGE_KEY; no local key."
    if os_name == "macos":
        if secure_enclave and human_present:
            return "se", "Secure Enclave: the key can't be copied, and every decrypt needs a human."
        return "keychain", ("Keychain: nobody is there to approve Secure Enclave prompts."
                            if secure_enclave else "Keychain: this Mac has no Secure Enclave.")
    if os_name == "windows":
        return "credman", "Credential Manager: encrypted with DPAPI, tied to the Windows login."
    if os_name == "linux":
        if desktop:
            return "libsecret", "Secret Service: encrypted keyring unlocked by the desktop login."
        return "file", "Headless Linux: 0600 file. Protect the account; consider a dedicated user."
    return "file", "Unknown OS: 0600 file."


# ───────────────────────────── key backends ─────────────────────────────

def _age_keygen() -> tuple[str, str]:
    """Generate an age X25519 key in memory. Returns (secret, public). Nothing is printed."""
    r = run_quiet([need("age-keygen")])
    sec = next((l for l in r.stdout.splitlines() if SECRET_RE.match(l.strip())), None)
    if r.returncode != 0 or not sec:
        die("age-keygen failed")
    pub = run_quiet([need("age-keygen"), "-y"], input=sec + "\n").stdout.strip()
    if not PUB_RE.match(pub):
        die("could not derive public key")
    return sec.strip(), pub


# Windows Credential Manager via ctypes (advapi32). Only imported on Windows.
def _win_cred():
    import ctypes
    from ctypes import wintypes

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
                    ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
                    ("CredentialBlobSize", wintypes.DWORD),
                    ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
                    ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
                    ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]

    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    CRED_TYPE_GENERIC, CRED_PERSIST_LOCAL_MACHINE = 1, 2

    def write(target: str, secret: str) -> None:
        data = secret.encode("utf-8")
        blob = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        c = CREDENTIAL()
        c.Type, c.TargetName, c.Persist = CRED_TYPE_GENERIC, target, CRED_PERSIST_LOCAL_MACHINE
        c.CredentialBlobSize, c.CredentialBlob = len(data), ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
        c.UserName = os.environ.get("USERNAME", "sopsmesh")
        if not adv.CredWriteW(ctypes.byref(c), 0):
            raise OSError(ctypes.get_last_error(), "CredWriteW failed")

    def read(target: str) -> str | None:
        p = ctypes.POINTER(CREDENTIAL)()
        if not adv.CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(p)):
            return None
        try:
            return ctypes.string_at(p.contents.CredentialBlob, p.contents.CredentialBlobSize).decode("utf-8")
        finally:
            adv.CredFree(p)

    def delete(target: str) -> bool:
        return bool(adv.CredDeleteW(target, CRED_TYPE_GENERIC, 0))

    return write, read, delete


def backend_store(backend: str, secret: str) -> dict:
    """Store a freshly generated secret. Returns backend-specific info for the local config."""
    if backend == "keychain":
        # `security -i` reads the command from stdin, so the key never appears in the process list.
        user = os.environ.get("USER", "sopsmesh")
        r = run_quiet([need("security"), "-i"],
                      input=f'add-generic-password -U -a "{user}" -s {SERVICE} -l "sopsmesh age key" -w {secret}\n')
        if r.returncode != 0 or "error" in (r.stdout + r.stderr).lower():
            die("Keychain write failed: " + (r.stderr or r.stdout).strip()[:200])
        return {"account": user}
    if backend == "credman":
        write, _, _ = _win_cred()
        write(SERVICE, secret)
        return {}
    if backend == "libsecret":
        r = run_quiet([need("secret-tool"), "store", "--label=sopsmesh age key", "service", SERVICE,
                       "account", "age"], input=secret)
        if r.returncode != 0:
            die("secret-tool store failed: " + r.stderr.strip()[:200])
        return {}
    if backend == "file":
        p = config_dir() / "age.key"
        write_private(p, f"# sopsmesh age key, created {_dt.datetime.now().isoformat(timespec='seconds')}\n{secret}\n")
        return {"key_file": str(p)}
    die(f"backend {backend} does not store raw secrets")


def backend_load(cfg: dict) -> str:
    """Return the private key for SOPS_AGE_KEY_CMD. Only called by `sopsmesh key`."""
    b = cfg.get("backend")
    if b == "keychain":
        r = run_quiet([need("security"), "find-generic-password", "-a", cfg.get("account", ""), "-s", SERVICE, "-w"])
        if r.returncode != 0:
            die(f"Keychain item {SERVICE} not found (exit {r.returncode})")
        return r.stdout.strip()
    if b == "credman":
        _, read, _ = _win_cred()
        s = read(SERVICE)
        if not s:
            die(f"Credential Manager entry {SERVICE} not found")
        return s
    if b == "libsecret":
        r = run_quiet([need("secret-tool"), "lookup", "service", SERVICE, "account", "age"])
        if r.returncode != 0 or not r.stdout.strip():
            die("secret-tool lookup failed (is the keyring unlocked?)")
        return r.stdout.strip()
    die(f"backend {b!r} is read by sops directly, not via `sopsmesh key`")


def backend_exists(backend: str) -> bool:
    if backend == "keychain":
        return run_quiet(["security", "find-generic-password", "-s", SERVICE]).returncode == 0
    if backend == "credman":
        return _win_cred()[1](SERVICE) is not None
    if backend == "libsecret":
        return bool(run_quiet(["secret-tool", "lookup", "service", SERVICE, "account", "age"]).stdout.strip())
    if backend == "file":
        return (config_dir() / "age.key").exists()
    if backend == "se":
        return (config_dir() / "se-identity.txt").exists()
    return False


def sops_env(cfg: dict) -> dict:
    """Environment for running sops itself: knows how to reach THIS machine's key."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("SOPS_AGE")}
    env["PATH"] = extra_path()
    b = cfg.get("backend")
    if b in ("se", "file"):
        env["SOPS_AGE_KEY_FILE"] = cfg["key_file"]
    elif b in ("keychain", "credman", "libsecret"):
        env["SOPS_AGE_KEY_CMD"] = " ".join(shlex.quote(x) for x in py_cmd() + ["key"])
    elif not os.environ.get("SOPS_AGE_KEY"):
        die("This machine has no key yet: run `sopsmesh keygen`.")
    else:
        env["SOPS_AGE_KEY"] = os.environ["SOPS_AGE_KEY"]   # CI
    return env


def child_env(base: dict) -> dict:
    """Environment for the agent: never contains any way to reach the key."""
    return {k: v for k, v in base.items() if not k.startswith("SOPS_AGE")}


# ───────────────────────────── mesh folder ─────────────────────────────

STIGNORE = """// sopsmesh: never sync private material or plaintext
*.key
keys.txt
*identity*.txt
*.dec.*
*.plain.*
.env
plain
"""

GITIGNORE = """# sopsmesh: never commit private material or plaintext
*.key
keys.txt
*identity*.txt
*.dec.*
*.plain.*
.env
plain/
.stversions/
*.sync-conflict-*
"""

MESH_README = """# Secrets mesh (managed by sopsmesh)

- `secrets/`     encrypted with SOPS. Safe to sync and commit.
- `recipients/`  one PUBLIC key per machine (`<name>.pub`). Safe to share.
- `.sops.yaml`   who can decrypt. Rewritten by `sopsmesh sync` from the admin's APPROVED list.

Private keys never live here. Run `sopsmesh status` to see who has access.
"""


def find_mesh(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for d in (p, *p.parents):
        if (d / ".sopsmesh.json").exists():
            return d
    die("Not inside a mesh folder (no .sopsmesh.json). Run `sopsmesh init <dir>` or cd into it.")


def mesh_meta(mesh: Path) -> dict:
    return load_json(mesh / ".sopsmesh.json", {})


def read_recipient_files(mesh: Path) -> dict[str, str]:
    out = {}
    for f in sorted((mesh / "recipients").glob("*.pub")):
        if ".sync-conflict-" in f.name:
            info(f"⚠ Syncthing conflict file ignored: {f.name}. Resolve it by hand.")
            continue
        pub = next((l.strip() for l in f.read_text(encoding="utf-8").splitlines() if PUB_RE.match(l.strip())), None)
        if pub:
            out[f.stem] = pub
        else:
            info(f"⚠ {f.name}: no age1… public key inside, ignored")
    return out


def sops_yaml_recipients(mesh: Path) -> list[str]:
    try:
        text = (mesh / ".sops.yaml").read_text(encoding="utf-8")
    except OSError:
        return []
    return re.findall(r"age1[0-9a-z]{20,}", text)


def write_sops_yaml(mesh: Path, approved: dict[str, str]) -> None:
    lines = ["# Managed by sopsmesh. Edit with `sopsmesh approve/revoke`, not by hand.",
             "# Each recipient is one machine's PUBLIC key:"]
    lines += [f"#   {name}: {short(pub)}" for name, pub in approved.items()]
    lines += ["creation_rules:", r"  - path_regex: secrets/[^/]+\.(yaml|yml|json|env)$", "    age: >-"]
    pubs = list(approved.values())
    lines += [f"      {p}{',' if i < len(pubs) - 1 else ''}" for i, p in enumerate(pubs)]
    (mesh / ".sops.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def syncthing_rescan(mesh: Path) -> None:
    """Best effort: ask a local Syncthing to rescan the mesh folders now instead of waiting for its
    file watcher (which can miss changes) or the hourly rescan. Silent if Syncthing isn't there."""
    st = which("syncthing")
    if not st:
        return
    try:
        key = run_quiet([st, "cli", "config", "gui", "apikey", "get"], timeout=5).stdout.strip()
        addr = run_quiet([st, "cli", "config", "gui", "raw-address", "get"], timeout=5).stdout.strip()
        if not key or not addr or addr.startswith(("unix", "/")):
            return
        import urllib.request
        base = f"http://{addr}"
        req = urllib.request.Request(f"{base}/rest/config/folders", headers={"X-API-Key": key})
        folders = json.load(urllib.request.urlopen(req, timeout=5))
        targets = {mesh.resolve(), (mesh / "recipients").resolve()}
        hit = []
        for f in folders:
            if Path(os.path.expanduser(f.get("path", ""))).resolve() in targets:
                urllib.request.urlopen(urllib.request.Request(
                    f"{base}/rest/db/scan?folder={f['id']}", method="POST", headers={"X-API-Key": key}), timeout=5)
                hit.append(f["id"])
        if hit:
            info(f"Syncthing: rescan requested for {', '.join(hit)}")
    except Exception:
        pass


def secret_files(mesh: Path) -> list[Path]:
    return sorted(p for p in (mesh / "secrets").iterdir()
                  if p.is_file() and p.suffix in SECRET_EXT and ".sync-conflict-" not in p.name)


def file_recipients(p: Path) -> list[str]:
    """age recipients a SOPS file is currently encrypted to (read from its metadata, no key needed)."""
    t = p.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"(?:recipient[\"']?\s*[:=]\s*[\"']?|map_recipient=)(age1[0-9a-z]{20,})", t)))


def is_sops_encrypted(p: Path) -> bool:
    """True only if the file carries SOPS metadata AND a SOPS MAC: a plaintext file that merely has a
    `sops:` key doesn't pass."""
    t = p.read_text(encoding="utf-8", errors="replace")
    has_meta = ("sops_mac=" in t) or bool(re.search(r"^sops:\s*$", t, re.M)) or '"sops": {' in t
    has_mac = bool(re.search(r"(?:sops_mac=|\bmac[\"']?\s*:\s*[\"']?)ENC\[AES256_GCM,", t))
    return has_meta and has_mac


# ───────────────────────────── commands ─────────────────────────────

INSTALL = {
    "macos": {
        "sops": "brew install sops", "age": "brew install age",
        "age-plugin-se": "brew install age-plugin-se   (macOS 26+; older macOS: see references/platforms.md)",
        "syncthing": "brew install syncthing && brew services start syncthing",
    },
    "linux": {
        "sops": "download from https://github.com/getsops/sops/releases (apt's sops is often outdated)",
        "age": "sudo apt install age   # or dnf install age / pacman -S age",
        "secret-tool": "sudo apt install libsecret-tools   (desktop only)",
        "syncthing": "sudo apt install syncthing && systemctl --user enable --now syncthing",
    },
    "windows": {
        "sops": "winget install --id Mozilla.SOPS    (or: scoop install sops)",
        "age": "winget install --id FiloSottile.age (or: scoop install age)",
        "syncthing": "winget install --id Syncthing.Syncthing (or SyncTrayzor)",
    },
}


def cmd_doctor(a) -> None:
    d = detect()
    print(f"sopsmesh {VERSION} · Python {platform.python_version()} · {sys.executable}")
    print(f"Machine: {d['hostname']} · {d['os']} {d.get('macos_version') or d.get('distro') or platform.release()} · {d['arch']}")
    if IS_MAC:
        print(f"Secure Enclave: {'yes' if d.get('secure_enclave') else 'no'}")
    if IS_LINUX:
        print(f"Desktop session: {'yes' if d.get('desktop_session') else 'no (headless)'} · TPM: {'yes' if d.get('tpm') else 'no'}")
    print("\nTools:")
    tools = ["sops", "age", "age-keygen", "syncthing"]
    tools += ["age-plugin-se"] if IS_MAC else ["secret-tool"] if IS_LINUX and d.get("desktop_session") else []
    missing = []
    for t in tools:
        v = tool_version(t)
        print(f"  {'✓' if v else '✗'} {t:14} {v or 'missing'}")
        if not v and t != "age-keygen":
            missing.append(t)
    if v := tool_version("sops"):
        m = re.search(r"(\d+)\.(\d+)", v)
        if m and (int(m[1]), int(m[2])) < (3, 10):
            print("  ⚠ sops < 3.10: SOPS_AGE_KEY_CMD unsupported. Upgrade sops.")
        elif m and IS_WIN and (int(m[1]), int(m[2])) < (3, 12):
            print("  ⚠ sops < 3.12 on Windows: Credential Manager backend needs 3.12+ (SOPS_AGE_RECIPIENT).")
    hints = INSTALL.get(d["os"], {})
    if missing:
        print("\nInstall:")
        for t in missing:
            if t in hints:
                print(f"  {t:14} {hints[t]}")
    print("\nKey stores on this machine:")
    avail = available_backends(d)
    for b, desc in BACKENDS.items():
        if b in avail:
            print(f"  ✓ {b:10} {desc}")
    rec, why = choose_backend(d["os"], "laptop", True, d.get("secure_enclave", False), d.get("desktop_session", False))
    if rec == "se" and not which("age-plugin-se"):
        rec, why = "keychain", "Keychain (install age-plugin-se to use the Secure Enclave instead)."
    print(f"\nRecommended here: {rec} · {why}")
    cfg = load_local()
    if cfg:
        print(f"Configured: name={cfg.get('name')} backend={cfg.get('backend')} public={short(cfg.get('public', ''))}")


def _ask(prompt: str, choices: list[str] | None = None, default: str | None = None) -> str:
    suffix = f" [{'/'.join(choices)}]" if choices else ""
    suffix += f" ({default})" if default else ""
    while True:
        ans = input(f"{prompt}{suffix}: ").strip() or (default or "")
        if not choices or ans in choices:
            return ans
        print(f"  choose one of: {', '.join(choices)}")


def cmd_plan(a) -> None:
    """Interview (or read --answers JSON) and print a per-machine setup plan."""
    if a.answers:
        ans = json.loads(Path(a.answers).read_text(encoding="utf-8"))
    else:
        print("Which machines will share secrets? One per line, empty name to finish.\n")
        machines = []
        while True:
            name = input(f"Machine #{len(machines) + 1} name (empty = done): ").strip()
            if not name:
                break
            os_name = _ask("  OS", ["macos", "linux", "windows"])
            kind = _ask("  kind", ["laptop", "desktop", "server", "ci"], "laptop")
            human = kind in ("laptop", "desktop") and _ask("  someone at the screen to approve prompts?", ["y", "n"], "y") == "y"
            m = {"name": name, "os": os_name, "kind": kind, "human_present": human}
            if os_name == "macos":
                m["secure_enclave"] = _ask("  Apple Silicon or T2 chip?", ["y", "n"], "y") == "y"
            if os_name == "linux" and kind != "ci":
                m["desktop"] = _ask("  desktop session (GNOME/KDE)?", ["y", "n"], "n" if kind == "server" else "y") == "y"
            machines.append(m)
        if not machines:
            die("no machines given")
        admin = _ask("Admin machine (approves new keys)", [m["name"] for m in machines], machines[0]["name"])
        transport = _ask("How do files travel between machines?", ["syncthing", "git", "both"], "syncthing")
        ans = {"machines": machines, "admin": admin, "transport": transport}

    for m in ans["machines"]:
        if not NAME_RE.match(m["name"]):
            die(f"bad machine name {m['name']!r}: letters, digits, . _ - only")
    oses = sorted({m["os"] for m in ans["machines"]})
    print("\n══ Plan ══")
    print(f"Platforms: {', '.join(oses)} · transport: {ans['transport']} · admin: {ans['admin']}")
    print("Stack: sops + age everywhere (one format on every OS); sopsmesh.py (Python stdlib) on every machine.\n")
    print(f"{'machine':16} {'os':8} {'key store':10} why")
    for m in ans["machines"]:
        b, why = choose_backend(m["os"], m.get("kind", "laptop"), m.get("human_present", True),
                                m.get("secure_enclave", True), m.get("desktop", False))
        m["backend"] = b
        print(f"{m['name']:16} {m['os']:8} {b:10} {why}")

    def kg(m: dict) -> str:
        return f"sopsmesh keygen --name {m['name']} --backend {m['backend']}"

    admin = next(m for m in ans["machines"] if m["name"] == ans["admin"])
    print("\nSteps  (sopsmesh = `python3 sopsmesh.py`; on Windows `py sopsmesh.py`)")
    print("1. Every machine: install tools. `sopsmesh doctor` prints the exact commands.")
    if ans["transport"] in ("syncthing", "both"):
        print("2. Syncthing: share ~/secrets-mesh with every machine. Hardened layout (recommended):")
        print("   outer folder Send Only on the admin / Receive Only elsewhere, and recipients/ shared as its own")
        print("   Send & Receive folder, with `/recipients` in the outer .stignore. See references/syncthing.md.")
    if ans["transport"] in ("git", "both"):
        print("2. Git: one PRIVATE repo for ~/secrets-mesh; every machine clones it.")
    print(f"3. On {admin['name']}:  sopsmesh init ~/secrets-mesh && cd ~/secrets-mesh && {kg(admin)}")
    for m in ans["machines"]:
        if m is not admin and m["backend"] != "ci":
            print(f"4. On {m['name']}, inside the synced folder:  {kg(m)}" + ("  --unattended" if m["backend"] == "keychain" and m["os"] == "macos" else ""))
    print(f"5. On {admin['name']}:  sopsmesh status → confirm each fingerprint by phone/in person →")
    print("   sopsmesh approve <name> --fingerprint <≥12 chars after age1, or last ≥6> → sopsmesh sync")
    if admin["backend"] == "se":
        print("   (the admin key is in the Secure Enclave: every sync asks for your password once per file)")
    print("6. Anywhere:  sopsmesh run --secrets secrets/app.env -- <agent command>")
    for m in ans["machines"]:
        if m["backend"] == "ci":
            print(f"CI ({m['name']}): on {admin['name']} run `sopsmesh keygen --backend file --name {m['name']} --export`;")
            print("   it prints the key ONCE and stores nothing. Put it into the CI secret store as SOPS_AGE_KEY,")
            print(f"   then `sopsmesh approve {m['name']}` and `sopsmesh sync`.")
    if a.save:
        Path(a.save).write_text(json.dumps(ans, indent=2), encoding="utf-8")
        print(f"\nSaved answers to {a.save}")


def cmd_init(a) -> None:
    mesh = Path(a.dir).expanduser().resolve()
    if (mesh / ".sopsmesh.json").exists():
        die(f"{mesh} is already a mesh")
    for sub in ("secrets", "recipients"):
        (mesh / sub).mkdir(parents=True, exist_ok=True)
    (mesh / ".sopsmesh.json").write_text(json.dumps({"id": str(uuid.uuid4()), "version": 1}, indent=2), encoding="utf-8")
    for name, text in ((".stignore", STIGNORE), (".gitignore", GITIGNORE), ("README.md", MESH_README)):
        if not (mesh / name).exists():
            (mesh / name).write_text(text, encoding="utf-8")
    print(f"✓ Mesh created at {mesh}")
    print("  Next: cd there and run `sopsmesh keygen`. You become the admin of this mesh on this machine.")


def cmd_keygen(a) -> None:
    mesh = find_mesh()
    meta = mesh_meta(mesh)
    cfg = load_local()
    d = detect()
    name = a.name or cfg.get("name") or d["hostname"]
    if not NAME_RE.match(name):
        die(f"bad name {name!r}")
    backend = a.backend
    if backend == "auto" and not a.export:
        backend, why = choose_backend(d["os"], "laptop", not a.unattended, d.get("secure_enclave", False),
                                      d.get("desktop_session", False))
        if backend == "se" and not which("age-plugin-se"):
            backend, why = "keychain", "age-plugin-se not installed"
        info(f"Key store: {backend} · {why}")
    if a.export:
        if not a.name or a.name == cfg.get("name"):
            die("--export makes a key for ANOTHER machine (CI): give it its own --name")
        backend = "file"   # generated in memory only; nothing is stored
    elif backend not in available_backends(d):
        die(f"backend {backend} not available here. Available: {', '.join(available_backends(d))}")
    elif cfg.get("public") and not a.force:
        die(f"this machine already has a key ({short(cfg['public'])}). Use --force to replace it "
            "(old key stays in its store; revoke it on the admin).")
    if not a.export and backend_exists(backend) and not a.force:
        die(f"a sopsmesh key already exists in {backend}. Use --force to overwrite.")

    extra: dict = {}
    if backend == "se":
        plugin = need("age-plugin-se")
        idf = config_dir() / "se-identity.txt"
        idf.parent.mkdir(parents=True, exist_ok=True)
        if idf.exists():
            idf.rename(idf.with_suffix(f".old-{_dt.datetime.now():%Y%m%d%H%M%S}.txt"))
        r = run_quiet([plugin, "keygen", "--access-control", a.access_control, "-o", str(idf)])
        if r.returncode != 0:
            die("age-plugin-se keygen failed: " + r.stderr.strip()[:200])
        if not IS_WIN:
            os.chmod(idf, 0o600)
        pub = run_quiet([plugin, "recipients", "-i", str(idf)]).stdout.strip()
        extra = {"key_file": str(idf)}
    else:
        secret, pub = _age_keygen()
        if a.export:   # CI only: print once, never stored here
            print(secret)
            info(f"⚠ Put this into the CI secret store as SOPS_AGE_KEY now. Public key: {pub}")
            del secret
            extra = {}
        else:
            extra = backend_store(backend, secret)
            del secret
    if not PUB_RE.match(pub or ""):
        die("could not read the new public key")

    pubfile = mesh / "recipients" / f"{name}.pub"
    pubfile.write_text(f"# sopsmesh recipient · {name} · {backend} · {d['os']} · "
                       f"{_dt.date.today().isoformat()}\n{pub}\n", encoding="utf-8")
    if not a.export:
        cfg.update({"name": name, "backend": backend, "public": pub, **extra})
        save_local(cfg)

    approved = load_approvals(meta["id"])
    if not approved and not sops_yaml_recipients(mesh):   # first key in a new mesh: you are the admin
        approved[name] = pub
        save_approvals(meta["id"], approved)
        write_sops_yaml(mesh, approved)
        print("✓ First key in this mesh: approved automatically, this machine is the admin.")
    if a.export:
        print(f"✓ Key for {name} printed above and NOT stored here. Approve it after it's in the CI secret store.")
    else:
        print(f"✓ Key created in {backend}. Private part never left this machine.")
    print(f"  Public key written to recipients/{name}.pub")
    print(f"  Fingerprint to read out to the admin: {short(pub)}")
    syncthing_rescan(mesh)


def cmd_key(a) -> None:
    """Print this machine's private key for sops (SOPS_AGE_KEY_CMD). Refuses obvious other callers.

    Defence in depth, NOT a security boundary: a process running as the same user can make sops its
    parent (e.g. `sops exec-env f '<this command>'`) or set SOPS_AGE_RECIPIENT itself. The real
    protections are the agent deny rules and, on Macs, the Secure Enclave backend.
    """
    # No override flag on purpose: an agent reading this file must not find a way around the check.
    if IS_WIN:   # no `ps`; sops ≥ 3.12 sets SOPS_AGE_RECIPIENT when it runs the key command
        if not os.environ.get("SOPS_AGE_RECIPIENT"):
            die("refusing: `sopsmesh key` only answers sops ≥ 3.12. Use `sopsmesh run` instead.")
    else:
        parent = run_quiet(["ps", "-o", "comm=", "-p", str(os.getppid())]).stdout.strip()
        if not os.path.basename(parent).startswith("sops"):
            die("refusing: `sopsmesh key` only answers sops itself (parent process is "
                f"{parent or 'unknown'}). Use `sopsmesh run` to give a program its secrets.")
    sys.stdout.write(backend_load(load_local()) + "\n")


def cmd_status(a) -> None:
    mesh = find_mesh()
    meta = mesh_meta(mesh)
    cfg = load_local()
    approved = load_approvals(meta["id"])
    files = read_recipient_files(mesh)
    in_yaml = set(sops_yaml_recipients(mesh))
    print(f"Mesh: {mesh}")
    print(f"This machine: {cfg.get('name', '— no key, run keygen')} ({cfg.get('backend', '-')})")
    print(f"Admin approvals stored here: {len(approved)}\n")
    print(f"{'name':16} {'key':22} state")
    for name in sorted(set(files) | set(approved)):
        pub = files.get(name) or approved.get(name)
        if name in approved and files.get(name) and files[name] != approved[name]:
            state = "⚠ KEY CHANGED in recipients/: not trusted until re-approved"
        elif name in approved:
            state = "approved" + ("" if approved[name] in in_yaml else " · not in .sops.yaml yet (run sync)")
        elif approved or not in_yaml:
            state = "pending: verify fingerprint, then `sopsmesh approve " + name + "`"
        else:
            state = "in .sops.yaml" if pub in in_yaml else "waiting for the admin"
        print(f"{name:16} {short(pub):22} {state}")
    if approved:
        rogue = in_yaml - set(approved.values())
        if rogue:
            print(f"\n⚠ .sops.yaml lists {len(rogue)} key(s) you never approved: {', '.join(short(r) for r in rogue)}")
            print("  Someone edited it in the shared folder. `sopsmesh sync` will rewrite it from your approvals.")
    print("\nSecrets:")
    want = set(approved.values()) if approved else in_yaml
    for f in secret_files(mesh):
        if not is_sops_encrypted(f):
            print(f"  ⚠ {f.name}: NOT ENCRYPTED. Move it out of the mesh now.")
            continue
        have = set(file_recipients(f))
        diff = "" if have == want else f" · differs from approved list (+{len(want - have)} / -{len(have - want)}), run sync"
        print(f"  {f.name}: {len(have)} recipients{diff}")


def cmd_approve(a) -> None:
    mesh = find_mesh()
    meta = mesh_meta(mesh)
    files = read_recipient_files(mesh)
    if a.name not in files:
        die(f"no recipients/{a.name}.pub")
    pub = files[a.name]
    if a.skip_fingerprint_check:
        info(f"⚠ Approving {a.name} WITHOUT a fingerprint check. Only do this for a machine you set up yourself.")
    else:
        fp = (a.fingerprint or "").strip().rstrip("…").lower()
        # Every key starts with "age1" (or "age1se1"), so a start-match must cover random characters too.
        head_ok = pub.startswith(fp) and len(fp) >= len(pub.split("1", 1)[0]) + 12
        tail_ok = len(fp) >= 6 and pub.endswith(fp)
        if not fp:
            die(f"--fingerprint is required: ask {a.name}'s owner to read out their key through another channel "
                f"(phone, in person). File has {short(pub)}.")
        if not (head_ok or tail_ok):
            die(f"fingerprint mismatch or too short: give ≥12 characters after 'age1…' or the last ≥6. "
                f"File has {short(pub)}. Do NOT approve until {a.name} confirms.")
    approved = load_approvals(meta["id"])
    approved[a.name] = pub
    save_approvals(meta["id"], approved)
    print(f"✓ Approved {a.name} ({short(pub)}). Run `sopsmesh sync` to give it access.")


def _sync(mesh: Path, approved: dict[str, str], dry: bool) -> None:
    if not approved:
        die("no approved keys on this machine. Only the admin machine can sync.")
    cfg = load_local()
    if cfg.get("public") not in approved.values():
        die("this machine's own key isn't approved here, so it couldn't re-wrap the secrets.")
    own = mesh / "recipients" / f"{cfg.get('name')}.pub"
    if cfg.get("name") in approved and read_recipient_files(mesh).get(cfg["name"]) != cfg["public"]:
        print(f"• recipients/{own.name} was missing or altered: restoring this machine's real public key")
        if not dry:
            own.write_text(f"# sopsmesh recipient · {cfg['name']} · {cfg.get('backend')} · restored "
                           f"{_dt.date.today().isoformat()}\n{cfg['public']}\n", encoding="utf-8")
    want = set(approved.values())
    if set(sops_yaml_recipients(mesh)) != want:
        print(f"• .sops.yaml → {len(want)} recipients")
        if not dry:
            write_sops_yaml(mesh, approved)
    env = sops_env(cfg)
    for f in secret_files(mesh):
        if not is_sops_encrypted(f):
            print(f"⚠ skipping {f.name}: not encrypted")
            continue
        if set(file_recipients(f)) == want:
            continue
        print(f"• {f.name}: re-wrapping data key")
        if not dry:
            r = subprocess.run([need("sops"), "updatekeys", "-y", str(f.relative_to(mesh))],
                               cwd=mesh, env=env, capture_output=True, text=True)
            if r.returncode != 0:
                die(f"updatekeys failed on {f.name}: {r.stderr.strip().splitlines()[-1] if r.stderr else ''}")
    print("✓ in sync" + (" (dry run, nothing written)" if dry else ""))
    if not dry:
        syncthing_rescan(mesh)


def cmd_sync(a) -> None:
    mesh = find_mesh()
    meta = mesh_meta(mesh)
    approved = load_approvals(meta["id"])
    files = read_recipient_files(mesh)
    for name, pub in files.items():
        if name in approved and approved[name] != pub:
            info(f"⚠ {name}: recipients/{name}.pub changed. Keeping the APPROVED key; re-approve if intended.")
        elif name not in approved:
            info(f"• {name}: pending ({short(pub)}). Not added. Verify, then `sopsmesh approve {name}`.")
    _sync(mesh, approved, a.dry_run)


def cmd_revoke(a) -> None:
    mesh = find_mesh()
    meta = mesh_meta(mesh)
    approved = load_approvals(meta["id"])
    if a.name not in approved:
        die(f"{a.name} is not approved")
    if approved[a.name] == load_local().get("public"):
        die("refusing to revoke this machine's own key (you'd lose the ability to re-wrap)")
    del approved[a.name]
    save_approvals(meta["id"], approved)
    pf = mesh / "recipients" / f"{a.name}.pub"
    if pf.exists():
        dst = mesh / "recipients" / "revoked"
        dst.mkdir(exist_ok=True)
        pf.rename(dst / f"{a.name}.{_dt.date.today().isoformat()}.pub.revoked")
    _sync(mesh, approved, False)
    print(f"⚠ {a.name} can no longer decrypt NEW versions. It may have copies of old values:")
    print("  rotate the real secrets (new API keys/passwords), then `sopsmesh edit` each file.")


def _resolve_secret(mesh: Path, s: str) -> Path:
    p = (Path.cwd() / s).resolve()
    if not p.exists():
        p = (mesh / "secrets" / s).resolve()
    if not p.exists() or mesh not in p.parents:
        die(f"no secret file {s} in this mesh")
    return p


def _decrypt_env(mesh: Path, f: Path, env: dict) -> dict[str, str]:
    """Decrypt one file in memory into a flat {VAR: value} map. Plaintext never touches disk or stdout."""
    fmt = {".env": "dotenv", ".json": "json"}.get(f.suffix, "yaml")
    r = subprocess.run([need("sops"), "decrypt", "--input-type", fmt, "--output-type", "json", str(f)],
                       cwd=mesh, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        if "no master key" in r.stderr or "no identity matched" in r.stderr:
            die(f"cannot decrypt {f.name}: this machine's key is not one of its recipients. Ask the admin to "
                "`sopsmesh approve <this machine>` and `sopsmesh sync`, then wait for the folder to sync.")
        if "failed to execute command" in r.stderr or "exit status" in r.stderr:
            die(f"cannot decrypt {f.name}: the key store refused (locked keychain, cancelled prompt, or no "
                "desktop session). Run `sopsmesh doctor`.")
        last = [l for l in r.stderr.strip().splitlines() if l.strip()]
        die(f"cannot decrypt {f.name}: {last[-1] if last else 'sops failed'}")
    data, out = json.loads(r.stdout), {}

    def scalar(v) -> str:
        if v is None:
            return ""
        if isinstance(v, bool):
            return str(v).lower()
        if isinstance(v, (dict, list)):
            die(f"{f.name}: lists of objects can't become env vars. Flatten that part of the file.")
        return str(v)

    def flat(prefix: str, v) -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                flat(f"{prefix}_{k}" if prefix else str(k), x)
        else:   # lists of scalars become comma-separated values
            val = ",".join(scalar(x) for x in v) if isinstance(v, list) else scalar(v)
            out[re.sub(r"[^A-Za-z0-9_]", "_", prefix).upper()] = val
    flat("", data)
    return out


def cmd_run(a) -> None:
    mesh = find_mesh()
    if not a.cmd:
        die("usage: sopsmesh run --secrets secrets/app.env -- <command> [args]")
    cmd = a.cmd[1:] if a.cmd[0] == "--" else a.cmd
    env = sops_env(load_local())
    values: dict[str, str] = {}
    for s in a.secrets or [str(p.relative_to(mesh)) for p in secret_files(mesh)]:
        values.update(_decrypt_env(mesh, _resolve_secret(mesh, s), env))
    if a.only:
        keep = {k.strip().upper() for k in a.only.split(",")}
        values = {k: v for k, v in values.items() if k in keep}
    info(f"sopsmesh: injecting {len(values)} variable(s) into one process: {', '.join(sorted(values))}")
    r = subprocess.run(cmd, env={**child_env(os.environ.copy()), **values})
    sys.exit(r.returncode)


def cmd_encrypt(a) -> None:
    mesh = find_mesh()
    src = Path(a.plaintext).expanduser().resolve()
    name = a.name or src.name
    if Path(name).suffix not in SECRET_EXT:
        die(f"secret name must end in one of {', '.join(SECRET_EXT)}")
    dst = mesh / "secrets" / name
    if dst.exists() and not a.force:
        die(f"{dst.relative_to(mesh)} exists. Use `sopsmesh edit` to change it, or --force.")
    fmt = {".env": "dotenv", ".json": "json"}.get(Path(name).suffix, "yaml")
    r = subprocess.run([need("sops"), "encrypt", "--filename-override", f"secrets/{name}",
                        "--input-type", fmt, "--output-type", fmt, str(src)],
                       cwd=mesh, env={**os.environ, "PATH": extra_path()}, capture_output=True, text=True)
    if r.returncode != 0:
        die("sops encrypt failed: " + r.stderr.strip()[-300:])
    dst.write_text(r.stdout, encoding="utf-8")
    print(f"✓ secrets/{name} encrypted for {len(file_recipients(dst))} recipient(s).")
    syncthing_rescan(mesh)
    if mesh in src.parents:
        print(f"⚠ The plaintext {src.name} is INSIDE the mesh folder. Move it to the Trash now.")
    else:
        print(f"  Now move the plaintext {src} to the Trash.")


def cmd_edit(a) -> None:
    mesh = find_mesh()
    f = _resolve_secret(mesh, a.file)
    sys.exit(subprocess.run([need("sops"), "edit", str(f)], cwd=mesh, env=sops_env(load_local())).returncode)


# ───────────────────────────── scan: find secrets worth encrypting ─────────────────────────────
# Values are NEVER printed. Findings show name, location, a type label and the value's length.

VALUE_PATTERNS = [   # (label, regex on the value)
    ("OpenAI key", r"^sk-(proj-)?[A-Za-z0-9_-]{20,}$"),
    ("Anthropic key", r"^sk-ant-[A-Za-z0-9_-]{20,}$"),
    ("GitHub token", r"^(ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}$"),
    ("Slack token", r"^xox[abprs]-[A-Za-z0-9-]{10,}$"),
    ("AWS access key", r"^(AKIA|ASIA)[A-Z0-9]{16}$"),
    ("Google API key", r"^AIza[0-9A-Za-z_-]{30,}$"),
    ("Stripe key", r"^(sk|rk)_(live|test)_[A-Za-z0-9]{16,}$"),
    ("JWT", r"^eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}$"),
    ("private key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("age private key", r"^AGE-SECRET-KEY-1[0-9A-Z]+$"),
    ("URL with password", r"^[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@"),
]
NAME_HINT = re.compile(r"(^|_)(API_?KEY|KEY|TOKEN|SECRET|PASS(WORD|WD)?|PWD|PRIVATE|CREDENTIALS?|AUTH|DSN|"
                       r"WEBHOOK|SESSION|COOKIE|SIGNING|ENCRYPTION|CLIENT_SECRET|BEARER)($|_)", re.I)
NAME_SAFE = re.compile(r"^(PATH|HOME|SHELL|USER|LOGNAME|LANG|LC_.*|TERM.*|PWD|OLDPWD|SHLVL|TMPDIR|EDITOR|PAGER|"
                       r"XPC_.*|SSH_AUTH_SOCK|SSH_AGENT_PID|GPG_TTY|COLORTERM|DISPLAY|WAYLAND_DISPLAY|"
                       r"DBUS_SESSION_BUS_ADDRESS|.*_PATH|.*_DIR|.*_HOME|SOPS_AGE_KEY_FILE|SOPS_AGE_KEY_CMD|"
                       r"__CF.*|_|COMMAND_MODE|SECURITYSESSIONID|.*_SOCK|.*_PID|KEYCHAIN.*|.*KEYMAP.*|.*KEYBOARD.*)$", re.I)
PLACEHOLDER = re.compile(r"^(|x+|changeme|change_me|example|placeholder|your[_-].*|<.*>|\$\{.*\}|\$[A-Z_]+|"
                         r"todo|none|null|false|true|0|1|dummy|test|demo.*|.*not[-_]?real.*)$", re.I)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".tox", "dist", "build", ".next",
             "Library", ".cache", ".npm", ".cargo", "target", ".Trash", "AppData", ".stversions", "Pods"}
ENV_FILE_RE = re.compile(r"^(\.env(\..+)?|.*\.env|\.envrc|.*\.secrets?(\..+)?|credentials(\.json)?|"
                         r"secrets?\.(ya?ml|json|toml)|\.npmrc|\.pypirc|\.netrc|config\.json)$")
PROFILE_FILES = [".zshrc", ".zprofile", ".zshenv", ".bashrc", ".bash_profile", ".profile",
                 ".config/fish/config.fish", "Documents/PowerShell/Microsoft.PowerShell_profile.ps1",
                 "Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1"]
QUOTED_PAIR_RE = re.compile(r"""["']([A-Za-z_][A-Za-z0-9_.-]*)["']\s*:\s*["']([^"']*)["']""")
ASSIGN_RE = re.compile(r"""^\s*(?:export\s+|set\s+-gx\s+|\$env:|setx\s+)?([A-Za-z_][A-Za-z0-9_.-]*)\s*[=:\s]\s*["']?([^"'#\n]*)""")


def _entropy(s: str) -> float:
    import math
    if not s:
        return 0.0
    freq = {c: s.count(c) for c in set(s)}
    return -sum(n / len(s) * math.log2(n / len(s)) for n in freq.values())


def classify(name: str, value: str) -> tuple[str, str] | None:
    """Return (severity, label) if this name/value pair looks like a secret, else None."""
    v = value.strip().strip("'\"")
    if PLACEHOLDER.match(v) or v.startswith(("ENC[", "op://", "vault:")):
        return None
    for label, rx in VALUE_PATTERNS:
        if re.search(rx, v):
            return "high", label
    if NAME_SAFE.match(name):
        return None
    if NAME_HINT.search(name):
        if len(v) >= 12 and _entropy(v) >= 3.0:
            return "high", "secret-like name, random-looking value"
        if len(v) >= 6:
            return "medium", "secret-like name"
    elif len(v) >= 32 and _entropy(v) >= 4.2 and not re.search(r"[\s/]", v):
        return "low", "long random-looking value"
    return None


def _scan_file(p: Path) -> list[dict]:
    out = []
    try:
        if p.stat().st_size > 512_000:
            return out
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    if is_sops_encrypted(p):
        return out
    if "-----BEGIN" in text and "PRIVATE KEY-----" in text:
        out.append({"name": "(PEM block)", "line": text[:text.find("-----BEGIN")].count("\n") + 1,
                    "severity": "high", "label": "private key", "length": 0})
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("#", "//")):
            continue
        pairs = [(m.group(1), m.group(2)) for m in QUOTED_PAIR_RE.finditer(line)]   # JSON / quoted YAML
        if not pairs and (m := ASSIGN_RE.match(line)):                               # KEY=value, export, YAML
            pairs = [(m.group(1), m.group(2))]
        for name, value in pairs:
            value = value.strip()
            c = classify(name.split(".")[-1].upper(), value)
            if c:
                out.append({"name": name, "line": i, "severity": c[0], "label": c[1], "length": len(value)})
    return out


def _walk(roots: list[Path], max_depth: int, max_files: int) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        if root.is_file():
            found.append(root)
            continue
        base_depth = len(root.parts)
        for dirpath, dirnames, filenames in os.walk(root):
            depth = len(Path(dirpath).parts) - base_depth
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not (depth >= max_depth)]
            if any(part in ("secrets",) for part in Path(dirpath).parts[-1:]) and (Path(dirpath).parent / ".sopsmesh.json").exists():
                continue   # our own encrypted secrets
            for f in filenames:
                if ENV_FILE_RE.match(f) and ".example" not in f and ".sample" not in f and ".template" not in f:
                    found.append(Path(dirpath) / f)
                    if len(found) >= max_files:
                        return found
    return found


def cmd_scan(a) -> None:
    findings: list[dict] = []
    if not a.no_env:
        for name, value in os.environ.items():
            c = classify(name, value)
            if c:
                findings.append({"where": "environment", "kind": "env", "name": name, "line": None,
                                 "severity": c[0], "label": c[1], "length": len(value)})
    home = Path.home()
    if not a.no_profiles:
        for rel in PROFILE_FILES:
            p = home / rel
            if p.exists():
                for f in _scan_file(p):
                    findings.append({"where": str(p), "kind": "profile", **f})
    roots = [Path(r).expanduser().resolve() for r in (a.paths or ["."])]
    for p in _walk(roots, a.depth, a.max_files):
        for f in _scan_file(p):
            findings.append({"where": str(p), "kind": "file", **f})

    order = {"high": 0, "medium": 1, "low": 2}
    findings = [f for f in findings if order[f["severity"]] <= order[a.min_severity]]
    findings.sort(key=lambda f: (order[f["severity"]], f["kind"], f["where"], f["line"] or 0))

    if a.json:
        print(json.dumps(findings, indent=2))
        return
    if not findings:
        print("✓ Nothing found that looks like a plaintext secret.")
        return
    def loc(f):
        return "env" if f["kind"] == "env" else f"{f['where'].replace(str(home), '~')}:{f['line']}"
    print(f"Found {len(findings)} likely secret(s). Values are not shown.\n")
    print(f"{'sev':6} {'name':28} {'what':38} where")
    for f in findings:
        what = f["label"] + (f" ({f['length']} chars)" if f["length"] else "")
        print(f"{f['severity']:6} {f['name'][:28]:28} {what[:38]:38} {loc(f)}")

    print("\nWhat to do")
    if any(f["kind"] == "profile" for f in findings) or any(f["kind"] == "env" for f in findings):
        print("• Shell profile / environment: every program you start, including AI agents, inherits these.")
        print("  Move each value into the mesh (`sopsmesh encrypt`), delete the `export` line, and start")
        print("  programs with `sopsmesh run -- <cmd>` so only that process gets it. Rotate anything an agent saw.")
    files = sorted({f["where"] for f in findings if f["kind"] == "file"})
    for fp in files:
        n = Path(fp).name
        if n.startswith(".env"):               # .env, .env.production → <folder>[-production].env
            tail = n[4:].lstrip(".")
            target = f"{Path(fp).parent.name or 'app'}{'-' + tail if tail else ''}.env"
        elif Path(n).suffix in SECRET_EXT:
            target = n
        else:
            target = n.lstrip(".").replace(".", "-") + ".env"
        print(f"• {fp.replace(str(home), '~')}:\n    sopsmesh encrypt '{fp}' --name {target}   # then move the original to the Trash")
    print("• Already committed to git? Encrypting now doesn't remove history: rotate those values.")


# ───────────────────────────── CLI ─────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(prog="sopsmesh", description="Per-machine age keys + SOPS secrets across macOS, Linux and Windows.")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="detect platform, tools and key stores; print install commands").set_defaults(fn=cmd_doctor)
    s = sub.add_parser("plan", help="interview about your machines and print a setup plan")
    s.add_argument("--answers", help="JSON answers instead of the interactive interview")
    s.add_argument("--save", help="save answers to this JSON file")
    s.set_defaults(fn=cmd_plan)
    s = sub.add_parser("init", help="create a mesh folder (secrets/, recipients/, .stignore)")
    s.add_argument("dir")
    s.set_defaults(fn=cmd_init)
    s = sub.add_parser("keygen", help="create THIS machine's key and publish its public key")
    s.add_argument("--backend", default="auto", choices=["auto", *BACKENDS])
    s.add_argument("--name", help="machine name in the mesh (default: hostname)")
    s.add_argument("--access-control", default="any-biometry-or-passcode", help="Secure Enclave policy")
    s.add_argument("--unattended", action="store_true", help="nobody at this screen: skip Secure Enclave")
    s.add_argument("--export", action="store_true", help="CI: print the private key ONCE instead of storing it")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_keygen)
    s = sub.add_parser("key", help="(for sops only) print the private key via SOPS_AGE_KEY_CMD")
    s.set_defaults(fn=cmd_key)
    sub.add_parser("status", help="who has access, pending keys, tampering, unencrypted files").set_defaults(fn=cmd_status)
    s = sub.add_parser("approve", help="(admin) trust a public key from recipients/")
    s.add_argument("name")
    s.add_argument("--fingerprint", help="start (≥12 chars past age1) or end (≥6 chars) of the key, as read out by its owner")
    s.add_argument("--skip-fingerprint-check", action="store_true", help="only for a machine you set up yourself")
    s.set_defaults(fn=cmd_approve)
    s = sub.add_parser("sync", help="(admin) rewrite .sops.yaml from approvals and re-wrap every secret")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_sync)
    s = sub.add_parser("revoke", help="(admin) remove a machine and re-wrap")
    s.add_argument("name")
    s.set_defaults(fn=cmd_revoke)
    s = sub.add_parser("run", help="run a command with secrets as env vars (the agent-safe way)")
    s.add_argument("--secrets", action="append", help="secret file (repeatable; default: all)")
    s.add_argument("--only", help="comma-separated variable names to pass")
    s.add_argument("cmd", nargs=argparse.REMAINDER)
    s.set_defaults(fn=cmd_run)
    s = sub.add_parser("encrypt", help="encrypt a plaintext file into secrets/")
    s.add_argument("plaintext")
    s.add_argument("--name")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_encrypt)
    s = sub.add_parser("scan", help="find plaintext secrets in env vars, shell profiles and .env-like files")
    s.add_argument("paths", nargs="*", help="folders/files to scan (default: current folder)")
    s.add_argument("--depth", type=int, default=4)
    s.add_argument("--max-files", type=int, default=2000)
    s.add_argument("--min-severity", choices=["high", "medium", "low"], default="medium")
    s.add_argument("--no-env", action="store_true", help="skip this process's environment")
    s.add_argument("--no-profiles", action="store_true", help="skip shell profiles in $HOME")
    s.add_argument("--json", action="store_true", help="machine-readable output (still no values)")
    s.set_defaults(fn=cmd_scan)
    s = sub.add_parser("edit", help="edit a secret in $EDITOR (decrypted only in a temp file)")
    s.add_argument("file")
    s.set_defaults(fn=cmd_edit)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
