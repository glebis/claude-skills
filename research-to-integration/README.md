# Research to Integration

A portable agent skill for researching technical options, running a bounded experiment, and delivering reusable code with a reproducible test. Designed for cloud agents with a handoff to local/GPU execution when necessary. MIT licensed.

## Install in Claude Code

```sh
claude plugin marketplace add glebis/claude-skills
claude plugin install research-to-integration@glebis-skills
```

If you already added the marketplace, refresh it first:

```sh
claude plugin marketplace update glebis-skills
claude plugin install research-to-integration@glebis-skills
```

Invoke the plugin skill:

```text
/research-to-integration:research-to-integration Investigate local open-source video-to-Gaussian-Splatting tools. Deliver reusable code and a reproducible experiment. Brief answers, one question at a time, autonomous mode.
```

Alternatively, install the plain skill for personal use:

```sh
git clone https://github.com/glebis/claude-skills.git
mkdir -p ~/.claude/skills
cp -R claude-skills/research-to-integration ~/.claude/skills/
```

Then invoke `/research-to-integration`. Choose plugin OR manual installation to avoid duplicate skills.

For another agent, copy the complete folder and load SKILL.md. The core instructions do not depend on Claude Code or ChatGPT-specific APIs. Supporting files are relative to SKILL.md. Download the repository ZIP using GitHub's Code → Download ZIP and extract this folder if you do not use Git.

## What it delivers

- A scoped experiment contract, current primary sources and a baseline plus feasible alternatives.
- Reusable implementation with a task-appropriate interface, explicit dependencies, errors and configuration.
- Meaningful tests, raw outputs, execution logs and a decision with evidence labels.
- A reproducible package if hardware, private input or network prevents target execution.

Separates measured behavior, upstream claims, inference and stages that were not run. Oracle-assisted transformation tests do not validate detection accuracy. Synthetic smoke checks do not establish production accuracy. The skill is an agent workflow, not a prebuilt PDF or 3D implementation.

## Configure

Provide `research-config.json` with your request or in the project. Settings are interpreted by the agent, not automatically enforced by a runtime. Explicit prompt instructions override project settings, which override assets/defaults.json.

```json
{
  "verbosity": "brief",
  "questions": {"mode": "bounded", "max_per_round": 1},
  "autonomy": "autonomous",
  "research_depth": "comparison",
  "budget": {
    "execution_minutes": 30,
    "per_command_timeout_seconds": 600,
    "download_mb": 2048,
    "paid_spend": 0
  }
}
```

See [all configuration semantics](references/configuration.md). Verbosity, question count, autonomy and research depth are independent. Language and interface are selected to fit the task. Defaults: cloud execution, up to three questions per round, agree substantive experiment choices then execute, reproducible-package fallback, no paid compute.

## Included command recorder

Python 3.9+; standard library only. No dependencies or credentials are required to load the skill. Individual experiments have their own dependencies.

```sh
python3 scripts/record_run.py --output /tmp/research-example-run --timeout 10 -- python3 -c 'print("hello")'
python3 -m unittest discover -s tests -v
```

The recorder saves stdout.log, stderr.log and run.json, refuses to overwrite an existing run directory, and records process success separately from quality validation. Do not pass secrets in command arguments or logs.

## Validation scope

The source skill structure, recorder success/failure/timeout/launch-error behavior and overwrite protection were tested. The workflow was also exercised on a planning-only CPU/no-video scenario. Claude Code installation and a real Gaussian Splatting backend were not run in the publishing environment. To validate the plugin on a machine with Claude Code:

```sh
claude plugin validate ./research-to-integration
```

## Command execution boundary

Only run reviewed commands authorized for the experiment. The recorder is not a sandbox and does not validate command intent, prevent file/network access, or sanitize output. Execute untrusted backends in an appropriate isolated environment, without credentials. It runs argv without a shell, forwards only basic runtime variables by default, and accepts repeated `--pass-env NAME` options for explicitly required environment variables. HOME and credentials are not forwarded automatically. Log files are private (0600) inside a private run directory (0700 on POSIX), but may still contain secrets printed by the command: inspect and sanitize before sharing. Timeouts must be finite and positive. POSIX timeouts terminate the process group; Windows does not provide equivalent descendant containment here.
