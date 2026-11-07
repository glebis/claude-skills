# Research to Integration: SkillSpector audit, 2026-11-07

## Outcome

Manual verdict: **CAUTION**. No malicious behavior or confirmed exploitable HIGH/CRITICAL defect was established by this source review. The tool executes explicitly supplied commands by design and is not a sandbox. Use reviewed commands in an appropriately scoped environment. This review does not certify the skill or override SkillSpector's recommendation.

**The unmodified static scanner did NOT pass.** Before: 83/100, CRITICAL, DO_NOT_INSTALL (2 HIGH findings, 6 MEDIUM). After: 100/100, CRITICAL, DO_NOT_INSTALL (5 HIGH, 9 MEDIUM). CRITICAL is the aggregate score band, not the severity of an individual finding. No finding suppressions, baselines or file exclusions were used. The higher score includes additional security tests and a negative instruction about secrets; it does not establish a regression in runtime behavior.

Scanner: NVIDIA SkillSpector 2.12.0, source revision `e48d771a26f7398b36256ceb8d8f94adce3d5c44`. Audited baseline: `glebis/claude-skills@43f920acead50e8d9f6b3e629df966a033d06217`, directory `research-to-integration`. Patched source hashes are in source-sha256.json. Raw JSON paths were normalized to `<workspace>`; findings and scores were not edited.

## Method and coverage

Used the project's `skills/skill-inspector/SKILL.md` workflow: static evidence plus a source-aware agent review. Ran `skillspector scan TARGET --no-llm --format json --output REPORT --fail-on-incomplete`. LLM semantic analysis through a provider was not requested or run. The agent's manual review is separate from the scanner's semantic stage. The scanner did not execute target scripts. Tests were run separately after code changes.

Before and final scans report 100% component coverage and `is_complete: true`, with status `complete_with_caveats`. The caveat is an unresolved reference to user-created runtime research-config.json, not a bundled file. Dependency-source inspection is not a certification of future experiment dependencies; the bundled recorder itself uses only Python's standard library. SC4 may query dependency coordinates through OSV even with --no-llm; no inference provider was used.

An intermediate scan encountered local test-generated __pycache__/pyc artifacts, added binary-file warnings and marked analysis incomplete. Those generated, untracked files are not publication assets; they were removed before the final full-directory scan. The final raw report includes the full text sources and tests with no exclusions.

## Actual hardening

- Explicitly separate untrusted pages/repositories/model outputs/config from user authorization. Require command/output review against the experiment contract.
- State intended tool scope without adding blanket allowed-tools preapproval; preserve host permission checks and authorized project boundaries.
- Make clear that the recorder is not a sandbox, log sanitizer or command validator.
- Replace implicit environment inheritance with a small runtime-variable allowlist; require explicit --pass-env NAME for additional variables. Do not log variable values in metadata.
- Create private POSIX run directories (0700) and exclusive log/metadata files (0600), retaining overwrite refusal.
- Make shell=False explicit; retain argv execution and close inherited file descriptors.
- Reject non-finite, zero and negative timeouts; use monotonic elapsed time and handle interruption/process-group cleanup.
- Require inspection/sanitization of artifacts before sharing; private permissions do not sanitize secret-bearing logs.

These are defense-in-depth improvements found during source review. Do not misattribute all of them to scanner findings or claim the previous arbitrary-command helper could safely sandbox hostile code.

## Finding triage (final scan)

| Rule | Severity / location | Source-aware judgment |
|---|---|---|
| PE3 | HIGH, SKILL.md:18 | The matched phrase `access secrets` appears in an explicit prohibition: never adopt untrusted instructions to do this. False positive in this context; the prohibition is retained. |
| OH1 | HIGH, tests/test_record_run.py:22,30,51 | Subprocess argv are constructed from fixed synthetic test cases and temporary paths, not LLM output. shell=False is explicit. No flow from model output exists in these tests; false-positive classification. |
| E2 | HIGH, tests/test_record_run.py:45 | Synthetic RESEARCH_TEST_SECRET canary in a child-process test. It verifies that the recorder does not forward it by default and forwards it only when explicitly requested. No transmission endpoint; no actual secret is added. The test process inherits the caller environment in the conventional way, so run tests in a suitable environment. |
| RA2 | MEDIUM, README.md:30 | Manual user-invoked skill installation example, not a self-installing persistence mechanism. |
| LP3 | MEDIUM, SKILL.md:1 | No preapproved tool list is intentionally declared. Tool needs are documented in the body and host permissions remain authoritative. Adding allowed-tools merely to silence this would grant permissions, not enforce a ceiling. |
| EA2 | MEDIUM, references/scenarios.md:25 | Instruction to resolve routine language/interface choices autonomously within an already authorized experiment. It does not authorize destructive/financial actions or bypass permissions. |
| AST4 | MEDIUM, scripts/record_run.py:59 and tests:22,30,38,51 | Intentional argv subprocess execution. In tests the commands are fixed; the recorder accepts caller-authorized commands. This is a genuine execution surface and the main reason for CAUTION. |
| TT2 | MEDIUM, scripts/record_run.py:59 | Selected environment variables flow to an intentionally launched child. Basic runtime variables are allowlisted; extra variables require explicit opt-in. Risk remains when a caller explicitly supplies credentials to an untrusted command. |

## Executed verification

Ran the published regression suite with three test methods covering success, nonzero exit, timeout, missing executable, overwrite refusal, NaN/infinite/nonpositive timeout rejection, literal shell-looking arguments, default environment filtering, explicit canary forwarding, omission of values from metadata, and POSIX file/directory modes. All passed on Linux/Python 3.12. The installed skill's structure validator also passed.

## Remaining limits

No LLM-backed SkillSpector scan, adversarial prompt-injection behavior trial, macOS/Windows runtime test, sandbox escape test or complete security audit was performed. Runtime-config and downloaded-code risks remain subject to the executing agent and host policy. Logs can contain command-produced secrets; pass-env can deliberately expose secrets; selected PATH may resolve attacker-controlled executables; the recorder cannot prevent file/network access. Windows descendant cleanup is weaker than POSIX. Do not run unknown code in a credentialed environment based on this report.

## Reproduce

```sh
git clone https://github.com/NVIDIA/SkillSpector.git
cd SkillSpector
git checkout e48d771a26f7398b36256ceb8d8f94adce3d5c44
uv venv .venv
uv pip install --python .venv/bin/python .
.venv/bin/skillspector scan /path/to/claude-skills/research-to-integration --no-llm --format json --output /trusted/output/report.json --fail-on-incomplete
```

Use a clean source directory (no generated pyc files) and store reports outside the scanned skill. Expect a nonzero scanner exit for this source; do not treat it as passing or mask it with an accepted baseline. Review context rather than optimizing source spelling for the score.
