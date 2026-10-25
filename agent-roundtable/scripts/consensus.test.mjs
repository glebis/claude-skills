// npm test (from scripts/)
import { test } from "node:test";
import assert from "node:assert/strict";
import { assessConsensus } from "./consensus.mjs";

const vote = (agent, over = {}) => ({ agent, parsed: true, stance: "converged", blocking: [], new_issues: [], resolved: [], ...over });
const ctx = (over = {}) => ({ round: 2, maxRounds: 3, minRounds: 2, expectedAgents: ["codex", "cmd"], ...over });

test("everyone converged, nothing blocking or new: stop", () => {
  assert.equal(assessConsensus([vote("codex"), vote("cmd")], ctx()).converged, true);
});

test("never before the minimum round", () => {
  assert.equal(assessConsensus([vote("codex"), vote("cmd")], ctx({ round: 1 })).converged, false);
});

test("a missing vote blocks", () => {
  const r = assessConsensus([vote("codex")], ctx());
  assert.equal(r.converged, false);
  assert.match(r.reason, /cmd/);
});

test("an invalid status block blocks", () => {
  assert.equal(assessConsensus([vote("codex"), vote("cmd", { parsed: false, stance: "open" })], ctx()).converged, false);
});

for (const [name, over] of [
  ["an open stance", { stance: "open" }],
  ["a contradictory converged + blocking", { blocking: ["CMD-1: x"] }],
  ["a new issue", { new_issues: ["CMD-9"] }],
]) {
  test(`${name} blocks`, () => {
    assert.equal(assessConsensus([vote("codex"), vote("cmd", over)], ctx()).converged, false);
  });
}

test("deadlock = same non-empty blocking ids two rounds running", async () => {
  const { blockingIds, isDeadlock } = await import("./consensus.mjs");
  const ids = blockingIds([vote("codex", { blocking: ["CMD-2: x", "CODEX-1: y"] }), vote("cmd", { blocking: ["CMD-2: other words"] })]);
  assert.deepEqual(ids, ["CMD-2", "CODEX-1"]);
  assert.equal(isDeadlock(null, ids), false);
  assert.equal(isDeadlock(["CMD-2", "CODEX-1"], ids), true);
  assert.equal(isDeadlock(["CMD-2"], ids), false);
  assert.equal(isDeadlock([], []), false);
});
