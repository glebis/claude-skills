# Cloudflare Workers and Workflows

Use backend `cloudflare.workflows` explicitly. Trigger.dev remains the default. Enable the Cloudflare example profile only after configuring a deployed Workflow. `projectRef` is the Cloudflare account ID; `tasks.run` is the Workflow name. Environment is a profile label: it does not select a Cloudflare deployment automatically. Give each deployment its own explicit Worker/Workflow name and profile.

## Runtime contract

The template in `assets/cloudflare-worker` runs **Pi agent core**, not the full Pi coding-agent SDK. It accepts `{"prompt":"..."}` and returns engine, provider, model and text. It has no search, shell, filesystem or enrichment tools. Supply source excerpts for source review, or explicitly implement and verify tools before advertising fresh research.

Workflows persist step outcomes. The Pi conversation is fresh per run and held in memory inside one step; durable multi-turn agent history is not implemented. The model call has no automatic step retries, a bounded response and a timeout. Profile concurrency describes desired limits; this template does not implement a global concurrency limiter. Enforce quotas before dispatch or add a tested shared admission mechanism.

## Deploy

Copy the template into a project-specific runtime directory, install its dependencies, and run `npm run check` and `npm run build:check`. Check current official Cloudflare and Pi documentation before changing dependencies. Configure names and model in `wrangler.jsonc`, authenticate with an account-scoped deployment token, then deploy with Wrangler. Do not overwrite unrelated existing resources.

Store `OPENROUTER_API_KEY` using Cloudflare Worker secrets with explicit authorization for that credential destination. Do not copy stale local values over dashboard-managed keys. The template disables public workers.dev and preview URLs; invoke it through the authenticated Workflows API. It needs no custom domain or DNS permissions.

Keep deployment credentials outside this skill. If SOPS is selected, encrypt JSON mapping credential names to values; decrypt only in memory. Configure an age/KMS identity through the normal SOPS configuration; do not put that identity into the skill or project archive. Avoid plaintext `.env`, command arguments, logs and shell tracing for secrets.

## Submit and reconcile

From this skill directory, with private runtime configuration and an optional encrypted credentials file:

```sh
python3 scripts/cloudflare_workflows.py --config agents.profiles.json \
  --profile pi-cloudflare --secrets-file runtime-secrets.sops.json \
  submit --payload-file payload.json --request-id stable-operation-id --wait
```

The payload is an object with a nonempty prompt of at most 12,000 characters. A stable instance ID includes canonical inputs, operation identity, environment and deployment. An existing run is reconciled before creation; only a confirmed 404 allows creation. Do not resubmit on an unknown network outcome. After a timeout, repeat the same request or inspect the returned instance:

```sh
python3 scripts/cloudflare_workflows.py --config agents.profiles.json \
  --profile pi-cloudflare --secrets-file runtime-secrets.sops.json \
  status --instance-id INSTANCE_ID
```

Exit 0 means the request was handled, not necessarily that a non-waiting job completed. Inspect `status`, `isSuccess` and `output`. Exit 1 reports an error; exit 2 indicates a timeout or paused run. Receipts omit inputs and credentials, but returned agent text may contain supplied data: keep private results private. Validate terminal output and expected engine/model before claiming live execution.

Official references: [Workflows API](https://developers.cloudflare.com/workflows/build/workers-api/), [REST create](https://developers.cloudflare.com/api/resources/workflows/subresources/instances/methods/create/), [authorization](https://developers.cloudflare.com/workers/authorization/), [Worker secrets](https://developers.cloudflare.com/workers/configuration/secrets/).
