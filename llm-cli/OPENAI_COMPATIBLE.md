# OpenAI-compatible gateways

The skill can use any gateway that speaks the OpenAI chat API (OrcaRouter,
a self-hosted proxy, LiteLLM, and similar). Nothing vendor-specific ships in
the repo. You wire a gateway into the `llm` CLI, then tell the skill which
model names to offer.

The example below uses OrcaRouter. Its docs list `https://api.orcarouter.ai/v1`
as the OpenAI-style base URL, with keys that start with `sk-orca-` and
provider-prefixed model names such as `openai/gpt-4o`. Check the gateway's
own docs before you use these values.

## 1. Point the skill at the gateway

```bash
export OPENAI_COMPATIBLE_BASE_URL='https://api.orcarouter.ai/v1'
```

The variable only turns the provider on. The `llm` CLI makes the requests.

## 2. Register the model with `llm`

`llm` reads extra OpenAI-compatible models from `extra-openai-models.yaml` in
its user directory. Find that directory with:

```bash
python3 -c "import llm; print(llm.user_dir())"
```

Add an entry to `extra-openai-models.yaml` there:

```yaml
- model_id: orcarouter-gpt-4o        # the name you pass to `llm -m`
  model_name: openai/gpt-4o          # the name the gateway expects
  api_base: https://api.orcarouter.ai/v1
  api_key_name: orcarouter           # key lookup name for `llm keys`
```

## 3. Store the API key with `llm`

Keep the key out of the config file and out of the shell history:

```bash
llm keys set orcarouter
```

## 4. Tell the skill which model IDs to offer

Add the `model_id` values to `~/.claude/llm-skill-config.json`:

```json
{
  "openai_compatible_models": ["orcarouter-gpt-4o"]
}
```

## 5. Check it works

```bash
llm -m orcarouter-gpt-4o "Reply with one word: ready"
```

If the menu shows no models, step 4 is missing or the list is empty.
