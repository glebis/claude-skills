# `COMPATIBILITY.md` structure & upkeep

The living contract. The skill updates it at **step 5** of every release.

## Sections

1. **Promise** — prose, Go-1 style: what `X.y.z` guarantees, what forces a major.
2. **Surfaces** table — the declared public API:

   | Surface | Tier | Since | Mode | Notes |
   |---|---|---|---|---|
   | Database schema | stable | 0.1.0 | BACKWARD_TRANSITIVE | migrations additive-only |
   | MCP token API | preview | — | unversioned | no version handshake yet → may change |
   | Export formats | stable | 0.1.0 | forward-compatible | unknown fields ignored |

3. **Deprecations** table — nothing is removed without a window:

   | Item | Deprecated in | Removable in | Replacement |
   |---|---|---|---|

4. **1.0 readiness gate** — the checklist that defines "stable enough to promise".

## Update rules (per release)

- **Tier change?** edit the surface row + note the version.
- **New deprecation?** add a row (item / deprecated-in / removable-in / replacement);
  signal on the wire with [RFC 9745](https://www.rfc-editor.org/rfc/rfc9745.html) /
  [RFC 8594](https://www.rfc-editor.org/rfc/rfc8594.html) where applicable.
- **Breaking a `stable` surface?** the release MUST be a `major` (the engine
  enforces it). Prefer keeping young surfaces at `preview`.
- Always stamp `Last updated: <version> (<date>)`.

Promotion `preview → stable` happens only when that surface's 1.0-gate items pass
(e.g. MCP gains a `protocolVersion` handshake + a deprecation policy).
