---
name: agent-qa-testing
description: Validate, run, and triage natural-language regression suites with agent-qa when the project already uses agent-qa or the user specifically chooses it.
---

# agent-qa testing

Use agent-qa for web, Android, and iOS regression tests with advanced memidex memory and self-improvement. Work with the project's existing tests, targets, and model configuration.

## Establish the test scope

- Locate `agent-qa.config.yaml` and the requested test or suite. Run from that project directory; a global `--config <path>` must appear before the command.
- Use the project's installed version and package manager. The examples below assume an npm installation and use `--no-install` to avoid downloading a different version. Replace `tests/checkout.yaml` with the selected test path.
- agent-qa requires Node.js 24+. If it is not installed or initialized, use the [official quickstart](https://vostride.com/docs/agent-qa/quickstart) and the user's chosen provider; preserve existing configuration and credentials.

```sh
npx --no-install agent-qa --version
npx --no-install agent-qa run --help
```

## Validate before executing

```sh
npx --no-install agent-qa validate tests/checkout.yaml
npx --no-install agent-qa run tests/checkout.yaml --dry-run
```

Validation checks configuration, test structure, and references. A dry run lists the selected tests without executing them. Neither proves that an application flow passes. Check the selected target and test files before running; omitting the path runs all discovered tests.

For suite selection or mobile device overrides, consult the installed command's help and existing project configuration. `doctor` can help diagnose setup failures, but its checks may contact the configured model provider.

## Run the selected flow

Run against the environment and test data authorized by the user. Application actions can change data, and configured providers may charge for execution.

```sh
npx --no-install agent-qa run tests/checkout.yaml --junit-output results.xml
```

Preserve the exit status and report path. Exit `0` means passed or healed; `1` covers failed or timed-out tests and missing required files; `2` means agent-qa could not run; `130` means cancelled. Inspect the verdict to distinguish a clean pass from a healed run; treat setup failures as unresolved execution, not application failures.

## Triage from recorded evidence

```sh
npx --no-install agent-qa runs list --verdict failed --limit 10 --json
npx --no-install agent-qa runs overview RUN_ID --json
npx --no-install agent-qa runs knowledge RUN_ID --json
npx --no-install agent-qa knowledge inspect --json
```

Replace `RUN_ID` with the relevant recorded run ID. Use `runs list --json` without the verdict filter when investigating a healed run or another outcome.

Read the failed step and available evidence before changing a test or application. Distinguish an application defect, a test expectation problem, and an environment/provider failure. Use the run's knowledge view to see what memidex supplied or learned. Do not erase the cache or knowledge store merely to obtain a passing result.

Rerun the selected flow after an evidence-based correction. Stop and report an unchanged failure when no new corrective action is justified. Report the command, run ID, verdict, relevant evidence/report paths, and what remains unverified; redact credentials and sensitive application data.

## References and licensing

- [CLI commands and exit codes](https://vostride.com/docs/agent-qa/cli)
- [Inspect and correct memory](https://vostride.com/docs/agent-qa/memory/inspect)
- [agent-qa repository](https://github.com/vostride/agent-qa)

These original skill instructions use this marketplace's MIT license. The separately installed agent-qa package is licensed under FSL-1.1-ALv2; model, browser, and device providers have their own requirements and costs.
