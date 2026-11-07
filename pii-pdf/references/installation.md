# Installation

Requires Node.js 22.20+ for the skills installer, and Python 3.10+ for this engine.

Install globally for Claude Code:

```sh
npx skills add glebis/claude-skills --skill pii-pdf -a claude-code -g
```

For a project-only installation, omit `-g`. For Codex, use `-a codex`.

Then ask the agent:

```text
/pii-pdf setup
```

Setup uses the bundled visible CLI source and installs dependencies in `~/.local/share/pii-pdf/venv`. It checks source hashes before installing. The English spaCy model is versioned; Tesseract and English OCR data must be available. On supported systems the setup can install missing Tesseract through the existing package manager. It does not install Homebrew or invoke sudo automatically.

Check installation and a synthetic redaction scenario:

```text
/pii-pdf doctor
```

A passing synthetic smoke check does not validate arbitrary documents. Treat redacted PDFs as requiring review.

Standalone Python toolkit: https://github.com/glebis/pii-pdf

This skill carries CLI 0.1.2 with the same experimental detection rules. When updating the snapshot, update `assets/source.sha256` and validate setup/doctor before publishing.
