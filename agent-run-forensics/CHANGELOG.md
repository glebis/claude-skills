# Changelog

All notable changes to the `agent-run-forensics` skill.

## [1.0.0] - 2026-09-14

### Added

- Initial release.
- Reads an earlier agent run from its recording rather than from the agent's memory of it: which step changed a file, why a command ran, where the build broke.
- Walks the causal chain to a single event instead of re-reading the whole timeline, and keeps `recorded` edges separate from `inferred` ones in the answer.
- Replays a recorded run offline, with the model's answers served from the trace and no provider contacted.
- Forks one run onto several models from the same checkpoint, graded by a shell command's exit code, so the model is the only variable.

### Notes

- Requires Node 20+ and the `orcareplay` CLI (Apache-2.0), which exposes an MCP server registered as `orca`.
- Replay re-executes the recorded tool calls for real; `egress=blocked` means model-provider egress, not network isolation. The skill instructs reading the recorded shell commands before the first replay and always passing `worktree: true`.
