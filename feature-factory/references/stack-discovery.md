# Stack Discovery — finding the repo's real verify commands

Expands step 4 of the loop. This is a **discovery checklist, not a config layer** — read it, look at the actual repo, and record what you found in `evidence/verify.log`. Do not turn it into a `factory.config`, an adapter, or a universal wrapper; the repo's own conventions stay the source of truth.

## Where the truth lives (check in this order)

1. **CI workflow files** — `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`, `.buildkite/`. Whatever CI runs on a PR **is** the verify contract; local commands that diverge from CI are guesses. If CI exists, mirror it.
2. **Repo-level task runners** — `Makefile`, `justfile`, `Taskfile.yml`, `scripts/` with an obvious `check`/`verify`/`ci` target. A repo that bothered to define `make check` wants you to use it.
3. **Agent/contributor docs** — `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, README "Development" section. These often name the one blessed command.
4. **Ecosystem manifests** — only if the above are silent:
   - **JS/TS**: `package.json` scripts (`test`, `lint`, `typecheck`, `build`); respect the lockfile's package manager (pnpm/yarn/npm/bun).
   - **Python**: `pyproject.toml` (`[tool.*]` sections reveal pytest/ruff/mypy), `tox.ini`, `noxfile.py`; respect the env manager in use (uv/poetry/pip).
   - **Rust**: `cargo test` · `cargo clippy -- -D warnings` · `cargo fmt --check` · `cargo build`.
   - **Go**: `go test ./...` · `go vet ./...` · `golangci-lint run` if configured · `go build ./...`.
   - **JVM**: `./gradlew check` or `mvn verify` — prefer the wrapper script committed to the repo.
   - **Elixir**: `mix test` · `mix format --check-formatted` · `mix credo`/`mix dialyzer` if configured.
   - **Other stacks**: same shape — the manifest or the community's standard check commands; when unsure, the CI file (step 1) decides.
5. **Secrets scan** — run one if the repo has it wired (gitleaks/trufflehog config, a pre-commit hook); don't bolt one on for a single feature.

Not every repo has all four check types (test · lint · typecheck · build). Run what the repo actually defines; note in `verify.log` which categories don't exist rather than inventing them.

## When there is no test harness at all

TDD (step 3) needs a runner to go red → green. If the repo has zero test infrastructure:

- **Bootstrap the stack's standard runner, minimally** — pytest, vitest/jest (match the repo's existing tooling), `cargo test` / `go test` (built-in, nothing to add), ExUnit, JUnit via the existing build tool. One config file and one test directory; no coverage gates, no CI redesign.
- Adding the harness is part of the feature's cost — if bootstrapping it is itself a day of work, that's a size trigger: re-triage (likely L, or split).
- Match the repo's language and idioms; don't introduce a second language or framework just because you prefer its test story.
