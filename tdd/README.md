# TDD Skill for Claude Code

Multi-agent TDD orchestrator that enforces RED-GREEN-REFACTOR cycles with architecturally isolated context between test writing and implementation. The Test Writer never sees implementation code; the Implementer never sees the specification.

## Usage

```
/tdd <feature description>          # Interactive mode with human checkpoints
/tdd --auto <feature description>   # Autonomous mode, stops only on errors
/tdd --resume                       # Resume from .tdd-state.json
```

## Features

- **Context isolation**: Separate agents for test writing, implementation, and refactoring with strict information boundaries
- **Vertical slicing**: Features decomposed into independently testable behavior slices
- **DDD/Onion layer awareness**: Slices sorted inside-out (domain first, infrastructure last) with layer-specific test constraints and dependency direction enforcement
- **Auto-retry**: Up to 5 implementation attempts per slice with fresh agent context on each retry
- **Greenfield support**: Works on projects with zero existing tests or source code
- **Framework detection**: Jest, Vitest, pytest, Go test, cargo test, RSpec, PHPUnit

## Architecture

```
ORCHESTRATOR (SKILL.md)
|-- Phase 0: Setup -- detect framework, extract API, create state file
|-- Phase 1: Decompose into vertical slices (inside-out by layer)
|
|-- FOR EACH SLICE:
|   |-- Phase 2 (RED):    Task(Test Writer)  <- spec + API + layer constraints
|   |   |-- Post-RED lint: block mocking libs in domain tests
|   |-- Phase 3 (GREEN):  Task(Implementer)  <- failing test + error + layer deps
|   |   |-- Layer path validation: reject files outside slice's layer
|   |   |-- Domain purity check (constructors, imports, statics)
|   |   |-- Full-repo import scan: catch violations in untouched files
|   |-- Phase 4 (REFACTOR): Task(Refactorer) <- all code + dependency direction audit
|
|-- Summary
```

## DDD / Onion Layer Support

Each slice is tagged with a layer (`domain`, `domain-service`, `application`, `infrastructure`) which determines:

| Layer | Test constraints | Dependency rule |
|-------|-----------------|-----------------|
| domain | No mocks, no framework imports, pure logic | Imports nothing from outer layers |
| domain-service | In-memory fakes for ports only | Imports domain only |
| application | In-memory fakes for all ports | Imports domain + domain-service |
| infrastructure | Integration tests, real deps allowed | Implements inner-layer interfaces |

Enforcement is multi-layered (not just textual reminders):

1. **Path validation** (GREEN phase): Implementer output files checked against `layer_map` — rejects writes to outer-layer directories
2. **Post-RED test lint**: Scans test code for mocking libraries (`jest.mock`, `Mock()`, etc.) in domain/domain-service tests
3. **Domain purity check**: Verifies constructors take no outer-layer types, no static calls to infrastructure
4. **Full-repo import scan**: Checks ALL source files (not just session-modified) for dependency direction violations
5. **Refactorer audit**: Checks direct + transitive dependency violations, flagging as high-priority suggestions

Port interface rule: **the consumer defines the contract** — ports live in the layer that needs them, not the layer that implements them.

This layer awareness degrades gracefully: for simple projects where everything lives in one layer, all slices get `layer: "application"` and the constraints don't add overhead.

Edge cases handled: infrastructure-only features, missing port interfaces (created by first slice that needs them), and cross-cutting slices (tagged by innermost layer touched).

## File Structure

```
tdd/
|-- SKILL.md                          # Main orchestrator (read by Claude Code)
|-- README.md                         # This file
|-- scripts/
|   |-- run_tests.sh                  # Test runner wrapper (JSON output)
|   |-- extract_api.sh                # Public API surface extractor
|-- references/
    |-- agent_prompts.md              # Agent prompt templates + constraint lookup
    |-- anti_patterns.md              # TDD and layer anti-pattern reference
    |-- framework_configs.md          # Per-framework test skeletons
    |-- layer_guide.md                # DDD/Onion layer definitions + test strategy
```

## Research-Informed Design

The layer-aware testing approach is informed by empirical software engineering research:

- **AI code + no arch constraints = 80% violation rate**: LLM-generated code violates hexagonal architecture boundaries 80% of the time without explicit enforcement. Layer constraints in agent prompts directly counteract this. (arXiv:2412.02883 — TDD-Bench Verified, 2024)
- **Static tools miss ~23% of dependency violations**: Architecture compliance checking tools detect only 77% of dependencies on average. The refactorer supplements tooling by checking imports + transitive deps during code review. (Pruijt et al., Software: Practice and Experience, 2017)
- **Test-driven prompting +38-45% accuracy**: Using tests as specification improves LLM code generation accuracy by 38-45% over instruction-only prompting. RED-first is empirically better than spec-first for AI agents. (Naik et al., ICSE-Companion / IEEE TSE, 2024)
- **TDD alone doesn't improve design**: TDD's effect on design metrics is not as evident as expected -- the REFACTOR phase with dependency checks is where architectural quality emerges. (Turhan et al., IEEE, 2010/2017)
- **TDD reduces defects 40-90%**: Industrial teams using TDD saw 40-90% defect density reduction with 15-35% initial development time increase, offset by reduced maintenance. (Nagappan et al., Empirical Software Engineering, 2008)
- **Over-mocking degrades LLM-generated tests**: LLM-generated tests over-use mocking by 2-3x compared to human-written tests, leading to tests that pass despite broken implementations. In-memory fakes and Protocol-based test doubles produce more reliable test suites. (arXiv:2602.00409, 2025)

Full research survey: see `references/layer_guide.md` for citations applied to specific design decisions.

## Installation

Copy `tdd/` to `~/.claude/skills/tdd/` and ensure `scripts/*.sh` are executable:

```bash
cp -r tdd/ ~/.claude/skills/tdd/
chmod +x ~/.claude/skills/tdd/scripts/*.sh
```
