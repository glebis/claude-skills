// npm test (from scripts/). Runs roundtable.mjs end to end against fake agents.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync, execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const RUNNER = join(HERE, "..", "roundtable.mjs");
const FAKE = join(HERE, "fake-agent.mjs");
const FAKE_CLI = join(HERE, "fake-cli.mjs");
const CONVERGED = '{"stance":"converged"}';

// agents: { id: { plan, cliPlan, status } }. Each agent gets ACP + a resumable headless fake.
function setup(agents) {
  const dir = mkdtempSync(join(tmpdir(), "rt-run-"));
  const registry = {};
  for (const [id, a] of Object.entries(agents)) {
    const status = a.status ?? CONVERGED;
    const cli = ["node", FAKE_CLI, "--plan", a.cliPlan ?? "ok", "--state", join(dir, `${id}.cli.n`), "--log", join(dir, `${id}.cli.jsonl`), "--status", status];
    registry[id] = {
      label: id, transport: a.transport ?? "acp",
      acp: ["node", FAKE, "--name", id, "--plan", a.plan ?? "ok", "--state", join(dir, `${id}.n`), "--log", join(dir, `${id}.jsonl`), "--status", status],
      headless: { start: cli, resume: [...cli, "--resume", "{session}"], input: "stdin", output: "json" },
    };
  }
  writeFileSync(join(dir, "agents.json"), JSON.stringify(registry));
  writeFileSync(join(dir, "brief.md"), "Audit nothing in particular.");
  const target = join(dir, "target");
  mkdirSync(target);
  return { dir, target, runDir: join(dir, "run") };
}

function run({ dir, target, runDir }, ids, args = []) {
  const r = spawnSync("node", [RUNNER, "run", "--registry", join(dir, "agents.json"), "--brief", join(dir, "brief.md"),
    "--run-dir", runDir, "--cwd", target, "--agents", ids, "--no-veto", "--turn-timeout", "1", "--drain-timeout", "0.3",
    "--kill-grace", "0.3", "--wait-timeout", "1", ...args], { encoding: "utf8", timeout: 60_000 });
  const state = existsSync(join(runDir, "state.json")) ? JSON.parse(readFileSync(join(runDir, "state.json"), "utf8")) : null;
  return { ...r, state };
}
const prompts = (dir, file) => readFileSync(join(dir, file), "utf8").trim().split("\n").map((l) => JSON.parse(l));

test("healthy run reaches consensus and is not degraded", () => {
  const s = setup({ a: {}, b: {} });
  const r = run(s, "a,b");
  assert.equal(r.status, 0, r.stderr);
  assert.equal(r.state.result, "consensus");
  assert.match(r.state.stopReason, /^consensus/);
  assert.ok(r.state.turns.every((t) => t.stopReason === "end_turn"));
});

test("crash mid-turn → ACP restart with context rebuilt from rounds/", () => {
  const s = setup({ a: { plan: "ok,crash,ok" }, b: {} });
  const r = run(s, "a,b");
  assert.equal(r.status, 0, r.stderr);
  assert.equal(r.state.agents.a.failedTurns, 1);
  assert.equal(r.state.agents.a.transport, "acp");
  assert.equal(r.state.result, "consensus", "a restart on the same transport is not a degradation");
  const [, , retry] = prompts(s.dir, "a.jsonl");
  assert.notEqual(retry.pid, prompts(s.dir, "a.jsonl")[0].pid, "a new process");
  assert.match(retry.prompt, /Context restored/);
  assert.match(retry.prompt, /reply 0 from a/, "its own round-1 reply is replayed");
});

test("hang twice → headless → drop, result degraded", () => {
  const s = setup({ a: {}, b: {}, c: { plan: "hang", cliPlan: "hang" } });
  const r = run(s, "a,b,c");
  assert.equal(r.status, 0, r.stderr);
  const c = r.state.agents.c;
  assert.equal(c.failedTurns, 3);
  assert.equal(c.live, false);
  assert.deepEqual(r.state.degraded.map((d) => d.what), ["switched to headless", "dropped"]);
  assert.equal(r.state.result, "degraded");
  assert.match(r.state.stopReason, /degraded: c switched to headless, c dropped/);
  assert.deepEqual(r.state.turns.filter((t) => t.agent === "c").map((t) => t.transport), ["acp", "acp", "headless"]);
  assert.equal(prompts(s.dir, "c.cli.jsonl").length, 1);
});

test("non-end_turn stopReason is a failed turn", () => {
  const s = setup({ a: { plan: "cancelled,ok" }, b: {} });
  const r = run(s, "a,b");
  assert.equal(r.status, 0, r.stderr);
  const failed = r.state.turns.find((t) => t.agent === "a" && t.outcome === "failed");
  assert.equal(failed.stopReason, "cancelled");
  assert.equal(r.state.agents.a.failedTurns, 1);
});

test("auto mode: the same blocking set two rounds running → awaiting_moderator", () => {
  const open = '{"stance":"open","blocking":["A-1: still wrong"]}';
  const s = setup({ a: { status: open }, b: { status: open } });
  const r = run(s, "a,b", ["--rounds", "4"]);
  assert.equal(r.status, 0, r.stderr);
  assert.equal(r.state.stopReason, "moderator timeout");
  assert.deepEqual(r.state.deadlocks, [{ round: 2, blocking: ["A-1"] }]);
  assert.match(readFileSync(join(s.runDir, "events.log"), "utf8"), /deadlock: same blocking set A-1/);
});

test("a reused run dir is refused", () => {
  const s = setup({ a: {}, b: {} });
  assert.equal(run(s, "a,b").status, 0);
  const again = run(s, "a,b");
  assert.equal(again.status, 1);
  assert.match(again.stderr, /already used/);
});

test("edit detection: a further edit to an already dirty file is caught; run files are not", () => {
  const s = setup({ a: {}, b: {} });
  s.runDir = join(s.target, "docs", "run"); // run dir inside the target repo
  execFileSync("git", ["init", "-q"], { cwd: s.target });
  writeFileSync(join(s.target, "f.txt"), "one");
  execFileSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", "add", "."], { cwd: s.target });
  execFileSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"], { cwd: s.target });
  writeFileSync(join(s.target, "f.txt"), "two"); // dirty before the run starts
  const clean = run(s, "a,b");
  assert.equal(clean.status, 0, clean.stderr);
  assert.deepEqual(clean.state.warnings, [], "the run's own files never warn");

  // Agent a writes to the already dirty file during its first turn.
  const s2 = setup({ a: {}, b: {} });
  s2.target = s.target; s2.runDir = join(s.target, "docs", "run2");
  const reg = JSON.parse(readFileSync(join(s2.dir, "agents.json"), "utf8"));
  reg.a.acp.push("--touch", `${join(s.target, "f.txt")}=three`);
  writeFileSync(join(s2.dir, "agents.json"), JSON.stringify(reg));
  const touched = run(s2, "a,b");
  assert.equal(touched.status, 0, touched.stderr);
  assert.match(touched.state.warnings.join("\n"), /round 1: working tree content changed/);
});

test("veto: a slowly written synthesis is read whole, and every veto prompt lists all agents' final status", async () => {
  const s = setup({ a: {}, b: { status: '{"stance":"converged","blocking":[],"resolved":["A-1"]}' } });
  const { spawn } = await import("node:child_process");
  const p = spawn("node", [RUNNER, "run", "--registry", join(s.dir, "agents.json"), "--brief", join(s.dir, "brief.md"),
    "--run-dir", s.runDir, "--cwd", s.target, "--agents", "a,b", "--turn-timeout", "5", "--wait-timeout", "20"], { stdio: "ignore" });
  const exited = new Promise((r) => p.on("exit", r));
  const synth = join(s.runDir, "synthesis.md");
  for (let i = 0; i < 200; i++) {
    const st = existsSync(join(s.runDir, "state.json")) && JSON.parse(readFileSync(join(s.runDir, "state.json"), "utf8"));
    if (st?.status === "awaiting_synthesis") break;
    await new Promise((r) => setTimeout(r, 100));
  }
  const { appendFileSync } = await import("node:fs");
  appendFileSync(synth, "# Draft part one\n");
  await new Promise((r) => setTimeout(r, 200));
  appendFileSync(synth, "## Part two END\n");
  assert.equal(await exited, 0);
  const vetoPrompt = prompts(s.dir, "a.jsonl").at(-1).prompt;
  assert.match(vetoPrompt, /Part two END/, "the whole synthesis was read");
  assert.match(vetoPrompt, /### a \(A\)\nFinal-round status: \{"stance":"converged"/);
  assert.match(vetoPrompt, /### b \(B\)\nFinal-round status/);
  const state = JSON.parse(readFileSync(join(s.runDir, "state.json"), "utf8"));
  assert.deepEqual(state.veto.map((v) => [v.agent, v.approve, v.stopReason]), [["a", true, "end_turn"], ["b", true, "end_turn"]]);
});
