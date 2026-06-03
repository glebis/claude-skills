---
name: vault
description: >-
  Set up and verify the CONFIDE THREE LOCKS for storing RED (real, identifiable) session
  data at rest — device FileVault, a dedicated encrypted store, and per-file sops/age
  encryption. Use when the user says "set up confide vault", "encrypt my session data",
  "three locks", "secure store for transcripts", "sops/age for RED data", or asks how to
  store real therapy/coaching transcripts safely. NON-DESTRUCTIVE: it CHECKS each lock's
  status and prints the EXACT command to fix any gap; it never moves, deletes, or encrypts
  data, and never runs `fdesetup enable`/`hdiutil`/`age-keygen` without an explicit flag
  and your confirmation. Probes are read-only (`fdesetup status`, which sops/age, key path).
---

# confide:vault — the THREE LOCKS for storing RED data

Operationalizes the defense-in-depth storage posture in
`confide/docs/THREE-LOCKS.md`: real (RED) transcripts rest behind **three independent
locks**, so compromising one does not expose a client. To read a real transcript an
attacker needs the **device password** AND the **encrypted-store password** AND the
**age key** — three separate secrets, ideally held in different places.

| Lock | What | Protects against |
|---|---|---|
| **1 — Device** | FileVault full-disk encryption + strong login password + short auto-lock | a lost/stolen/USB-booted machine |
| **2 — Store** | RED in a dedicated ENCRYPTED store (encrypted APFS volume / AES-256 `.dmg`), NOT in Documents and NEVER in iCloud/Dropbox | other apps, other users, silent cloud sync |
| **3 — Per-file** | each RED file `sops`/`age`-encrypted at rest, age key stored SEPARATELY; processing in a no-network VM/container | files individually sealed; key not beside the data |

## NON-DESTRUCTIVE — read before running
- `--check` (the default) runs **only read-only probes**: `fdesetup status`,
  `shutil.which(sops/age)`, and `os.path.exists(...)`. It **never** moves, deletes, or
  encrypts data and **never** runs `fdesetup enable`, `hdiutil`, `age-keygen`, or `rm`.
- It reports each lock ✓/✗ and prints the **exact command** to fix every ✗ — for the user
  to review and run themselves.
- `--init-age` generates an age key **only** with that explicit flag, and **never**
  overwrites an existing key.
- `--init-store PATH` only **prints** the encrypted-store creation command; it does not
  execute disk-image creation. Refuses cloud-synced paths.
- Never move, encrypt, or delete the user's RED data on their behalf without explicit
  confirmation. There is no destructive default.

## Run it

```bash
# default = read-only status check + checklist with fix commands
python3 skills/vault/scripts/vault.py --check
python3 skills/vault/scripts/vault.py --json            # structured status dict

# point at your own RED store to verify it's not cloud-synced
python3 skills/vault/scripts/vault.py --store-path ~/CONFIDE-RED.dmg

# optional, GUARDED helpers (explicit flags only)
python3 skills/vault/scripts/vault.py --init-age        # make an age key (never overwrites)
python3 skills/vault/scripts/vault.py --init-store ~/CONFIDE-RED.dmg   # prints the hdiutil command
```

`lock_status()` is importable and returns:

```
{
  "device":  {"filevault": bool},
  "store":   {"present": bool, "path": str|None, "cloud_synced": bool, "safe": bool},
  "perfile": {"sops": bool, "age": bool, "key": bool, "key_path": str|None}
}
```

## How to help the user

1. Run `--check` and read back the ✓/✗ checklist.
2. For each ✗, show the printed fix command (e.g. `sudo fdesetup enable`,
   `age-keygen -o ~/.config/confide/age.key`,
   `hdiutil create -encryption AES-256 … ~/CONFIDE-RED.dmg`) and let the user run it.
3. Confirm the RED store is **not** inside iCloud/Dropbox (`store.safe`).
4. Show the sops/age encrypt+decrypt recipe (printed in the checklist) so RED stays
   ciphertext at rest and is decrypted only in-memory inside the isolated pipeline
   (`confide/docs/ISOLATION.md`). Only GREEN (redacted) output ever leaves the machine.

See `confide/docs/THREE-LOCKS.md` (the model + checklist) and `confide/docs/ISOLATION.md`
(red/green flow, no-network VM/container).
