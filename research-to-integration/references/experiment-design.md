# Experiment design

Freeze the question and comparison before scoring. Choose observable acceptance criteria linked to the intended product. State proposed thresholds as provisional when the user has not set them. Never retrofit the criterion to select the preferred tool.

Use a minimal baseline and at most a few useful alternatives. Keep data, preprocessing and evaluator fixed when isolating a component; if a pipeline differs, report that difference. Record unsupported methods as unavailable, not low quality. Distinguish tool support, successful execution and actual output quality.

Record for each fixture: origin/license, hash, seed/generator version, expected answer or behavior, edge cases and group/split. Split related renders, source documents, scenes or identities together. Do not randomly distribute near duplicates across train/test. Synthetic samples support controlled checks; independent real examples support generalization. Small smoke tests are not production benchmarks.

Separate the system under test from the evaluator. Do not leak labels into inference prompts or generators. For independent agent checks, provide task and raw artifacts, not the intended answer. Oracle coordinates or known entity strings can isolate transformation behavior, but cannot validate detection recall.

Collect task-relevant metrics rather than one decorative aggregate. Include failures, missing outputs and review/abstention rates. Do not infer performance from upstream leaderboards without verifying task and hardware match. Record versions, exact commands, input hashes, resource limits, raw outputs and actual measured scope. One passing sample does not establish an error rate.

Test invariants before adding infrastructure: untouched content, ordering, sign/units, valid output format, provenance, idempotency if needed, clean errors and bounded runtime. For images/PDFs inspect renders and preserved objects; for 3D inspect viewer/export compatibility, geometry/scale if required, and held-out views. Use a genuine downstream consumer when possible.

If interrupted, save a checkpoint with completed runs, config, unresolved issues and exact next command. Mark unavailable stages not_run with reasons. Report quality separately from process exit status.
