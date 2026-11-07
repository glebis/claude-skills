# Scope examples

## PDF replacement

User: compare local ways to replace personal identifiers in text and scanned bank statements while preserving appearance and editable text.

Clarify only missing identifier classes/replacement policy. Compare a text-only baseline with true redaction. Require separate detection vs removal metrics; test hidden OCR, embedded images, metadata, comments and forms where relevant. Check transformed output through extraction and rendering. If oracle boxes are used, say removal is measured and detection is not run. Package core transformation and an evaluator separately. Do not claim universal sanitization from a few synthetic files.

## Apartment video to 3D

User: investigate local open tools for video-to-Gaussian-Splatting, deliver code and a test suitable for integration; no video is supplied and cloud has no GPU.

Determine whether the intended output is visual navigation, a mesh, or metric geometry; ask about available capture/hardware only if not already known. Verify licenses, actual runtime support and required conversion/export tools. Compare feasible approaches and simple baselines from primary sources; do not assume CUDA runs on Apple Silicon. Implement adapters/config and run feasible preparation/format tests using appropriately licensed or synthetic samples. Package target commands, capture guidance, dataset provenance and not-run training/evaluation stages. Never claim reconstruction of the user's actual apartment without their video. Do not claim a toy output validates the real training pipeline.

## Knowledge linking

User: compare embeddings and a small local model for linking notes.

Freeze a labeled corpus, hold out note groups, compare retrieval and relation classification separately. Keep reference labels from the evaluated model. Deliver callable linking code, reproducible evaluation, false-positive examples and source provenance. Do not claim synthetic-pair success establishes real-vault accuracy.

## Interaction override

User: brief, at most one question at a time, act autonomously; compare two implementations.

Use concise messages, cap questions at one per round, execute the authorized experiment within budget, and preserve full tests/evidence. Do not ask the user to select routine language or interface choices. Do not reduce verification merely to shorten the response.
