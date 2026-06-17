# Serving & embeddings

## OpenAI-compatible server (`llama-server`)

For repeated calls, load the model once and keep it resident. `lm serve` wraps
`llama-server`:

```bash
lm serve qwen2.5:3b 8080        # blocks; Ctrl-C to stop
```

This exposes an OpenAI-compatible API on `http://localhost:8080`. Hit it with
curl, any OpenAI SDK, or the `llm` CLI:

```bash
curl -s http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"One-sentence summary of TCP."}],"temperature":0.3}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["choices"][0]["message"]["content"])'
```

Useful `llama-server` flags (append after the port, editing `scripts/lm` or
running `llama-server` directly):
- `-c 8192` — context size (default is model-dependent; raise for long inputs).
- `-ngl 99` — offload all layers to GPU/Metal (usually the default on macOS).
- `--host 0.0.0.0` — expose on the network (default is localhost only).
- `--parallel N` / `--cont-batching` — serve concurrent requests.

### Pointing the `llm` CLI at the server

The `llm` CLI already talks to Ollama directly via the `llm-ollama` plugin
(`llm -m qwen3:4b "..."`). To instead route through a `llama-server` instance,
register it as an OpenAI-compatible model in `~/.config/io.datasette.llm/extra-openai-models.yaml`:

```yaml
- model_id: local-qwen
  model_name: qwen2.5:3b
  api_base: http://localhost:8080/v1
  api_key_name: none
```

Then `llm -m local-qwen "..."`.

## Embeddings (`llama-embedding`)

`lm embed "text"` returns an OpenAI-style JSON vector using the multilingual e5
model by default. Override with a model argument or `LM_EMBED_MODEL`:

```bash
lm embed qwen3-embedding:0.6b "text to embed"
```

Available embedding models (from `lm models`, kind=embed):
- `jeffh/intfloat-multilingual-e5-large:f16` — 1024-dim, strong multilingual (good for EN/RU/DE mixed corpora).
- `qwen3-embedding:0.6b` — smaller/faster, English-leaning.

### Minimal local RAG pattern

llama.cpp has no built-in vector store, so pair embeddings with any similarity
search. Smallest viable loop in Python:

```python
import json, subprocess, numpy as np

LM = "/abs/path/to/local-models/scripts/lm"

def embed(text):
    out = subprocess.run([LM, "embed", text], capture_output=True, text=True).stdout
    return np.array(json.loads(out)["data"][0]["embedding"])

docs = ["...chunk 1...", "...chunk 2...", "...chunk 3..."]
mat = np.vstack([embed(d) for d in docs])          # embed corpus once
q = embed("user question")
scores = mat @ q / (np.linalg.norm(mat, axis=1) * np.linalg.norm(q))
top = docs[int(scores.argmax())]                    # nearest chunk
```

For anything beyond a few hundred chunks, persist vectors in `sqlite-vec`,
`chroma`, or the `llm` CLI's own `llm embed-multi` / `llm similar` collections
(which can use the same Ollama embedding models via `llm-ollama`).

The raw binary, if finer control is needed:

```bash
llama-embedding -m "$(scripts/ollama_blob.py path qwen3-embedding:0.6b)" \
  --pooling mean --embd-output-format json -p "text"
```
