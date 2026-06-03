# Standards this skill encodes

The workflow isn't invented — each step maps to an industry standard. Learn the
one behind whatever step you're on.

| Concern | Standard | Link |
|---|---|---|
| Version math; "declare your public API" | **Semantic Versioning 2.0.0** | https://semver.org/spec/v2.0.0.html |
| A single durable compatibility promise (formulation #1) | **Go 1 Compatibility Promise** | https://go.dev/doc/go1compat |
| Maturity tiers + deprecation windows (formulation #2) | **Kubernetes API deprecation policy** | https://kubernetes.io/docs/reference/using-api/deprecation-policy/ |
| The release-readiness gate | **Google SRE Production-Readiness Review** | https://sre.google/sre-book/evolving-sre-engagement-model/ |
| Named compatibility modes (formulation #3) | **Schema-Registry compatibility** (Avro/Protobuf) | https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html |
| Consumer-driven contract tests | **Pact** · Fowler | https://docs.pact.io/ · https://martinfowler.com/articles/consumerDrivenContracts.html |
| Human changelog | **Keep a Changelog** | https://keepachangelog.com/ |
| Wire-level deprecation signalling | **RFC 9745** (Deprecation) · **RFC 8594** (Sunset) | https://www.rfc-editor.org/rfc/rfc9745.html · https://www.rfc-editor.org/rfc/rfc8594.html |
| API version negotiation (MCP servers) | **MCP `protocolVersion`** | https://modelcontextprotocol.io/specification/versioning |

## The three formulations (this skill = "compose them")

1. **The Promise** — one prose pledge (Go 1). Enforced by discipline.
2. **Tiers & Gates** — per-surface tiers + readiness gate + deprecation windows
   (Kubernetes + SRE). *This skill's default posture.*
3. **Contracts & Modes** — named modes enforced by tests in CI (Schema-Registry +
   Pact). *Grown into via `extraGate` golden/contract tests.*

Backward-compatible = new code reads old data. Forward-compatible = old code
ignores unknown new fields. `_TRANSITIVE` modes check against *all* prior
versions, not just the last.
