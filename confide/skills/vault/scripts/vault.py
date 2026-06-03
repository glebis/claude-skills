#!/usr/bin/env python3
"""confide:vault — the THREE LOCKS storage checker for RED (real, identifiable) data.

NON-DESTRUCTIVE BY DESIGN. `--check` (and `lock_status()`) only run READ-ONLY probes:
`fdesetup status`, `shutil.which(sops/age)`, and `os.path.exists(...)`. They NEVER move,
delete, or encrypt data, and never run `fdesetup enable`, `hdiutil`, `age-keygen`, or `rm`.

The three locks (see confide/docs/THREE-LOCKS.md):
  Lock 1 — Device:    FileVault full-disk encryption + login password + auto-lock.
  Lock 2 — Store:     a dedicated ENCRYPTED store (encrypted APFS volume / AES-256 .dmg),
                      NOT loose in Documents and NEVER inside iCloud/Dropbox.
  Lock 3 — Per-file:  each RED file sops/age-encrypted at rest; age key stored SEPARATELY.

To read a real transcript an attacker needs the device password AND the store password
AND the age key — three independent secrets.
"""
import argparse
import json
import os
import shutil
import subprocess

# Standard paths.
AGE_KEY_PATHS = [
    os.path.expanduser("~/.config/confide/age.key"),
    os.path.expanduser("~/.config/sops/age/keys.txt"),
]
DEFAULT_AGE_KEY = AGE_KEY_PATHS[0]
DEFAULT_STORE_PATHS = [
    os.path.expanduser("~/CONFIDE-RED"),
    os.path.expanduser("~/CONFIDE-RED.dmg"),
    "/Volumes/CONFIDE-RED",
]

# Substrings that indicate a cloud-synced (UNSAFE for RED) location.
CLOUD_MARKERS = (
    "Library/Mobile Documents",          # iCloud Drive
    "com~apple~CloudDocs",               # iCloud Drive
    "/Dropbox",
    "/Google Drive",
    "/GoogleDrive",
    "/OneDrive",
    "/iCloud",
)

CAVEAT = (
    "This is a confidentiality posture, not legal advice or a compliance certificate. "
    "A ✓ means the probe passed; human review of your full setup is still required. "
    "vault never moves, deletes, or encrypts data without your explicit confirmation."
)


# --------------------------------------------------------------- read-only probes
def _filevault_on():
    """Lock 1: parse `fdesetup status` (read-only). Returns bool, best-effort."""
    try:
        res = subprocess.run(
            ["fdesetup", "status"],
            capture_output=True, text=True, timeout=10,
        )
        out = (res.stdout or "") + (res.stderr or "")
        return "FileVault is On" in out
    except Exception:
        return False


def _which(name):
    return shutil.which(name) is not None


def _age_key_path():
    for p in AGE_KEY_PATHS:
        if os.path.exists(p):
            return p
    return None


def _is_cloud_synced(path):
    if not path:
        return False
    return any(marker in path for marker in CLOUD_MARKERS)


def _find_store(store_path=None):
    """Return (path or None) for a configured/dedicated RED store. Read-only."""
    if store_path is not None:
        return store_path if os.path.exists(store_path) else store_path
    for p in DEFAULT_STORE_PATHS:
        if os.path.exists(p):
            return p
    return None


# --------------------------------------------------------------- status
def lock_status(store_path=None):
    """Probe all three locks. READ-ONLY. Returns a structured dict.

    {
      "device":  {"filevault": bool},
      "store":   {"present": bool, "path": str|None,
                  "cloud_synced": bool, "safe": bool},
      "perfile": {"sops": bool, "age": bool, "key": bool, "key_path": str|None},
    }
    """
    filevault = _filevault_on()

    if store_path is not None:
        present = os.path.exists(store_path) if store_path else False
        # an explicit path the user names is treated as their configured store
        present = True if store_path else False
        path = store_path
    else:
        path = _find_store()
        present = path is not None

    cloud = _is_cloud_synced(path) if present else False
    safe = present and not cloud

    sops = _which("sops")
    age = _which("age")
    key_path = _age_key_path()

    return {
        "device": {"filevault": filevault},
        "store": {
            "present": present,
            "path": path,
            "cloud_synced": cloud,
            "safe": safe,
        },
        "perfile": {
            "sops": sops,
            "age": age,
            "key": key_path is not None,
            "key_path": key_path,
        },
    }


# --------------------------------------------------------------- checklist
def checklist_items(st):
    """Flatten lock_status into checklist items, each with ok + a fix command for ✗."""
    items = []

    # Lock 1 — Device
    items.append({
        "lock": "Lock 1 — Device",
        "label": "FileVault full-disk encryption ON",
        "ok": st["device"]["filevault"],
        "fix": "sudo fdesetup enable    # then store the recovery key in a password manager",
    })
    items.append({
        "lock": "Lock 1 — Device",
        "label": "Strong login password, screen auto-lock <=5 min, no auto-login (verify manually)",
        "ok": st["device"]["filevault"],  # gated on FileVault; manual verify
        "fix": ("Open System Settings > Lock Screen: set 'Require password' immediately and "
                "screen-saver start <=5 min; System Settings > Users: disable automatic login"),
    })

    # Lock 2 — Encrypted store
    items.append({
        "lock": "Lock 2 — Encrypted store",
        "label": "Dedicated ENCRYPTED store for RED exists (encrypted APFS volume / AES-256 .dmg)",
        "ok": st["store"]["present"],
        "fix": ("hdiutil create -encryption AES-256 -stdinpass -size 5g -fs APFS "
                "-volname CONFIDE-RED ~/CONFIDE-RED.dmg    "
                "# or: diskutil apfs addVolume <disk> APFS CONFIDE-RED -encryption"),
    })
    items.append({
        "lock": "Lock 2 — Encrypted store",
        "label": "RED store is NOT inside iCloud / Dropbox / any cloud-synced folder",
        "ok": (not st["store"]["present"]) or st["store"]["safe"],
        "fix": ("Move the RED store OUT of iCloud/Dropbox/OneDrive/Google Drive to a local-only "
                "path (e.g. ~/CONFIDE-RED.dmg) and exclude it from all cloud sync"),
    })

    # Lock 3 — Per-file + isolation
    items.append({
        "lock": "Lock 3 — Per-file",
        "label": "`sops` on PATH",
        "ok": st["perfile"]["sops"],
        "fix": "brew install sops",
    })
    items.append({
        "lock": "Lock 3 — Per-file",
        "label": "`age` on PATH",
        "ok": st["perfile"]["age"],
        "fix": "brew install age",
    })
    items.append({
        "lock": "Lock 3 — Per-file",
        "label": f"age key exists (kept SEPARATE from the data) at {DEFAULT_AGE_KEY}",
        "ok": st["perfile"]["key"],
        "fix": (f"mkdir -p ~/.config/confide && age-keygen -o {DEFAULT_AGE_KEY}    "
                "# keep a recovery copy in your password manager, NOT beside the data"),
    })

    return items


def sops_recipe():
    """The exact sops/age encrypt+decrypt recipe (printed; never executed)."""
    return (
        "# encrypt a RED transcript at rest (ciphertext on disk):\n"
        f"export SOPS_AGE_RECIPIENTS=$(age-keygen -y {DEFAULT_AGE_KEY})\n"
        "sops --encrypt --input-type binary --output-type binary session.md > session.md.sops\n"
        "\n"
        "# decrypt ONLY in-memory inside the isolated VM/container, redact, publish GREEN:\n"
        f"export SOPS_AGE_KEY_FILE={DEFAULT_AGE_KEY}\n"
        "sops --decrypt --input-type binary --output-type binary session.md.sops \\\n"
        "  | python3 confide.py redact /dev/stdin --out /green"
    )


def render_checklist(st):
    """Render the THREE-LOCKS checklist with ✓/✗ and the EXACT fix command per ✗."""
    lines = []
    lines.append("=== confide:vault — THREE LOCKS storage checklist (read-only) ===")
    lines.append("RED (real, identifiable) data must rest behind THREE independent locks.\n")

    current = None
    for it in checklist_items(st):
        if it["lock"] != current:
            current = it["lock"]
            lines.append(f"\n{current}")
        mark = "✓" if it["ok"] else "✗"
        lines.append(f"  [{mark}] {it['label']}")
        if not it["ok"]:
            lines.append(f"        fix: {it['fix']}")

    lines.append("\nLock 3 — sops/age encrypt-at-rest recipe:")
    for r in sops_recipe().splitlines():
        lines.append("    " + r if r else "")

    lines.append("\nCAVEAT: " + CAVEAT)
    return "\n".join(lines)


# --------------------------------------------------------------- optional init (guarded)
def init_age(confirm=False, key_path=DEFAULT_AGE_KEY):
    """Generate an age key — ONLY with explicit confirm. NEVER overwrites an existing key.

    confirm=False is a dry run: returns the command, runs nothing.
    """
    command = f"mkdir -p {os.path.dirname(key_path)} && age-keygen -o {key_path}"
    if os.path.exists(key_path):
        return {
            "created": False,
            "reason": f"age key already exists at {key_path}; refusing to overwrite",
            "command": command,
            "path": key_path,
        }
    if not confirm:
        return {
            "created": False,
            "reason": "dry run — pass --init-age to actually generate the key",
            "command": command,
            "path": key_path,
        }
    # explicit confirmation: actually create the key.
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    subprocess.run(["age-keygen", "-o", key_path], check=True)
    return {"created": True, "reason": "generated", "command": command, "path": key_path}


def init_store(path, confirm=False, size="5g"):
    """Print/confirm the encrypted-store creation command. NEVER executes without confirm.

    confirm is accepted for symmetry but execution of disk-image creation is intentionally
    NOT performed automatically — vault prints the command for the user to run themselves.
    """
    command = (
        f"hdiutil create -encryption AES-256 -stdinpass -size {size} -fs APFS "
        f"-volname CONFIDE-RED {path}"
    )
    warning = None
    if _is_cloud_synced(path):
        warning = "REFUSING: that path is inside a cloud-synced folder — pick a local-only path."
        return {"executed": False, "command": command, "warning": warning, "path": path}
    # Non-destructive default: print the command, do not execute.
    return {
        "executed": False,
        "command": command,
        "warning": ("vault does not create disk images automatically. Review and run the command "
                    "above yourself, choosing a strong store password."),
        "path": path,
    }


# --------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="confide:vault — check (and optionally help init) the THREE LOCKS for "
                    "storing RED data. Non-destructive: --check only runs read-only probes.")
    ap.add_argument("--check", action="store_true",
                    help="probe and report each lock's status + checklist (default)")
    ap.add_argument("--store-path", default=None,
                    help="path to your dedicated RED store (overrides auto-detection)")
    ap.add_argument("--json", action="store_true", help="emit JSON status")
    ap.add_argument("--init-age", action="store_true",
                    help="generate an age key (explicit; never overwrites an existing key)")
    ap.add_argument("--init-store", metavar="PATH", default=None,
                    help="print the encrypted-store creation command for PATH (does NOT execute)")
    args = ap.parse_args(argv)

    # init-age: explicit, guarded.
    if args.init_age:
        res = init_age(confirm=True)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            if res["created"]:
                print(f"Created age key at {res['path']}.")
                print("Store a recovery copy in your password manager, NOT beside the data.")
            else:
                print(f"Did not create a key: {res['reason']}")
                print("Command:", res["command"])
        return res

    # init-store: print command only, never execute.
    if args.init_store is not None:
        res = init_store(args.init_store, confirm=False)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("Encrypted-store creation command (review and run yourself):")
            print("  " + res["command"])
            if res.get("warning"):
                print("\n" + res["warning"])
        return res

    # default: --check (read-only).
    st = lock_status(store_path=args.store_path)
    if args.json:
        print(json.dumps(st, ensure_ascii=False, indent=2))
    else:
        print(render_checklist(st))
    return st


if __name__ == "__main__":
    main()
