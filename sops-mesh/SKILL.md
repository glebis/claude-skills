---
name: sops-mesh
description: This skill should be used to share SOPS + age secrets across someone's machines (macOS, Linux, Windows, CI), with one private key per machine in the strongest local store (Secure Enclave, Keychain, Credential Manager, libsecret, 0600 file), public keys exchanged over Syncthing or git, and secrets injected into AI agents that never see the keys. Triggers include "encrypt my secrets", "set up sops", "share API keys between my machines", "stop agents seeing my keys", "sync secrets with Syncthing", "scan for plaintext secrets", adding or revoking a machine, "зашифровать секреты", "синхронизировать ключи", "спрятать ключи от агента".
---

# sops-mesh

One CLI, `scripts/sopsmesh.py`, runs the same on macOS, Linux and Windows (Python 3.8+, standard library
only). Invoke it as `python3 <skill>/scripts/sopsmesh.py <command>` (Windows: `py <skill>\scripts\sopsmesh.py`).
Below, `sopsmesh` means that invocation.

## The model (explain this to the user before setup)

- **One private key per machine, never copied, never synced, never printed.** It lives in the best
  store that machine has. Secrets are shared by encrypting them to every machine's PUBLIC key.
- **Only public keys and encrypted files travel** (Syncthing or git). If the user asks to sync private
  keys, push back: that puts a copy on every disk, in Syncthing's `.stversions` and conflict files, and
  is impossible for Secure Enclave keys.
- **A machine gets access only after a human approves its key** on the admin machine. Approvals live
  outside the shared folder, so a peer that can write to the folder can't grant itself access.
- **Agents get secrets through `sopsmesh run -- <cmd>`**: values go into one child process's
  environment; the child never sees `SOPS_AGE_*`, the key file or the key command.

## Workflow

### 1. Check the machine
Run `sopsmesh doctor`: OS, tools, available key stores, a recommendation, exact install commands.
Install what's missing (ask first; Windows: prefer `winget`). Then run `python3 <skill>/scripts/selftest.py`
on any platform not listed as tested in `references/tested.md`, and report its result before relying on it.

### 2. Interview, then plan
Ask in one panel with the host's question tool, not one question at a time in chat:

1. Which machines will share secrets? Per machine: name, OS, kind (laptop/desktop/server/CI), is someone
   at its screen to approve prompts, Apple Silicon/T2 (Mac), desktop session (Linux).
2. Which machine is the admin (approves new keys)? Usually the main laptop.
3. How do files travel: Syncthing, git, or both?
4. Scan for plaintext secrets to migrate (step 6)?

Write the answers to JSON (schema: `references/plan-answers.md`) and run `sopsmesh plan --answers <file>`.
Show the user the plan table: one key store per machine, with the reason.

### 3. Create the mesh (admin machine)
```
sopsmesh init ~/secrets-mesh && cd ~/secrets-mesh
sopsmesh keygen --backend <store from plan>     # first key = admin, approved automatically
```
Set up transport. Syncthing: follow `references/syncthing.md` (two-folder layout). Git: a PRIVATE repo;
the mesh already has `.gitignore`.

### 4. Each other machine
Inside the synced folder run `sopsmesh keygen --backend <store from plan>` (`--unattended` on Macs nobody
sits at). It writes only `recipients/<name>.pub` and prints a fingerprint for the owner to read to the admin.
Run keygen **in a local terminal on that machine, not over SSH**, for Keychain and Secure Enclave: over SSH
the login keychain may be locked, and Secure Enclave prompts appear on the remote screen.

### 5. Admin approves
```
sopsmesh status                                          # pending keys, tampering warnings
sopsmesh approve <name> --fingerprint <≥12 chars after age1…, or the last ≥6>
sopsmesh sync                                            # rewrites .sops.yaml, re-wraps every secret
```
`approve` refuses without a matching fingerprint. Get it from the key's owner through a second channel
(phone, in person), never from the shared folder. Use `--skip-fingerprint-check` only for a machine the
user just set up themselves. If the admin key is in the Secure Enclave, `sync` asks for the password
once per secret file.

### 6. Put secrets in, optionally after a scan
```
sopsmesh scan ~/projects            # env vars, shell profiles, .env-like files; names and lengths only
sopsmesh encrypt path/to/.env --name app.env    # then move the plaintext to the Trash
sopsmesh edit secrets/app.env       # later edits, decrypted only in a temp file
```
Secrets exported in shell profiles are the worst case: every program, agents included, inherits them.
Recommend moving each into the mesh, deleting the `export` line, and rotating anything an agent saw.

### 7. Use secrets
```
sopsmesh run --secrets secrets/app.env -- python3 agent.py
sopsmesh run --only OPENAI_API_KEY -- my-agent
```
Nested YAML/JSON keys become `PARENT_CHILD`; lists of scalars become comma-separated values.

### Revoke
`sopsmesh revoke <name>`, then **rotate the real secrets**: the machine may keep copies of old values.

## Agent guardrails

- Never run `sops decrypt` to stdout, `sopsmesh key`, `security find-generic-password -w`,
  `secret-tool lookup`, or read a key file.
- `sopsmesh key` refuses callers other than sops, but it is defence in depth, not a boundary: any
  process running as the user can make sops its parent. The real protections are the deny rules in
  `assets/claude-settings.json` (propose adding them to the project's `.claude/settings.json`) and, on
  Macs with someone present, the Secure Enclave store.
- Never print or `echo` a secret to check it; check presence (`SET` / `unset`).
- Never write a secret anywhere unencrypted, and never paste one into chat.

## Resources

| File | Read when |
|---|---|
| `references/platforms.md` | installing tools, choosing or debugging a key store, Secure Enclave on macOS < 26, Windows |
| `references/syncthing.md` | setting up Syncthing, conflicts, files not arriving, tampering behaviour |
| `references/plan-answers.md` | writing the JSON for `sopsmesh plan --answers` |
| `references/tested.md` | deciding whether a platform/store is verified or needs `selftest.py` first |
| `scripts/selftest.py` | verifying a new platform: `--native` also tests the OS key store (throwaway entry) |
| `assets/claude-settings.json` | deny rules that keep agents away from keys |

Default store per machine: Secure Enclave (Mac, someone present) · Keychain (Mac, unattended) ·
Credential Manager (Windows) · libsecret (Linux desktop) · 0600 file (Linux server) · CI secret store (CI).
