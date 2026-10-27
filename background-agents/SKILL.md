---
name: background-agents
description: Configure and run background agents with reusable profiles for agent engines, model providers and execution backends. Use when delegating background work, reusing agents across sessions, or adding an engine or backend. Trigger.dev and Cloudflare Workflows are available backends; the approach is extensible. Includes optional source-backed evidence review.
---

# Background Agents

Run the requested work through a selected profile, verify the remote outcome, and return usable results with run references.

Keep four choices separate: **execution backend** (Trigger.dev by default), **agent engine** (for example Pi), **model provider**, and **model**. Changing one does not automatically change the others. Profiles select deployed tasks; they do not install a new engine or grant it tools.

## Select configuration

Use the configuration explicitly supplied by the user, otherwise `BACKGROUND_AGENT_PROFILES`, otherwise `agents.profiles.json` in the working project. Do not search unrelated projects or reuse remembered account/project identifiers.

Read [references/profiles.md](references/profiles.md) when creating, extending or resolving profiles. Copy [assets/profiles.example.json](assets/profiles.example.json) as a starting point; it contains environment references, not working deployment identifiers.

The standard-library helper lists and resolves profiles without executing jobs:

```sh
python3 scripts/profiles.py --config agents.profiles.json list
python3 scripts/profiles.py --config agents.profiles.json validate
python3 scripts/profiles.py --config agents.profiles.json resolve pi-openrouter
```

Run helper commands from this skill folder, or use the helper's resolved path and the project's configuration path. An explicit profile takes precedence over `defaultProfile`. Unset references, unknown profiles, disabled profiles and inheritance cycles stop resolution. An omitted backend resolves to Trigger.dev. An explicitly selected different backend must never silently fall back to Trigger.dev.

## Confirm the deployed contract

Inspect the selected backend's task metadata or implementation before execution:

- Match project, environment, task, expected input/output and available tools.
- Verify engine/provider/model when the profile specifies them. A profile's model label is an expectation, not a model override supported by every task.
- Check actual concurrency, duration and retry settings. Profile limits describe desired bounds; they do not reconfigure a deployed task by themselves.
- For Trigger.dev, **development runs use a local worker**; cloud execution requires a deployed production, staging or preview worker. Keep the selected environment explicit.
- Distinguish a fresh per-run session from durable conversation state. Do not promise continuity unless the task implements it.

If the task lacks a required capability, use an already deployed compatible profile or implement the missing capability within the user's scope. Do not ask a prompt-only agent to claim it searched, ran tools or updated records.

## Execute and verify

For Cloudflare Workers/Workflows, read [references/cloudflare.md](references/cloudflare.md). The optional adapter and Worker template support a prompt-only Pi core engine; Trigger.dev remains the default.

Prefer an available backend MCP tool when it supports the selected profile and required operation. For Trigger.dev, the CLI is a fallback:

```sh
npx trigger.dev@latest tasks trigger "$TASK_ID" \
  --project-ref "$PROJECT_REF" --env "$ENVIRONMENT" \
  --payload-file payload.json --idempotency-key "$REQUEST_ID" \
  --wait --timeout "$TIMEOUT_SECONDS"
```

Derive these values from the resolved profile and actual task contract. Include a branch/login profile when required. Check the installed CLI's help for current flags.

- Give each job a bounded payload and a stable request identity derived from its operation and canonical inputs. Reuse it when an outcome is uncertain; changed inputs need a new identity.
- Respect shared provider quotas as well as task concurrency. Moving work to another backend must not bypass a shared research allowance.
- Preserve receipts with profile, environment, task, request identity, run ID/status and result disposition. Keep private payloads and credentials out of general receipts.
- A submission or deployment is not a completed job. Inspect terminal status and output. After a timeout, reconcile the existing run before submitting another.
- For failures, fix a demonstrated cause before a bounded retry. Stop and report when repeated failures require a credential, capability or external change.
- Do not wrap Trigger.dev `wait.*`, `triggerAndWait` or `batchTriggerAndWait` in `Promise.all`.

## Handle results

Validate outputs against the task's actual schema and the user's acceptance criteria. For source review or enrichment, read [references/evidence-review.md](references/evidence-review.md) before dispatch and before import. Unknown, proposed, accepted and verified outcomes remain distinct.

Import only the intended validated results. Correct an error in an agent-generated proposal without rewriting unrelated records or changing review decisions. Report completed/failed/pending coverage, useful results, unresolved gaps and remote run links. Say whether the work used saved evidence or fresh external research.

## Credentials and portability

The shared skill and example profiles contain no credentials, account/project IDs, run references, private datasets or absolute machine paths. Runtime project configuration belongs outside the shared skill.

Credential **environment-variable names** may appear in profiles. Values belong in the selected backend's secret store. Never resolve credential references into a payload, command argument, profile output or receipt. Use existing authenticated connections and preserve dashboard-managed variables; do not overwrite them from an old local environment file.

Creating this skill does not authorize unrelated deployments, credential changes or data writes. Work within the current user's request; consult current official documentation before adding SDKs or changing deployment behavior. Trigger.dev SDK imports use `@trigger.dev/sdk`; exported tasks, built-in `fetch`, explicit task directories and finite durations are the supported starting points.

Official references: [Trigger.dev tasks](https://trigger.dev/docs/tasks/overview), [environments](https://trigger.dev/docs/deployment/overview), [environment variables](https://trigger.dev/docs/deploy-environment-variables).
