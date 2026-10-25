// Decides whether the debate can stop before the round limit.
//
// statuses: one entry per agent with a current vote, e.g.
//   { agent: "codex", parsed: true, stance: "converged" | "open",
//     blocking: ["CODEX-3: no test for empty input"], new_issues: ["CODEX-7"], resolved: [] }
//   parsed:false means the agent forgot or mangled its status block. An agent whose
//   turn failed has no entry at all.
// ctx: { round, maxRounds, minRounds, expectedAgents }  (expectedAgents = agents that should have answered)
//
// Returns { converged: boolean, reason: string }. reason is written to the run log
// and shown to the moderator, so it says *why*.
//
// Rule: stop only when every expected agent cast a valid vote, all say "converged",
// nobody holds a blocking objection, and nobody raised a new issue this round.
// Silence or a broken status block counts against consensus, never for it.
export function assessConsensus(statuses, ctx) {
  if (ctx.round < ctx.minRounds) {
    return { converged: false, reason: `round ${ctx.round} is below the minimum of ${ctx.minRounds}` };
  }
  const byAgent = new Map(statuses.map((s) => [s.agent, s]));
  const missing = ctx.expectedAgents.filter((id) => !byAgent.has(id));
  if (missing.length) return { converged: false, reason: `no current vote from ${missing.join(", ")}` };

  const invalid = statuses.filter((s) => !s.parsed).map((s) => s.agent);
  if (invalid.length) return { converged: false, reason: `invalid status block from ${invalid.join(", ")}` };

  const open = statuses.filter((s) => s.stance !== "converged").map((s) => s.agent);
  if (open.length) return { converged: false, reason: `still open: ${open.join(", ")}` };

  const blocking = statuses.flatMap((s) => s.blocking);
  if (blocking.length) return { converged: false, reason: `"converged" but still blocking: ${blocking.join("; ")}` };

  const fresh = statuses.flatMap((s) => s.new_issues);
  if (fresh.length) return { converged: false, reason: `new issues raised: ${fresh.join(", ")}` };

  return { converged: true, reason: `all ${statuses.length} agents converged with no blocking or new issues` };
}

// The finding ids behind a set of blocking objections ("CODEX-3: reason" -> "CODEX-3").
export function blockingIds(statuses) {
  return [...new Set(statuses.flatMap((s) => s.blocking ?? []).map((b) => b.split(":")[0].trim()))].sort();
}

// Deadlock: the same non-empty blocking set two rounds running.
export function isDeadlock(previousIds, currentIds) {
  return !!previousIds && currentIds.length > 0 && previousIds.join("\n") === currentIds.join("\n");
}
