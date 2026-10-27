# Profile contract

The JSON configuration is project-owned, outside the shared skill. The helper needs Python's standard library only. It validates and resolves configuration; it does not trigger jobs or read provider credentials.

## Configuration and precedence

Root fields:

| Field | Meaning |
| --- | --- |
| `schemaVersion` | Currently `1` |
| `defaultBackend` | Optional; defaults to `trigger.dev` |
| `defaultProfile` | Profile selected when the caller omits a name |
| `defaults` | Optional shared profile fields |
| `profiles` | Nonempty object of named profiles |

Resolution order: shared defaults → parent profile → selected profile. Objects merge recursively; arrays and scalars replace their inherited values. A profile can name one parent using `extends`. Unknown parents and cycles are errors. The selected profile must be enabled.

Root `defaultBackend` applies only if the resolved profile has no `backend`. Explicit backend selection is preserved even when no adapter is installed. Stop and discover/implement a compatible adapter instead of guessing Trigger.dev commands for another backend.

Use `env:VARIABLE_NAME` for deployment identifiers or other non-secret settings. Resolution requires a nonempty value. Credential-like environment references are rejected; credential names belong only in `credentialsEnv`, which is never expanded. An empty model/provider can be omitted if the task does not expose or require that setting.

## Profile fields

| Field | Meaning |
| --- | --- |
| `extends` | Optional parent profile |
| `enabled` | Optional boolean, default true |
| `backend` | Execution backend; default supplied by the root |
| `projectRef` | Selected backend's project identifier |
| `environment` | Explicit target environment |
| `agent` | Metadata: `engine`, optional `provider` and `model` |
| `tasks` | Operation-to-deployed-task-ID map; `run` is conventional |
| `capabilities` | Declared capabilities to check against the actual task |
| `credentialsEnv` | Names of required backend-side credential variables; no values |
| `limits` | Positive integers such as `concurrency`, `runTimeoutSeconds`, `maxAttempts`, `maxExternalRequestsPerRun` |
| `output` | Optional `format` and project-specific `contract` name |
| `backendOptions` | Non-secret adapter options, such as `branch` or `loginProfile` |

For Trigger.dev, accepted environments are `dev`, `prod`, `staging` and `preview`; provide a branch when the selected environment/task requires it. The helper does not assume an environment. Other backends can define their own environment names.

The helper does not inspect live tasks, provision engines, update models, grant tools or enforce remote execution limits. Verify the resolved expectations against the backend before dispatch.

## Add another agent

Add a profile with its deployed task ID, engine metadata, capabilities and backend-side credential names. Engine/provider names are open strings, not a Pi-only enum. Use another profile for a different model or task contract instead of silently rewriting global defaults. The disabled `another-agent` example illustrates this shape; enable it only after configuring and verifying a real deployment.

Use inheritance when profiles share execution settings, but override arrays deliberately: for example, an agent with a different provider must replace inherited `credentialsEnv` rather than keeping an unrelated provider's credential name.

## Add another backend

Set the profile's `backend`, project/environment and non-secret options. Discover a corresponding connector or document the adapter's submit/status/result/idempotency contract using current official documentation. The skill's lifecycle and result checks remain applicable. Trigger.dev-specific CLI commands, environment names and wait constraints apply only to Trigger.dev.

## Setup versus use

Running an existing profile does not imply permission to deploy a replacement. If setup or extension is requested, inspect the existing project first; use its package manager, SDK contract and secret-management conventions. Do not embed runtime credentials in the skill or copy another project's deployment settings into it.
