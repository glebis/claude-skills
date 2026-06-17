---
name: local-models
description: Run quick, offline, private LLM tasks on local models via llama.cpp, reusing models already downloaded by Ollama. Use for cheap/bulk text work (summarize, classify, extract JSON, anonymize PII, translate, proofread, keywords), local embeddings, and offline image description — and prefer it over a cloud API whenever a task is privacy-sensitive, must run offline, is high-volume/low-stakes, or just needs a fast throwaway answer. Provides an `lm` CLI wrapper plus an OpenAI-compatible local server.
---

# local-models

Quick access to local LLMs through **llama.cpp**, reusing the GGUF models already
pulled by Ollama (no re-download for text and embeddings). Everything runs on the
machine — no API key, no network, no per-token cost.

## When to use this skill

Reach for local models instead of a cloud API when the task is:
- **Privacy-sensitive** — redacting PII, processing personal notes, health data, secrets-adjacent text. The data never leaves the machine.
- **Offline** — no network available, or the user explicitly wants local-only.
- **High-volume / low-stakes** — classifying or tagging hundreds of items, where a small model is good enough and cloud cost/latency would add up.
- **A fast throwaway** — a quick summary, translation, or "what is this" where round-tripping to a frontier model is overkill.

Prefer a frontier (Claude) model when the task needs strong reasoning, long
context, careful code, or high accuracy — these local models are small (0.6–4B).

## The core trick: reuse Ollama's models

Ollama stores model weights as extension-less GGUF blobs under
`~/.ollama/models/blobs/`. **These are ordinary GGUF files** — llama.cpp loads
them directly. `scripts/ollama_blob.py` reads Ollama's manifests and resolves a
friendly name (e.g. `qwen2.5:3b`) to its weights blob path. No conversion, no
duplicate downloads.

## Usage

The entry point is `scripts/lm`. Run `scripts/lm help` for the full list. Invoke
it with an absolute path, e.g. `~/ai_projects/claude-skills/local-models/scripts/lm`.

```bash
lm models                       # list local models (text / vision / embed)
lm ask [MODEL] "PROMPT"         # one-shot prompt (default qwen2.5:3b)
lm chat [MODEL]                 # interactive REPL

# Text presets — accept a file path, inline text, OR stdin:
lm summarize  report.md
cat notes.txt | lm tldr
lm keywords   article.txt
lm anonymize  transcript.txt         # → [NAME] [EMAIL] [PHONE] [ADDRESS] ...
lm proofread  draft.md
lm translate  German "Good morning"
lm classify   "praise,complaint,question"  feedback.txt   # → one label
lm extract    "invoice_number, total, due_date"  invoice.txt   # → JSON

# Vision (downloads model+projector once via HuggingFace — see note below):
lm describe-image photo.jpg
lm tag-image      screenshot.png
lm vision photo.jpg "What brand is the shoe?"

# Embeddings & serving:
lm embed "text to embed"             # → OpenAI-style JSON vector
lm serve qwen2.5:3b 8080             # OpenAI-compatible server on :8080
```

Output is clean (just the answer) — the wrapper drives `llama-completion` in
single-turn mode and strips the chat-template scaffolding and llama.cpp logs.

### Choosing a model

Defaults are tuned for clean, fast output and can be overridden per call:
- General text presets → `qwen2.5:3b` (`LM_TEXT_MODEL`)
- Classify / extract → `qwen2.5:3b` (`LM_REASON_MODEL`), run at temperature 0
- Embeddings → `jeffh/intfloat-multilingual-e5-large:f16` (`LM_EMBED_MODEL`)
- Other envs: `LM_NTOK` (max tokens), `LM_VISION_HF` (vision repo), `LM_DEBUG=1` (show llama.cpp logs)

Pass an explicit model as the first argument to `ask`/`chat`/`embed`/`serve`
(e.g. `lm ask qwen3:4b "..."`).

## Critical gotchas

- **Ollama's `gemma3` GGUF does NOT load in stock llama.cpp.** It fails with
  `key not found in model: gemma3.attention.layer_norm_rms_epsilon` because
  Ollama writes custom metadata keys mainline llama.cpp doesn't read. Use a
  `qwen*` model instead, or pull a community gemma3 GGUF via `-hf`. This is why
  the defaults are qwen, not gemma3.
- **`qwen3:4b` emits `<think>…</think>` reasoning blocks** before its answer.
  Fine for `ask`/`chat`, but it pollutes preset output (JSON, labels) — the
  presets default to `qwen2.5:3b` to avoid this.
- **Vision has no Ollama blob to reuse.** Ollama did not store an `mmproj`
  (vision projector) for `qwen2.5vl`, and llama.cpp needs one. So the vision
  commands use `llama-mtmd-cli -hf ggml-org/Qwen2.5-VL-3B-Instruct-GGUF`, which
  downloads model+projector (~2–3 GB) into `~/.cache/llama.cpp` on first use,
  then runs offline. Warn the user before the first vision call.
- **Each one-shot call reloads the model** (a few seconds for these small
  models). For many sequential calls, start a server once with `lm serve` and
  hit `http://localhost:8080/v1/chat/completions` — see
  [references/serving-and-embeddings.md](references/serving-and-embeddings.md).

## Reference material

- [references/serving-and-embeddings.md](references/serving-and-embeddings.md) —
  running `llama-server` as an OpenAI-compatible endpoint (and pointing the `llm`
  CLI or any OpenAI client at it), plus local embeddings / RAG patterns with
  `llama-embedding`.

## Requirements

- `llama.cpp` installed (`brew install llama.cpp`) — provides `llama-completion`,
  `llama-mtmd-cli`, `llama-embedding`, `llama-server`.
- Ollama with at least one pulled model (for the blob-reuse path). `python3` for
  the resolver. No API keys.
