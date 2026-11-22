# Syncthing transport

Syncthing moves **public keys and encrypted files only**. Private keys never go into the mesh folder,
and `.stignore` blocks the usual private-key and plaintext file names as a second line of defence.

## Recommended: two folders

| Folder | Contents | Admin machine | Other machines |
|---|---|---|---|
| `secrets-mesh` | `.sops.yaml`, `secrets/`, `.sopsmesh.json` | **Send Only** | **Receive Only** |
| `secrets-mesh/recipients` (shared as its own folder) | `*.pub` | Send & Receive | Send & Receive |

Why: with one Send & Receive folder, any peer could edit `.sops.yaml` and add its own key. sopsmesh
detects that (`status` warns, `sync` rewrites it from the admin's approvals), but anyone who edits a
secret before the admin notices would encrypt to the rogue key. Receive Only on peers removes that window.

Setup:
1. Admin: `sopsmesh init ~/secrets-mesh`, `sopsmesh keygen`.
2. Syncthing UI on admin → Add Folder `~/secrets-mesh`, type *Send Only*, share with each device.
3. Add Folder `~/secrets-mesh/recipients`, type *Send & Receive*, share with each device.
   Syncthing does **not** skip a nested shared folder by itself: on **every** device add the line
   `/recipients` to `~/secrets-mesh/.stignore`, so the outer share leaves it to the inner one.
4. On each peer accept both shares: outer as *Receive Only*, `recipients` as *Send & Receive*,
   at the same relative path, and add `/recipients` to the outer `.stignore` there too.
5. Peer: `cd ~/secrets-mesh && sopsmesh keygen`. The `.pub` file syncs to the admin.
6. Admin: `status` → verify fingerprint by phone → `approve` → `sync`. The re-wrapped files sync out.

## What the hardened layout does under attack (tested, MacBook ↔ Mac Mini, Syncthing 2.x)

| A peer… | Result |
|---|---|
| edits `.sops.yaml` to add its own key | Stays local: Receive Only marks it as a local change (`receiveOnlyChangedFiles`), the admin never receives it. Undo on the peer: *Revert Local Changes* in the UI or `POST /rest/db/revert?folder=<id>` |
| swaps the admin's `recipients/<admin>.pub` | Reaches the admin, `status` shows `KEY CHANGED`, `sync` keeps the approved key and restores the admin's own `.pub` |
| drops a new `rogue.pub` | Shows as `pending`, never added without `approve` |

## File watcher misses changes

Syncthing's watcher sometimes doesn't see a new file (seen with the Homebrew service started over SSH),
and the fallback rescan runs hourly. `sopsmesh keygen`, `sync` and `encrypt` therefore ask the local
Syncthing to rescan the mesh folders through its REST API (API key read from `syncthing cli`, never
printed). If nothing arrives on the other side, rescan there too: Syncthing UI → folder → *Rescan*.

## Simple: one folder

Fine for one person's own machines on a trusted network. Share `~/secrets-mesh` as Send & Receive
everywhere. Run `sopsmesh status` on the admin after any unexpected change.

## Things Syncthing does that matter here

- **Versioning** (`.stversions/`): keeps old copies. Harmless for encrypted files and public keys, which
  is one more reason private keys must never be in the folder.
- **Conflicts** (`*.sync-conflict-*`): sopsmesh ignores conflict copies of `.pub` and secret files and
  warns. Resolve by hand: keep the newer one, trash the conflict copy.
- **Revocation**: removing a machine from Syncthing stops future syncs but doesn't remove what it
  already has. Always `sopsmesh revoke` **and** rotate the secrets.

Install: macOS `brew install syncthing && brew services start syncthing` · Debian/Ubuntu
`sudo apt install syncthing && systemctl --user enable --now syncthing` · Windows
`winget install --id Syncthing.Syncthing` (or SyncTrayzor for a tray app).
