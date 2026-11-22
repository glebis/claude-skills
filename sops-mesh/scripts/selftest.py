#!/usr/bin/env python3
"""End-to-end self-test for sopsmesh on THIS machine. Standard library only.

Simulates an admin and a peer machine in a temporary folder, each with its own config dir, and runs
the whole lifecycle plus tampering checks. Never prints a secret value. Never touches your real
sopsmesh config or your real key-store entry.

  python3 selftest.py            # both simulated machines use the portable 0600-file store
  python3 selftest.py --native   # the peer uses this OS's real store (Keychain / Credential Manager /
                                 # libsecret) under a throwaway entry name, removed afterwards
  python3 selftest.py --keep     # keep the temp folder for inspection

Exit code 0 = all checks passed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "sopsmesh.py"
IS_WIN = os.name == "nt"
RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> bool:
    RESULTS.append((ok, name, detail))
    print(f"  {'✓' if ok else '✗'} {name}" + (f"  ({detail})" if detail and not ok else ""))
    return ok


class Machine:
    """One simulated machine: its own config dir (XDG_CONFIG_HOME / APPDATA)."""

    def __init__(self, root: Path, name: str, service: str):
        self.name, self.cfg = name, root / f"cfg-{name}"
        self.cfg.mkdir(parents=True)
        self.env = {**os.environ, "SOPSMESH_SERVICE": service}
        self.env.pop("SOPS_AGE_KEY", None)
        self.env["APPDATA" if IS_WIN else "XDG_CONFIG_HOME"] = str(self.cfg)

    def sm(self, *args: str, cwd: Path, inp: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(TOOL), *args], cwd=cwd, env=self.env,
                              capture_output=True, text=True, input=inp, timeout=120)


PROBE = ("import os;print('CHILD', 'DB_PASSWORD=' + ('SET' if os.environ.get('DB_PASSWORD') else 'unset'),"
         "'SOPS_AGE=' + (','.join(k for k in os.environ if k.startswith('SOPS_AGE')) or 'none'))")


def probe(m: Machine, mesh: Path) -> str:
    r = m.sm("run", "--secrets", "secrets/app.env", "--", sys.executable, "-c", PROBE, cwd=mesh)
    line = next((l for l in r.stdout.splitlines() if l.startswith("CHILD")), "")
    return line or ("FAILED: " + (r.stderr.strip().splitlines() or ["no output"])[-1][:160])


def cleanup_native(backend: str, service: str) -> None:
    if backend == "keychain":
        subprocess.run(["security", "delete-generic-password", "-s", service], capture_output=True)
    elif backend == "libsecret":
        subprocess.run(["secret-tool", "clear", "service", service, "account", "age"], capture_output=True)
    elif backend == "credman":
        import importlib.util
        spec = importlib.util.spec_from_file_location("sopsmesh", TOOL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        mod._win_cred()[2](service)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--native", action="store_true", help="peer uses this OS's real key store")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    for tool in ("sops", "age-keygen"):
        if not shutil.which(tool, path=os.environ.get("PATH", "") + os.pathsep + "/opt/homebrew/bin"):
            print(f"✗ {tool} not found: run `sopsmesh doctor` first")
            return 2

    root = Path(tempfile.mkdtemp(prefix="sopsmesh-selftest-"))
    service = f"sopsmesh-selftest-{uuid.uuid4().hex[:8]}"
    admin, peer = Machine(root, "admin", service), Machine(root, "peer", service)
    mesh = root / "mesh"
    native = None
    print(f"sopsmesh self-test · {sys.platform} · Python {sys.version.split()[0]} · temp {root}")
    try:
        print("\nSetup")
        check(admin.sm("init", str(mesh), cwd=root).returncode == 0, "init mesh")
        r = admin.sm("keygen", "--backend", "file", "--name", "admin", cwd=mesh)
        check(r.returncode == 0 and "admin" in r.stdout, "admin keygen (file), auto-approved", r.stderr[-200:])
        plain = root / "plain.env"
        plain.write_text(f"DB_PASSWORD={secrets.token_urlsafe(18)}\nAPP_MODE=test\n", encoding="utf-8")
        r = admin.sm("encrypt", str(plain), "--name", "app.env", cwd=mesh)
        plain.unlink()
        enc = mesh / "secrets" / "app.env"
        check(r.returncode == 0 and enc.exists() and "ENC[AES256_GCM" in enc.read_text(), "encrypt", r.stderr[-200:])

        print("\nAgent injection")
        out = probe(admin, mesh)
        check("DB_PASSWORD=SET" in out and "SOPS_AGE=none" in out, "child gets secret, no SOPS_AGE_* vars", out)
        r = admin.sm("key", cwd=mesh)
        check(r.returncode != 0 and not r.stdout.strip(), "`key` refuses a non-sops caller")

        print("\nSecond machine")
        if a.native:
            avail = {"darwin": "keychain", "win32": "credman"}.get(sys.platform)
            if sys.platform.startswith("linux") and shutil.which("secret-tool") and os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
                avail = "libsecret"
            if not avail:
                print("  - no native store on this machine; using file")
            native = avail
        backend = native or "file"
        r = peer.sm("keygen", "--backend", backend, "--name", "peer", cwd=mesh)
        check(r.returncode == 0, f"peer keygen ({backend})", r.stderr[-300:])
        st = admin.sm("status", cwd=mesh).stdout
        check(bool(re.search(r"^peer .*pending", st, re.M)), "peer shows as pending")
        check(probe(peer, mesh).startswith("FAILED"), "peer can't decrypt before approval")

        pub = next(l for l in (mesh / "recipients" / "peer.pub").read_text().splitlines() if l.startswith("age1"))
        check(admin.sm("approve", "peer", cwd=mesh).returncode != 0, "approve without fingerprint refused")
        check(admin.sm("approve", "peer", "--fingerprint", "age1", cwd=mesh).returncode != 0,
              "approve with trivial 'age1' fingerprint refused")
        check(admin.sm("approve", "peer", "--fingerprint", "age1qqqqqqqqqqqqqq", cwd=mesh).returncode != 0,
              "approve with wrong fingerprint refused")
        check(admin.sm("approve", "peer", "--fingerprint", pub[-6:], cwd=mesh).returncode == 0,
              "approve with correct fingerprint")
        r = admin.sm("sync", cwd=mesh)
        check(r.returncode == 0, "sync re-wraps for peer", r.stderr[-200:])
        out = probe(peer, mesh)
        check("DB_PASSWORD=SET" in out and "SOPS_AGE=none" in out, f"peer decrypts via {backend}", out)

        print("\nTampering")
        rogue = subprocess.run(["age-keygen"], capture_output=True, text=True,
                               env={**os.environ, "PATH": os.environ.get("PATH", "") + os.pathsep + "/opt/homebrew/bin"})
        rogue_pub = re.search(r"age1[0-9a-z]+", rogue.stdout + rogue.stderr).group(0)
        sy = mesh / ".sops.yaml"
        sy.write_text(re.sub(r"(age1[0-9a-z]+)\n(?!\s+age1)", rf"\1,\n      {rogue_pub}\n", sy.read_text(), count=1))
        check("never approved" in admin.sm("status", cwd=mesh).stdout, "status flags rogue key in .sops.yaml")
        admin.sm("sync", cwd=mesh)
        check(rogue_pub not in sy.read_text(), "sync removes the rogue key")

        own = mesh / "recipients" / "admin.pub"
        own.write_text(f"# swapped\n{rogue_pub}\n")
        check("KEY CHANGED" in admin.sm("status", cwd=mesh).stdout, "status flags a swapped .pub")
        admin.sm("sync", cwd=mesh)
        check(rogue_pub not in own.read_text(), "sync restores the admin's own .pub")
        (mesh / "recipients" / "rogue.pub").write_text(rogue_pub + "\n")
        admin.sm("sync", cwd=mesh)
        check(rogue_pub not in sy.read_text(), "unapproved rogue.pub is not added")

        print("\nScan")
        fx = root / "fixture"
        (fx / "app").mkdir(parents=True)
        val = secrets.token_urlsafe(24)
        (fx / "app" / ".env").write_text(f"WEBHOOK_SECRET={val}\nDEBUG=true\n")
        (fx / "app" / ".env.example").write_text(f"SESSION_SECRET={secrets.token_urlsafe(24)}\n")
        (fx / "secrets.yaml").write_text("sops:\n  note: plaintext, not encrypted\napi_token: " + secrets.token_hex(20) + "\n")
        r = admin.sm("scan", str(fx), "--no-env", "--no-profiles", "--json", cwd=root)
        found = {f["name"] for f in json.loads(r.stdout or "[]")}
        check("WEBHOOK_SECRET" in found, "scan finds a secret in .env")
        check("SESSION_SECRET" not in found, "scan skips .env.example")
        check("api_token" in found, "a plaintext file with a `sops:` key isn't mistaken for encrypted")
        check(val not in r.stdout and val not in r.stderr, "scan output contains no values")

        print("\nRevoke")
        r = admin.sm("revoke", "peer", cwd=mesh)
        check(r.returncode == 0, "revoke peer", r.stderr[-200:])
        check(probe(peer, mesh).startswith("FAILED"), "peer can no longer decrypt")
    finally:
        if native:
            cleanup_native(native, service)
        if a.keep:
            print(f"\nKept {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)

    failed = [n for ok, n, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed" + (f" · FAILED: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
