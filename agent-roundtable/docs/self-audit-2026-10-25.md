# agent-roundtable — self-audit result (focus: ACP reliability)

2026-10-25 · codex (ACP, auditor), cmd (ACP, architect), claude (ACP, devil's advocate) · roles · 3 rounds · stopped on consensus in round 3

## Summary
The reasoning layer (strict parser, consensus rule) is sound and tested. The transport lifecycle is not. A timed-out turn leaves an orphaned update reader that can steal or blank later turns, and a dead or hung agent stays "live" with no recovery. Both degrade the result without the moderator noticing. Read-only enforcement, edit detection and the auto-mode moderator handshake are also weaker than documented. ACP stays, but as one of two equal transports next to headless CLIs with native resume, which replace today's history-replay fallback.

## Final specification
- **One reader per session.** A turn never calls `prompt()` while the previous turn's prompt is still unsettled. On timeout: send `session/cancel`, then drain to the old turn's `stop` for at most 30 s. If it doesn't arrive, discard the session and kill the agent.
- **Recovery ladder (user decision).** A *failed attempt* is any turn attempt that crashes, hangs, times out or stops with something other than `end_turn`. Each agent gets at most 3 attempts over the whole run, counted in `failedTurns`:
  - 1st failure: restart ACP, rebuild context from the completed `rounds/` files, and re-run the turn in the same round.
  - 2nd failure: switch to headless with native resume, bootstrapped the same way, and re-run the turn.
  - 3rd failure: drop the agent and mark the run degraded.
  A failed agent's vote is cleared immediately.
- **Degraded runs are labelled.** `state.json` keeps per-agent `{ok, transport, lastError, failedTurns}`, updated every turn. `state.result = "degraded"` whenever an agent was switched or dropped. The consensus reason and the synthesis name the degraded agents, and a degraded run is never reported as full consensus.
- **Native-resume headless transport.** It replaces history replay and tracks an explicit native session id per agent (an ACP session id is not a CLI resume id). It never resumes "the latest session" in a shared cwd. If no native id exists, it starts a new CLI session once from the completed turns, then resumes that id.
- **Prompt delivery.** `{prompt}`, `{out}` and `{cwd}` are substituted in a single pass with a function replacer, and the prompt goes over stdin or a file for every adapter, never through argv.
- **Permission policy (best effort, user decision).**
  - Deny: a missing kind or a kind outside the ACP enum; `edit`/`delete`/`move` with no `locations`; `edit`/`delete`/`move`/`other` with any location inside `cwd` or `runDir`.
  - Allow: `read`, `search`, `fetch`, `think` and `execute` wherever their locations are; `edit`/`delete`/`move`/`other` when every location is outside `cwd` and `runDir`. `execute` and `other` are logged with their title.
  - Never decide from the tool's title.
- **Default transports:** codex = headless with resume and `--sandbox read-only`; cmd = ACP, falling back to `cmd --resume --permission-mode plan`; claude = ACP, falling back to `claude -p --resume --permission-mode plan`. A default changes only after that transport passes the acceptance tests.
- **Edit detection.** Fingerprint tracked and untracked content: SHA-256 of `git diff --binary HEAD` plus hashes of untracked file contents, with `runDir` excluded. Take the baseline before agents start, then check after every round and after the veto. Gitignored files are **not** covered; `state.json` and the result say so.
- **Moderator handshake.** The runner detects a deadlock itself (the same blocking set two rounds running) and switches to `awaiting_moderator` even in auto mode. At the start of each round it consumes moderator notes it hasn't read yet. Every handshake file (`state.json`, `moderator/rN.md`, `synthesis.md`) is published atomically (tmp file + rename), and the runner only reads the final name. A run dir that already has `moderator/` or `synthesis.md` is refused.
- **stopReason.** Recorded for every turn. Anything other than `end_turn` is a failed turn, and a veto approval requires `end_turn`.
- **Lifecycle.** `close()` waits for the process to exit and sends SIGKILL after 5 s. Every exit path runs it: a `try/finally` around the run, plus SIGINT/SIGTERM handlers. Headless children are tracked.

## Tasks
| # | Priority | Task | Closes | Verify with |
|---|---|---|---|---|
| 1 | blocker | One reader per session; cancel + bounded drain, else discard | CLAUDE-1 (CODEX-1, CMD-1) | fake agent: timeout + late update; cancel ignored then prompt |
| 2 | blocker | Awaited `close()` with SIGKILL escalation on every exit path | CODEX-3 (CMD-4) | fake child ignoring SIGTERM is gone after the grace period |
| 3 | blocker | Recovery ladder, per-turn health, degraded result | CLAUDE-2 (CODEX-7, CMD-2) | fake agent: crash → restart; hang ×2 → headless → drop, `result: degraded` |
| 4 | major | Record stopReason; non-`end_turn` = failed turn; veto needs `end_turn` | CLAUDE-7 | fake agent returning `cancelled` |
| 5 | major | Native-resume headless adapters, single-pass substitution, stdin/file input | CLAUDE-6 (CODEX-8, CMD-7) | `$$ $& {out}` reaches the CLI unchanged; 3 turns + veto per adapter |
| 6 | major | Path-scoped permission policy; headless sandbox and plan-mode flags | CODEX-4 (CLAUDE-5, CMD-6) | policy unit test: `/tmp` write allowed, in-target write denied, in-target read allowed |
| 7 | major | Runner-detected deadlock → moderator handshake in auto mode | CLAUDE-3 (CMD-3) | 2 rounds with the same blocking set → `awaiting_moderator` |
| 8 | major | Content-fingerprint edit detection, `runDir` excluded, checked after the veto | CODEX-5 (CLAUDE-4, CMD-5) | further edit to an already-dirty file is detected; run files don't warn |
| 9 | major | Atomic publication of all handshake files; refuse a reused run dir | CODEX-6 | a slowly written synthesis is never read half-done; second run into the same dir exits |
| 10 | major | Veto prompt includes every agent's final-round status and reply summary | new: veto visibility (moderator, from CMD's veto) | each veto prompt lists all peers' last stance |

## Improvements
- `doctor` sends a one-line prompt with a short timeout. This would have caught the expired OpenCode key and the Gemini OAuth failure. (CLAUDE-8, CMD-8; cheap, so do it early.)
- Detect auth from the ACP error code and the advertised `authMethods`, never from message text. "Internal error" alone must not trigger an authentication guess. (CLAUDE-8)
- Regression test that a rejected prompt surfaces its original error. (CODEX-2)
- Add a `rounds` array to `state.json` with per-agent duration, outcome and transport.
- Warn when `--format roles` is used without `--roles`; fix the SKILL.md wording about a Claude seat and model diversity.
- Pausing the budget while waiting for the moderator is a product choice, deferred.

## Open disagreements
None blocking. Remaining differences in emphasis:
- **Where cleanup sits in the order.** CODEX and CLAUDE put CODEX-3 right after CLAUDE-1, because the recovery ladder kills and replaces processes. CMD ranks it last, because it leaks resources rather than results. The task table follows CODEX and CLAUDE.
- **Content fingerprints before the next run.** CODEX and CLAUDE: required. CMD: excluding `runDir` is enough for now, and fingerprints can wait. The table lists them as major, after the transport work.
- **Codex's transport until the resume adapter exists.** CMD: codex stays on ACP with the recovery ladder until headless with resume lands. CLAUDE: the recovery decision needs the resume adapter before the next run anyway. Either way, nothing flips until the acceptance tests pass.

## Refuted or dropped findings
- **CODEX-2** (a prompt rejection surfaces as a fake timeout): refuted by CMD's and CLAUDE's real-SDK probes; the SDK rejects the waiting reader with the original error. Only a regression test remains.
- **Worktree/copy isolation** (CLAUDE-5): dropped per the user's decision that read-only stays best effort.
- **Severity of CLAUDE-3**: settled as major, not blocker, but still on the pre-run list.

## Moderator notes
- I observed this during the run: CMD's round-1 turn ended with no audit after the runner rejected its `/tmp` writes, and `state.json` still showed CMD as healthy. That is CLAUDE-2, CLAUDE-7 and CODEX-4 together, seen live.
- The consensus rule worked as designed and stopped the debate in round 3. The auto-mode handshake was not exercised (this was an active-mode run).

## Veto
- **codex: objected, fixed.** Atomic publication now covers every handshake file (task 9, raised to major). The permission location rule is limited to the kinds that change files. The fingerprint's exclusion of gitignored files is now stated. The recovery ladder now has exact attempt accounting and rebuilds context on an ACP restart.
- **claude: objected, fixed.** Same permission rule fix, and task 6 now also checks that an in-target `read` is allowed.
- **cmd: objected, not accepted.** It said the stop on consensus was misreported. `rounds/r3.summary.json` shows all three agents `converged` with empty `blocking` in round 3, so `stopReason` is right. CMD was looking at its peers' round-2 replies, because the veto prompt never shows the other agents' final round. That gap is now task 10.
