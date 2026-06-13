# QuickSort-NG: Faster Sorting for Log Pipelines

*Version 0.9 · 2026-04-12 · Ada Developer*

## Summary

QuickSort-NG is a sorting library tuned for log-pipeline workloads. On our test set of
40 log files it sorted 2.3× faster than the standard library sort (median; range
1.8–2.9×). This paper explains the technique and the measurement.

## The problem

Log pipelines sort huge, nearly-sorted files. General-purpose sorts waste work on data
that is already mostly ordered.

## How it works

QuickSort-NG detects pre-sorted runs (stretches of already-ordered records) and merges
them directly, falling back to standard quicksort for disordered segments. Run detection
is a single linear pass.

## Results

| Workload | Speedup |
|---|---|
| Nearly sorted (90% ordered) | 2.9× |
| Half sorted | 2.2× |
| Random | 1.1× |

The gains concentrate exactly where the workload hypothesis predicts: pre-ordered data.

## Conclusion

For log pipelines specifically, run-detection sorting is worth adopting. Random-data
workloads should keep the standard sort.

<!-- PLANTED: limitations-present — this document makes empirical performance claims
     (2.3x median across 40 files) but has NO limitations section at all: nothing on
     test-set composition bias, hardware, memory trade-offs, or generality.
     expected: check_id=limitations-present, severity=P0 -->

## Glossary

| Term | Meaning |
|---|---|
| **Run** | A stretch of records that is already in sorted order. |
