# Evidence for a PDF review

The baseline test had 16 synthetic PDFs and 193 repeated target occurrences. All expected values intersected a matching candidate; nine extra areas altered tables in three PDFs across five pages. This is one repeated identity, not an independent accuracy estimate for real documents.

For a requested test or before/after report:

- Run inference using PDFs alone. Ground-truth identities and coordinates belong only in a separate post-hoc evaluator.
- Assess detection and erasure separately. An intersecting bbox does not prove every glyph/pixel was removed. A generous field rectangle may include padding and need not be entirely covered.
- Check rendered output, copyable/hidden text, extracted image resources, widgets, comments, document metadata and attachments in scope. A white overlay can hide intact underlying data. Tesseract's failure to recover a full original string does not establish absence of fragments.
- Compare every page outside approved PII regions for damage; verify financial dates, values and descriptions against the source where appropriate. For image-only financial sections, selectable-text equality is not applicable.
- Record unsupported binary attachments, retained metadata, disabled OCR and untested encodings as limits. Original-image hash changes alone do not prove sanitization.
- Preserve a frozen detector result when reporting a benchmark. If fixing an observed failure, label the next run separately and keep the original measurements.

For new test documents, use independent identities/layouts and keep their annotations out of inference inputs. Do not import the old evaluator's fixed identity-panel coordinates into the detector or apply them to arbitrary new files.
