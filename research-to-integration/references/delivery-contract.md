# Integration package contract

Adapt structure to the project; do not require a language or unnecessary service. Supply:

- Core implementation callable from an external product; isolate tool-specific adapters.
- Explicit inputs, outputs, units, schema/version, error behavior and supported formats.
- Configuration with no machine-specific absolute paths or embedded secrets.
- Dependency versions and setup; pinned source commits/model revisions and hashes where applicable. Explain required OS, accelerator, disk and external binaries. Avoid embedding large weights; include lawful acquisition instructions and checksums.
- A minimal integration example using the actual public entry point.
- Meaningful tests including failures/edge cases and one end-to-end run when feasible.
- Evaluation runner, frozen config/fixtures or acquisition instructions, raw logs/results and an evidence report.
- README for the DELIVERED PRODUCT PACKAGE with install/run/test/integrate commands and limitations. This is distinct from the skill itself, which does not need a README.
- A continuation note naming not-run commands and prerequisites for another environment.

Separate core code from notebooks, benchmarking and sample data. Use structured results and actionable errors. Make downloads and expensive execution explicit. Avoid web UI, deployment, authentication, plugin framework or generalized infrastructure unless integration actually needs them.

Recommended report fields: task; decision; acceptance criteria; options and dated sources; actual vs target environment; data provenance/split; exact executed commands; metrics and raw-output paths; stage-by-stage status; failure analysis; integration example; licenses; unresolved limits and next command.

Use evidence labels:
- measured: executed with recorded outputs in the stated environment; distinguish correctness checks from quality estimates.
- source-reported: supported by a dated upstream source, not locally confirmed.
- inferred: engineering interpretation with assumptions.
- not run: no execution evidence, with reason and reproduction instructions.

Do not ship reference labels as runtime input. Do not redistribute private documents or claim model licenses from the code repository license alone. Preserve originals when transforming data. Treat a package with unrun GPU/backend stages as integration-oriented code awaiting target validation, not a verified solution.
