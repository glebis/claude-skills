# qmd-search eval baseline

Regression set: `evals/fixture.example.json` (6 queries across exact / semantic / topical /
cross-domain / alias types). Run: `scripts/run-evals.sh`. Metrics are per backend, averaged.

## Baseline (vault `brain`, embeddinggemma-300M, 2026-05-29)

| Backend | P@k | R@1 | R@3 | R@5 | MRR | F1 | Avg latency |
|---|---|---|---|---|---|---|---|
| **bm25** | 0.50 | 0.31 | 0.75 | 0.75 | 0.64 | 0.50 | ~230ms |
| hybrid | 0.33 | 0.14 | 0.69 | **0.875** | 0.59 | 0.33 | ~2.1s |
| vector | 0.17 | 0.06 | 0.19 | 0.53 | 0.33 | 0.17 | ~2.3s |
| full | 0.33 | 0.14 | 0.57 | 0.75 | 0.58 | 0.33 | ~1.8s |

## What this tells us
- **BM25 is the best default** on this vault: top precision/MRR and ~10× faster than hybrid.
  (The wrapper defaults to hybrid for *recall* on fuzzy questions; for keyword/name lookups,
  `-m search` is both better and faster.)
- **Hybrid wins on R@5** (0.875) — use it when recall matters more than latency.
- **Vector-only is weakest** — prefer hybrid or BM25 over raw `vsearch` unless you specifically
  want pure semantic neighbors.
- **Cross-lingual (RU→EN) is the genuine weak spot**: the `cross-lingual-anxiety-ru` case scores
  0 on bm25/vector and only ~0.25–0.50 R@5 on hybrid/full, and the specific top file is unstable
  across re-embeds. Cross-lingual recall is *topical, not exact-file-stable*. This is exactly why
  the skill mandates a native-script literal `-m grep` pass for names/entities before concluding
  absence (see SKILL.md → "Bilingual / proper-name rule").

## How to use
Re-run after any change to the wrapper, the index, or the embedding model. A drop in R@5/MRR vs.
this table is a regression. Latencies are machine-dependent (Apple Silicon, Metal); compare
*relative* backend ordering, not absolute ms.
