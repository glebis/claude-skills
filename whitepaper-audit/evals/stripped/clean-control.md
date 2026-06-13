# GreenCache: Measuring a Memory Cache for Weather Data

*Version 1.1 · 2026-03-20 · Kim Researcher · kim@example.org*

## Summary

GreenCache is a small in-memory cache for weather-station readings. On a replay of 30
days of real station traffic, it answered 72% of queries from memory (95% CI 68–76%),
cutting database reads by roughly two thirds. The cache helps most for stations queried
many times per hour; it adds little for rarely-queried stations. This paper describes the
design, the measurement method, and the limits of what we can conclude.

## The problem

Weather dashboards ask for the same recent readings again and again. Each repeated
question normally goes to the database, which is slow and costly. A cache — a small store
of recently used answers kept in fast memory — can answer repeats directly.

## Design

GreenCache keeps the most recently requested readings in memory (an LRU policy — *Least
Recently Used*, meaning the reading unused for the longest time is evicted first when
space runs out). Cache size is configurable; we tested 512 MB.

## Method

We replayed 30 days of recorded query traffic (4.1 million queries) against GreenCache
and counted hits and misses. The replay preserves the original timing and ordering. We
report the hit rate with a bootstrap confidence interval (resampling days, 2,000 times).

## Results

| Metric | Value | 95% CI |
|---|---|---|
| Hit rate | 0.72 | 0.68–0.76 |
| DB read reduction | 67% | 62–71% |

## Limitations

One month of traffic from one deployment may not represent other seasons or sites. The
replay ignores cache warm-up on day one (under 2% of queries). We did not measure tail
latency, only hit rate. Results are specific to the 512 MB configuration.

## Conclusion

For dashboards with repeated queries, a small LRU cache is a cheap, measurable win. To
adopt: start with the default configuration, replay a week of your own traffic, and check
your hit rate before rollout. Code and replay scripts: github.com/example/greencache.

## Glossary

| Term | Meaning |
|---|---|
| **Cache** | A small store of recently used answers kept in fast memory. |
| **Hit rate** | The fraction of queries answered from the cache. |
| **LRU** | Least Recently Used — the eviction policy described above. |
