# `sopsmesh plan --answers` schema

```json
{
  "machines": [
    {"name": "macbook",  "os": "macos",   "kind": "laptop", "human_present": true,  "secure_enclave": true},
    {"name": "mac-mini", "os": "macos",   "kind": "server", "human_present": true,  "secure_enclave": true},
    {"name": "vps",      "os": "linux",   "kind": "server", "human_present": false, "desktop": false},
    {"name": "win-pc",   "os": "windows", "kind": "desktop","human_present": true},
    {"name": "ci",       "os": "linux",   "kind": "ci",     "human_present": false}
  ],
  "admin": "macbook",
  "transport": "syncthing"
}
```

- `os`: `macos` | `linux` | `windows`
- `kind`: `laptop` | `desktop` | `server` | `ci`
- `human_present`: someone can answer a password/Touch ID prompt on that machine's screen
- `secure_enclave` (macOS): Apple Silicon or T2. Default true.
- `desktop` (Linux): has a GNOME/KDE session with a keyring
- `transport`: `syncthing` | `git` | `both`
- names: letters, digits, `.`, `_`, `-`
