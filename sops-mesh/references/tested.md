# Test log

Run `python3 scripts/selftest.py` (25 checks: lifecycle, approval rules, tampering, scan, revoke) on any
new platform; add `--native` to also exercise the OS key store under a throwaway entry name.

| Date | Platform | Python | Stores verified | How |
|---|---|---|---|---|
| 2026-11-22 | macOS 27, Apple Silicon | 3.13.9 | file, Keychain, Secure Enclave (age-plugin-se 0.2.1) | selftest 25/25, `selftest --native` 25/25 (peer on real Keychain) + manual |
| 2026-11-22 | macOS 15.3, Apple Silicon | 3.9 | file, Secure Enclave (age-plugin-se 0.1.4 built from source) | selftest 25/25 + manual |
| 2026-11-22 | Ubuntu 24.04 headless (x86_64) | 3.12 | file | selftest 25/25 + manual |
| 2026-11-22 | Syncthing 2.x, MacBook ↔ Mac Mini | n/a | two-folder layout, three tampering attacks | manual, see syncthing.md |

## Not yet verified

- **Windows Credential Manager** (`credman`): implemented via ctypes `CredWriteW`/`CredReadW`; needs sops ≥ 3.12.
  Run `py scripts\selftest.py --native` on Windows before telling a user it works.
- **Linux libsecret**: needs a desktop session with GNOME Keyring or KWallet.
- **Windows file backend ACL** (`icacls /inheritance:r /grant:r <user>:F`).
