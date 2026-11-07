# Existing runtime on this machine

These paths are local conveniences, not portable installation requirements.

- Existing venv: `/Users/glebkalinin/Documents/Codex/2026-11-07/new-chat/work/pdf-env`
- Installed CLI: `/Users/glebkalinin/Documents/Codex/2026-11-07/new-chat/work/pdf-env/bin/pii-pdf`
- Source package and manual: `/Users/glebkalinin/Documents/Codex/2026-11-07/new-chat/outputs/pii-pdf-cli/`
- Previous automatic-test report: `/Users/glebkalinin/Documents/Codex/2026-11-07/new-chat/outputs/auto-pii-test-report.html`

This is the historical 0.1.0 / PyMuPDF 1.26.6 environment. It is retained for reproducing the old benchmark, not for processing new documents. Use setup mode to create the patched runtime. If it has moved or is missing, use the current setup mode when requested, rather than assuming an older chat environment still exists.

The bundled source is CLI version 0.1.8 (0.1.2 publication fix, 0.1.3 account-number rules, 0.1.4–0.1.5 multi-line address blocks, 0.1.6–0.1.8 table-safety: address tail limits, per-line PERSON trimming and filtering) with dependency floors PyMuPDF >=1.26.7 and build setuptools >=78.1.1. Account-number (0.1.3) and multi-line address (0.1.4–0.1.5) and table-safety (0.1.6–0.1.8) rules changed; other detection rules are unchanged from the earlier baseline. A new installed version may expose different options; inspect the live schema.
