# Existing runtime on this machine

These paths are local conveniences, not portable installation requirements.

- Existing venv: `/Users/glebkalinin/Documents/Codex/2026-11-07/new-chat/work/pdf-env`
- Installed CLI: `/Users/glebkalinin/Documents/Codex/2026-11-07/new-chat/work/pdf-env/bin/pii-pdf`
- Source package and manual: `/Users/glebkalinin/Documents/Codex/2026-11-07/new-chat/outputs/pii-pdf-cli/`
- Previous automatic-test report: `/Users/glebkalinin/Documents/Codex/2026-11-07/new-chat/outputs/auto-pii-test-report.html`

This is the historical 0.1.0 / PyMuPDF 1.26.6 environment. It is retained for reproducing the old benchmark, not for processing new documents. Use setup mode to create the patched runtime. If it has moved or is missing, use the current setup mode when requested, rather than assuming an older chat environment still exists.

The bundled source is CLI version 0.1.2 (0.1.1 plus a fix for output publication on macOS) with dependency floors PyMuPDF >=1.26.7 and build setuptools >=78.1.1. Detection rules are unchanged from the earlier baseline. A new installed version may expose different options; inspect the live schema.
