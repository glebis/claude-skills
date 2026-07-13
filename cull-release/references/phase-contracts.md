# Cull release phase contracts

## Runtime

Resolve Cull from the current repository when origin matches `glebis/cull`, then
absolute `CULL_REPO`, then `$HOME/ai_projects/cull`. Require
`npm run release:cull -- --help`. Parse exactly one JSON envelope from stdout;
stderr is operator logging. Exit codes: `2` input/config, `3` blocked gate, `4`
external action failure, `5` inconsistent or recovery-required state.

An explicit “Release Cull patch|minor|major” request authorizes the full cycle,
including publication after all gates. It never authorizes bypassing a gate.

## States

| Accepted state | Phase and command | Required evidence | Legal next state | Mutation boundary | Failure route |
| --- | --- | --- | --- | --- | --- |
| `requested` | Check: `npm run release:cull -- check --bump KIND --json` | version, source SHA, sync, disk, toolchains, gates | `checked` | none | `rerun-check` |
| `checked` | Prepare: `npm run release:cull -- prepare ... --dry-run --json`, then real prepare | bound plan, notes, compatibility review, release commit | `prepared` | release-owned files and one commit | `prepare-new-version` |
| `prepared` | Publish preflight and one annotated-tag push | pushed main commit, exact version, tag object | `tagged` | one new tag | `prepare-new-version` |
| `tagged` | Watch tag-bound Release workflow | authenticated run and signed inventory | `draft-built` | workflow-owned empty draft only after verification | `watch-build` |
| `draft-built` | Secret-free exact artifact verification | updater signature, notarization, inventory, SHA-256, gate evidence | `artifact-verified` | no public mutation | `verify-artifact` |
| `artifact-verified` | Guarded workflow publication | public digest equality, provenance, immutable tag | `published` | publish exact verified assets | `publish-verified-artifacts` |
| `published` | Provenance-bound Homebrew workflow | public provenance, exact DMG SHA-256, audit/install/launch | `homebrew-promoted` | one cask commit or idempotent no-op | `promote-homebrew` |
| `homebrew-promoted` | cull-release-verify | release, updater, trust, cask, install/launch evidence | `post-publish-verified` | none by default | `prepare-patch-plan` |
| `post-publish-verified` | Report complete | all prior immutable evidence | terminal | none | `prepare-patch-plan` if later evidence fails |

Local `.release-state/<version>.json` is a resumability cache. Re-derive state
from external evidence before advancing. Never delete or rewrite a tag/release,
clobber assets, force-push, or silently publish a recovery patch.
