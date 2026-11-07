# pii-pdf

Experimental local PDF PII detection and redaction for command-line tools and agents. Detect candidates in one PDF or a directory, emit versioned NDJSON, and optionally write redacted copies. Inputs are protected from overwriting. Processing does not download models or call a remote service.

**A completed operation is not a validated anonymization.** Every result remains `validated: false`. Inspect outputs before using or sharing them. The detector combines spaCy PERSON recognition, format rules, and Tesseract OCR; it can miss personal information and redact unrelated content.

## Install

Python 3.10+ and Tesseract are required. Install Tesseract separately (`brew install tesseract` on macOS, or `sudo apt-get install tesseract-ocr` on Ubuntu). Install any additional OCR language packs before processing documents.

Use an isolated Python environment, then install this GitHub repository and the English spaCy model:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'git+https://github.com/glebis/pii-pdf.git'
python -m spacy download en_core_web_sm
pii-pdf doctor
```

This is a GitHub installation, not a published PyPI or npm package. The Python distribution is named `pii-pdf-lab`; the command is `pii-pdf`. The package requires PyMuPDF >=1.26.7,<1.27 and spaCy >=3.8,<3.9. Model installation requires network access; document processing is local.

For a source checkout, use `python -m pip install -e .`, or run `python ./pii-pdf` with dependencies installed in that Python environment. `python -m pii_pdf` is also available after installation.

## Commands

```sh
# Detect candidates without writing a PDF
pii-pdf detect statement.pdf

# Write a separate copy and a run manifest
pii-pdf redact statement.pdf --output ./redacted

# Process a directory while preserving relative paths
pii-pdf redact ./statements --output ./redacted --recursive

# Inspect the plan without loading the model, OCR, or creating files
pii-pdf redact ./statements -o ./redacted --recursive --dry-run

# Machine-readable command contract and dependency checks
pii-pdf schema
pii-pdf doctor
pii-pdf redact --help --json

# Limit entities or use blank redactions
pii-pdf redact statement.pdf -o ./redacted --entities EMAIL,PHONE --replacement blank

# JSON configuration; explicit flags take precedence
pii-pdf redact statement.pdf -o ./redacted --config example-config.json --dpi 200
```

`--output` is a directory. A file `a.pdf` becomes `OUTPUT/a.pdf`; a directory entry `sub/a.pdf` becomes `OUTPUT/sub/a.pdf`. Discovery accepts case-insensitive `.pdf` extensions, skips symlink files, and excludes a nested output directory. Existing outputs cause a conflict unless `--overwrite` is explicit; source files remain protected. Each PDF is written atomically, but a batch is not atomic: completed files can remain after another file fails. `--fail-fast` stops after the first failure.

`detect` without `--output` writes no files. With `--output`, it writes a manifest. `--dry-run` creates no output directory.

## Agent output and privacy

Default stdout is NDJSON: one JSON object per line. `--json` explicitly selects the same mode before or after a command. Plain `--help` prints text; `--help --json` emits JSON. Library messages go to stderr.

Every event contains `schema_version` (`1.0`), `event`, `ts` (UTC), `run_id`, and monotonic `seq`. Processing emits `run_started`, `file_started`, `file_result`, errors where needed, and `summary`. Preflight failures can emit only `error`. Use the exit code and final `summary` to determine completion; `file_started` is not success. `schema` describes options, event envelopes, defaults, and stable error semantics.

Original detected text and raw PII values are omitted from events and manifests by default. **Paths and filenames, coordinates, and synthetic replacements remain and can themselves be sensitive.** `--include-sensitive` opts into original values. `--save-evidence` requires both `--include-sensitive` and `--output`; its OCR TSV files contain source text. Keep these diagnostic materials private.

Run manifests are stored as `OUTPUT/run-UUID.json` and updated after each processed file. Synthetic replacements are deterministic demonstration values, can collide between people, and do not provide a reversible identity mapping.

## Processing policies

| Option | Choices | Default |
|---|---|---|
| `--ocr-mode` | `auto`, `always`, `never` | `auto` |
| `--replacement` | `synthetic`, `blank` | `synthetic` |
| `--metadata` | `strip`, `keep` | `strip` |
| `--attachments` | `error`, `drop`, `keep` | `error` |

`auto` runs OCR on pages containing images; `always` runs it on all pages. `never` skips image-based detection and flags affected pages for review. OCR settings include `--language`, `--dpi`, `--psm`, and `--ocr-timeout`; the model is selected with `--model`.

UTF-8 TXT attachments are processed with the detector. Unsupported binary attachments use the attachment policy: `error` prevents an output PDF, `drop` removes them from the copy, and `keep` retains them with a review flag. Keeping existing metadata also requires review. Restricting `--entities` narrows the requested detection scope.

## Known quality limits

Multiline PERSON predictions can cross table rows and damage financial information. A previous narrow test damaged 3 of 16 documents; that set reused identity patterns and is **not a general accuracy estimate**. Those historical results do not validate this release or unseen documents. CLI contract tests do not measure detector recall or redaction quality.

Vector outlines of letters are not removed. Digital signatures and XFA are not validated. Rotated or unusual pages require separate quality checks. This tool performs no exhaustive forensic audit and issues no automatic quality certificate. Even exit code 0 leaves `validated: false`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Operation completed; anonymization remains unvalidated |
| 1 | Internal error |
| 2 | Invalid arguments, configuration, or input |
| 3 | Missing dependency or model |
| 4 | Completed with explicit review conditions |
| 5 | One or more processing failures; partial outputs can remain |
| 6 | Output conflict or attempted source overwrite |
| 130 | Interrupted; earlier completed files can remain |

## Agent skill

The skills installer requires Node.js 22.20+. The companion skill lives in [glebis/claude-skills](https://github.com/glebis/claude-skills/tree/main/pii-pdf). Install it for Claude Code with:

```sh
npx skills add glebis/claude-skills --skill pii-pdf -a claude-code -g
```

This installs the skill instructions and a versioned source snapshot. Then run `/pii-pdf setup` in Claude Code to install the Python CLI and its dependencies in an isolated environment. Run `/pii-pdf doctor` to check the installation and a synthetic redaction scenario. You can also install the standalone CLI directly as described above.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests create synthetic PDFs in a temporary directory and require the engine dependencies, `en_core_web_sm`, and Tesseract. They cover command contracts, errors, source protection, conflicts, batch continuation, entity filters, OCR, and attachment policies. They are not a detector quality benchmark.

## Licensing

The toolkit source is provided under the inherited MIT license in the skills repository root, copyright 2025–2026 Gleb Kalinin. Dependencies retain their own licenses. In particular, PyMuPDF has its own AGPL/commercial licensing terms; review the [official PyMuPDF licensing information](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) for your intended use.
