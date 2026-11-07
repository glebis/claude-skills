---
name: pii-pdf
description: Detect and replace personal names, addresses, contacts, bank accounts and IBANs in PDF files or folders using the local pii-pdf JSON CLI. Use for PDF anonymization, coordinate-based PII review, and setup of this PDF engine; not for general PDF editing or ordinary text anonymization.
---

# PDF PII workflow

Use the bundled, versioned `pii-pdf` CLI. It combines native character boxes, local Tesseract OCR, spaCy PERSON and format rules. Preserve the user's selected scope and retain originals. The detector is experimental: a completed command is not a validated anonymous document.

`SKILL_DIR` below means the directory containing this file. Resolve it from the actual loaded skill path; do not assume the current working directory is the skill directory.

## Setup mode

When asked to install, configure or repair this engine:

```sh
python3 "$SKILL_DIR/scripts/setup.py" --plan
python3 "$SKILL_DIR/scripts/setup.py" --apply
```

Explain the actual installation plan before applying it. An explicit request to set up this engine authorizes its documented missing dependencies; do not ask again for the same installation. Downloads happen during setup, not document processing. The installer checks the bundled source hashes, uses an isolated Python environment, installs its Python dependencies and the pinned English model, and installs a missing Tesseract through an existing supported package manager. It does not bootstrap Homebrew, run remote shell installers, or invoke sudo automatically.

Default environment: `~/.local/share/pii-pdf/venv`. `--venv PATH` selects another environment. `--system skip` skips installing system packages; if Tesseract is still missing the result remains incomplete. Report a missing package manager or privilege requirement with the exact missing step; do not invent success or silently substitute cloud OCR. Use `setup.py --help` for supported switches.

For installation through npx and runtime setup, read [references/installation.md](references/installation.md). The standalone toolkit is maintained at https://github.com/glebis/pii-pdf; this skill includes a versioned source snapshot for reproducible setup.

## Doctor mode

When asked to diagnose, check, test or troubleshoot this engine (`/pii-pdf doctor`), or when a document run fails with exit `2`/`3`:

```sh
python3 "$SKILL_DIR/scripts/doctor.py"            # diagnose + synthetic smoke test
python3 "$SKILL_DIR/scripts/doctor.py" --no-smoke # diagnose only
python3 "$SKILL_DIR/scripts/doctor.py" --keep     # keep fixture + redacted copy for inspection
```

It never installs dependencies or changes existing documents. The smoke check creates temporary synthetic files. Three stages, NDJSON on stdout:

1. `setup_plan`: bundled-source hashes and pending install steps (`setup.py --plan`).
2. `cli_doctor`: dependencies and model in the runtime (`pii-pdf doctor`).
3. `smoke`: builds a 2-page synthetic invoice (page 1 native text, page 2 image-only scan) with a fake name, email, phone and IBAN, redacts it, then checks native text and Tesseract OCR of every page. Each fake value must be gone, and the non-PII heading and total must survive. Skipped when stages 1–2 are blocking.

The final `diagnosis` event lists `findings`, each with `stage`, `problem`, `fix` and `severity` (`blocking` = install/repair, `detector` = leak or over-redaction). Exit `0` healthy, `3` blocking (repair with setup mode; an explicit repair request authorizes `--apply`), `4` smoke test flagged the detector (don't trust redactions until resolved), `5` doctor failed. Report each finding with its fix. Exit `0` means the fixture passed, not that real documents will be anonymised. The fixture contains only invented data, so `--keep` output is safe to inspect.

## Locate and discover the CLI

```sh
python3 "$SKILL_DIR/scripts/run.py" schema
python3 "$SKILL_DIR/scripts/run.py" doctor
```

The launcher uses the default isolated environment, or `--runtime PATH` for another venv; if the default is absent it can use an installed `pii-pdf` on PATH. Require CLI 0.1.2+ (0.1.1 can trash its own published outputs on macOS) and PyMuPDF 1.26.7+ for new processing; older baseline environments need setup first. Read the live `schema` JSON for current parameters, defaults and event semantics. Do not guess flags or auto-install dependencies while handling a document request. If dependencies are missing, report them or use setup mode when installation is authorized.

## Detection and redaction

```sh
python3 "$SKILL_DIR/scripts/run.py" detect "/path/statement.pdf" --json
python3 "$SKILL_DIR/scripts/run.py" redact "/path/statements" \
  --output "/path/redacted" --recursive --json
```

- Accept a single PDF or a folder. Use `--recursive` when subfolders are in scope; retain their relative structure.
- `detect` identifies areas without writing PDFs. `redact` writes copies. If the user requested redaction, proceed with copies within that scope; a separate confirmation is not a prerequisite.
- Use a separate output directory. Do not add `--overwrite`, drop attachments, or retain unsupported contents without an applicable user choice. Default unsupported-attachment behavior is an explicit error.
- For a new batch, `--dry-run` can verify file selection and output paths without OCR, model loading or writes.
- Keep default `--ocr-mode auto` for image-bearing pages, including sparse hidden OCR. Disabling OCR does not make scan pixels safe. Choose `--dpi`, `--psm`, `--language`, entity types and JSON config from the document and the user's request.
- Default output omits source PII values. Enable `--include-sensitive` or `--save-evidence` only when original-value diagnostics are needed within the authorized local review; keep those artifacts separate from redacted deliverables. OCR evidence contains originals.
- Processing is local. Publishing, sending or uploading source PDFs, diagnostics or results is a separate action, not implied by this skill.

## Interpret results and verify

Parse stdout as NDJSON, one object per line. Use the process exit code and final `summary`; `file_started` is not evidence of success. Preserve partial-batch error information and report which PDFs were actually produced.

- Exit `0`: processing completed, **not validated anonymity**.
- Exit `4`: explicit unprocessed/retained surfaces require review.
- Exit `5`: at least one processing error; already completed files may remain.
- Exit `6`: output/source-path conflict; do not retry with overwrite blindly.
- Exit `2` or `3`: bad arguments/config or unavailable dependencies/model.

Check the actual generated files. Before 0.1.6 the detector often overwrote table dates, amounts and balances with address or PERSON replacements after OCR block reordering; 0.1.6–0.1.8 limit address tails and trim/filter PERSON spans per line, but some table values can still be hit, street names can pass as PERSON, and middle lines of replaced address blocks are left blank. Inspect both missed PII and deletion of non-PII; test every page, including the second page. For requested leak evaluation or a report, read [references/evaluation.md](references/evaluation.md).

Report the scope processed, errors/review flags, output locations and what was verified. Keep processing, detection coverage and leak verification distinct. Do not describe output as safe to share based only on exit `0`, empty exact-string matches or disappearance of the original image hash.
