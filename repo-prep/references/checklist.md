# Repo-prep checklist & per-item guidance

The full menu. Confirm which items apply (the profile `defaults` pre-answer
most), then generate each from its template, filling placeholders. Skip items
already present unless the user wants them refreshed.

## Placeholders used across templates

Resolve these once, reuse everywhere:

| Placeholder | Source |
|---|---|
| `{{project}}` | repo/dir name or package name |
| `{{author}}`, `{{email}}`, `{{github}}` | profile `[author]` |
| `{{year}}`, `{{date}}` | current year / ISO date |
| `{{license}}`, `{{license_name}}` | chosen SPDX id / full name |
| `{{repo_url}}`, `{{default_branch}}` | `git remote get-url origin`, default branch |
| `{{setup_cmd}}`, `{{test_cmd}}`, `{{ecosystem}}` | detected from manifest (below) |
| `{{stack}}`, `{{ai_tools}}`, `{{location}}`, `{{provider_terms}}` | authorship interview |

## Ecosystem detection

| Manifest | ecosystem | typical test_cmd |
|---|---|---|
| `pyproject.toml` | pip / uv | `pytest -q` or `uv run pytest -q` |
| `package.json` | npm | `npm test` |
| `Cargo.toml` | cargo | `cargo test` |
| `go.mod` | gomod | `go test ./...` |

## 1. Core legal / metadata (baseline — almost always)

- [ ] **LICENSE** — `scripts/fetch_license.py <id> --author ...`. See `licenses.md`.
- [ ] **NOTICE** (Apache only) — `assets/templates/NOTICE.txt`.
- [ ] **AUTHORSHIP.md** — run the **authorship wizard** (`authorship-wizard.md`).
      Do *not* just dump the template; interview + gather evidence.
- [ ] **Package metadata** — set `license` (SPDX) + author name/email in the
      manifest. Edit inline per ecosystem:
      - `pyproject.toml`: `license = "<id>"`, `license-files = ["LICENSE"]`,
        `authors = [{ name, email }]`.
      - `package.json`: `"license": "<id>"`, `"author": "Name <email>"`.
      - `Cargo.toml`: `license = "<id>"`, `authors = ["Name <email>"]`.
- [ ] **.gitignore** — ensure language-appropriate ignores + local tool
      artifacts. Fetch from <https://github.com/github/gitignore> if missing.

## 2. Community docs

- [ ] **README** — audit for: title + one-line description, badges, install,
      usage, license section, and the **promo block** (below). Add a
      `## License` section linking LICENSE (+ AUTHORSHIP).
- [ ] **CONTRIBUTING.md** — `assets/templates/CONTRIBUTING.md` (includes the
      AI-assisted-contribution + license-compatibility clause).
- [ ] **CODE_OF_CONDUCT.md** — `assets/templates/CODE_OF_CONDUCT.md`.
- [ ] **SECURITY.md** — `assets/templates/SECURITY.md` (private vuln reporting).
- [ ] **CHANGELOG.md** — `assets/templates/CHANGELOG.md` (Keep a Changelog).

## 3. .github/ templates

- [ ] **pull_request_template.md**, **ISSUE_TEMPLATE/** (bug + feature) — from `assets/github/`.
- [ ] **dependabot.yml** — set `{{ecosystem}}`.
- [ ] **CI workflow** — copy `ci-python.yml` or `ci-node.yml` to
      `.github/workflows/ci.yml`; set `{{default_branch}}`/`{{test_cmd}}`.
- [ ] **FUNDING.yml** — only if profile has a `sponsor`.

## 4. Promo block ("ads")

From profile `[promo]` (skip if `enabled = false`). Append a README footer:

```md
## More from {{author}}

> {{tagline}}

- **[name](url)** — blurb
- ...
```

Keep it to 3–6 links. Per-repo, the user may opt out.

## 5. EU / Germany compliance (conditional)

Run the gating questions in `eu-germany-compliance.md`. Add only what applies
(SBOM/CI audit, AI-transparency note, IMPRESSUM.md, PRIVACY.md, non-commercial
framing). For a personal non-commercial repo with no data collection, usually
nothing beyond LICENSE/NOTICE/SECURITY.md.

## 6. GitHub remote setup (gh) — optional, confirm first

Outward-facing; confirm before running.

- [ ] Repo exists? `gh repo view` — else `gh repo create`.
- [ ] Description + topics: `gh repo edit --description "…" --add-topic a,b,c`.
- [ ] Default branch matches `{{default_branch}}`.
- [ ] Enable private vulnerability reporting (Settings → Security).

## Finish

- Run the test suite to confirm metadata changes didn't break the build.
- Show the user the diff; commit only when asked (per their git conventions).
