#!/usr/bin/env python3
"""Resolve Ollama model names to their on-disk GGUF blob paths.

Ollama stores model weights as extension-less GGUF blobs under
~/.ollama/models/blobs/. The manifests under .../manifests/ map a
model name+tag to the digests of its layers. The layer whose mediaType
ends in ".model" is the GGUF weights file; ".projector" is the vision
mmproj. llama.cpp can load these blob files directly with `-m`.

Usage:
  ollama_blob.py list                 # tab-separated: name  sizeGB  kind  path
  ollama_blob.py path  <name>         # absolute path to weights GGUF
  ollama_blob.py mmproj <name>        # absolute path to vision projector GGUF (if any)
"""
import json, glob, os, sys

BASE = os.path.expanduser("~/.ollama/models")
REG = os.path.join(BASE, "manifests", "registry.ollama.ai")


def _friendly(manifest_path: str) -> str:
    rel = os.path.relpath(manifest_path, REG)          # e.g. library/qwen3/4b
    parts = rel.split(os.sep)
    tag = parts[-1]
    name = parts[-2] if parts[:-1] and parts[-2] != "library" else parts[-2]
    if parts[0] == "library":
        return f"{parts[-2]}:{tag}"                      # qwen3:4b
    return f"{'/'.join(parts[:-1])}:{tag}"               # jeffh/foo:f16


def _layers(manifest_path):
    d = json.load(open(manifest_path))
    return d.get("layers", [])


def _blob(digest: str) -> str:
    return os.path.join(BASE, "blobs", digest.replace(":", "-"))


def _all():
    out = {}
    for m in glob.glob(os.path.join(REG, "**"), recursive=True):
        if os.path.isfile(m):
            out[_friendly(m)] = m
    return out


def _weights_layer(layers):
    for l in layers:
        if l["mediaType"].endswith(".model"):
            return l
    return None


def _proj_layer(layers):
    for l in layers:
        if l["mediaType"].endswith(".projector"):
            return l
    return None


def _kind(name, layers):
    if _proj_layer(layers):
        return "vision"
    n = name.lower()
    if "embed" in n or "e5" in n or "bge" in n:
        return "embed"
    return "text"


def _resolve(query):
    """Match a query to a manifest. Exact friendly name wins, else substring
    on the model part, else substring anywhere."""
    models = _all()
    if query in models:
        return query, models[query]
    base = query.split(":")[0].lower()
    cands = [n for n in models if n.split(":")[0].lower() == base]
    if not cands:
        cands = [n for n in models if base in n.lower()]
    if len(cands) == 1:
        return cands[0], models[cands[0]]
    if cands:
        # prefer exact-name-any-tag, else shortest name
        cands.sort(key=len)
        return cands[0], models[cands[0]]
    return None, None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]

    if cmd == "list":
        rows = []
        for name, man in sorted(_all().items()):
            layers = _layers(man)
            w = _weights_layer(layers)
            size = (w["size"] / 1e9) if w else 0
            rows.append((name, f"{size:.2f}", _kind(name, layers), _blob(w["digest"]) if w else "-"))
        for r in rows:
            print("\t".join(r))
        return

    if cmd in ("path", "mmproj"):
        if len(sys.argv) < 3:
            sys.exit("error: model name required")
        name, man = _resolve(sys.argv[2])
        if not man:
            avail = ", ".join(sorted(_all()))
            sys.exit(f"error: no model matching '{sys.argv[2]}'. Available: {avail}")
        layers = _layers(man)
        layer = _weights_layer(layers) if cmd == "path" else _proj_layer(layers)
        if not layer:
            sys.exit("")  # empty: caller decides (e.g. no projector -> use -hf)
        print(_blob(layer["digest"]))
        return

    sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
