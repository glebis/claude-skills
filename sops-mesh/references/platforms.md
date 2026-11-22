# Platforms and key stores

## Tools

| | macOS | Debian/Ubuntu | Windows |
|---|---|---|---|
| Python 3.8+ | preinstalled / `brew install python` | preinstalled | `winget install Python.Python.3.12` |
| sops ≥ 3.10 | `brew install sops` | GitHub release `.deb` (apt is often old) | `winget install --id Mozilla.SOPS` or `scoop install sops` |
| age | `brew install age` | `sudo apt install age` | `winget install --id FiloSottile.age` or `scoop install age` |

If a winget id doesn't resolve, `winget search sops` / `winget search age` shows the current one.
sops ≥ 3.10 is required for `SOPS_AGE_KEY_CMD` (used by Keychain, Credential Manager and libsecret).

## Key stores

### macOS Secure Enclave (`se`)
- Key is generated inside the chip and can't be exported. The identity file
  (`AGE-PLUGIN-SE-1…`) is the key wrapped by the chip's hardware key: useless on any other machine.
- Every decrypt shows a password / Touch ID prompt **on that Mac's screen**. Agents over SSH can't answer.
- Needs `age-plugin-se`. Homebrew ships ≥ 0.2, which requires **macOS 26**. On macOS 13–15 build
  v0.1.4 from source (Xcode Command Line Tools):
  ```
  git clone --depth 1 --branch v0.1.4 https://github.com/remko/age-plugin-se ~/src/age-plugin-se
  cd ~/src/age-plugin-se && swift build -c release && mkdir -p ~/.local/bin && cp .build/release/age-plugin-se ~/.local/bin/
  ```
- Encrypting to an `age1se1…` recipient also needs the plugin on the encrypting machine.
- Lost Mac = lost key. Keep at least one other recipient.

### macOS Keychain (`keychain`)
- Stored with `security -i` (key passed on stdin, never in the process list), read via
  `SOPS_AGE_KEY_CMD` → `sopsmesh key`.
- Items created by `security` trust `security` itself, so reads don't prompt. Any process running as the
  user can read it: rely on agent deny rules.
- Items made with `security` don't sync through iCloud Keychain.
- Over SSH the login keychain may be locked: run keygen in a local terminal.

### Windows Credential Manager (`credman`)
- Generic credential `sopsmesh-age`, written/read through `advapi32` (`CredWriteW`/`CredReadW`) via ctypes.
  Encrypted with DPAPI, bound to the Windows user. Visible in Control Panel → Credential Manager.
- No prompt on read. Any process running as the user can read it.
- Needs **sops ≥ 3.12**: on Windows `sopsmesh key` has no `ps` to check its caller, so it only answers when
  sops sets `SOPS_AGE_RECIPIENT`, which sops passes to the key command from 3.12 on.
- sops runs `SOPS_AGE_KEY_CMD` without a shell: it splits the string with `google/shlex` (POSIX quoting)
  and executes it directly, so the single-quoted Windows path that sopsmesh writes is parsed correctly.
- The `file` backend on Windows strips inherited ACLs with `icacls` so only the current user can read the key.
- Not yet verified on real Windows: run `py scripts\selftest.py --native` before relying on it.

### Linux libsecret (`libsecret`)
- `secret-tool store/lookup service sopsmesh-age account age`. Needs a Secret Service (GNOME Keyring,
  KWallet) and a desktop session; headless servers usually have neither.

### File (`file`)
- `~/.config/sopsmesh/age.key`, mode 0600, directory 0700. For headless Linux and servers.
- Weakest option: anyone with the account (or root) can read it. Prefer a dedicated user for agents.
- Alternatives worth considering for servers: `age-plugin-tpm` (TPM 2.0), `age-plugin-yubikey`.

### CI (`ci`)
- On the admin: `sopsmesh keygen --backend file --name ci --export` prints the key ONCE. Put it into
  the CI secret store as `SOPS_AGE_KEY`, approve `ci`, sync. Nothing is stored locally.
