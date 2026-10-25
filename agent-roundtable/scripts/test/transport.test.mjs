// npm test (from scripts/). Drives the real ACP SDK against test/fake-agent.mjs.
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { AcpAgent, HeadlessAgent, TurnTimeout, killTree, spawnTracked, substitute, decidePermission } from "../agents.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FAKE = join(HERE, "fake-agent.mjs");
const FAKE_CLI = join(HERE, "fake-cli.mjs");
const tmp = () => mkdtempSync(join(tmpdir(), "rt-test-"));
const lines = (f) => (existsSync(f) ? readFileSync(f, "utf8").trim().split("\n").filter(Boolean).map((l) => JSON.parse(l)) : []);

async function fakeAcp(plan, extra = {}) {
  const dir = tmp();
  const log = join(dir, "log.jsonl");
  const a = new AcpAgent("fake", { acp: ["node", FAKE, "--plan", plan, "--state", join(dir, "n"), "--log", log] },
    { cwd: dir, runDir: join(dir, "run"), drainMs: 1000, killGraceMs: 500, ...extra });
  await a.start();
  return { a, log, dir };
}

test("timeout + late update: the late text never reaches the next turn", async () => {
  const { a } = await fakeAcp("late,ok");
  try {
    await assert.rejects(a.ask("turn 1", 150), TurnTimeout);
    assert.equal(a.discarded, undefined, "the cancelled turn drained, so the session stays usable");
    const r = await a.ask("turn 2", 5000);
    assert.equal(r.stopReason, "end_turn");
    assert.doesNotMatch(r.text, /LATE-TEXT/);
    assert.match(r.text, /reply 1/);
  } finally { await a.close(); }
});

test("cancel ignored: the session is discarded and never prompted again", async () => {
  const { a, log } = await fakeAcp("hang,ok", { drainMs: 300 });
  await assert.rejects(a.ask("turn 1", 150), TurnTimeout);
  assert.equal(a.discarded, true);
  assert.notEqual(a.proc.exitCode ?? a.proc.signalCode, null, "the agent process was killed");
  await assert.rejects(a.ask("turn 2", 1000), /discarded/);
  assert.equal(lines(log).length, 1, "no second prompt was sent to the unsettled session");
});

test("crash mid-turn fails the turn fast instead of waiting for the timeout", async () => {
  const { a } = await fakeAcp("crash");
  const t0 = Date.now();
  await assert.rejects(a.ask("turn 1", 20_000), /exited|closed/i);
  assert.ok(Date.now() - t0 < 5000);
  await a.close();
});

test("a rejected prompt keeps its original error", async () => {
  const { a } = await fakeAcp("reject");
  try { await assert.rejects(a.ask("turn 1", 5000), /FAKE-REJECT-42/); } finally { await a.close(); }
});

test("stopReason is reported, not swallowed", async () => {
  const { a } = await fakeAcp("cancelled");
  try { assert.equal((await a.ask("turn 1", 5000)).stopReason, "cancelled"); } finally { await a.close(); }
});

test("close() kills a child that ignores SIGTERM after the grace period", async () => {
  const p = spawnTracked("node", ["-e", "process.on('SIGTERM',()=>{}); setInterval(()=>{},1000); console.log('up')"], { stdio: ["ignore", "pipe", "ignore"] });
  await new Promise((r) => p.stdout.once("data", r));
  const t0 = Date.now();
  await killTree(p, 300);
  assert.equal(p.signalCode, "SIGKILL");
  assert.ok(Date.now() - t0 >= 300);
});

test("AcpAgent.close() escalates to SIGKILL too", async () => {
  const dir = tmp();
  const a = new AcpAgent("fake", { acp: ["node", FAKE, "--ignore-sigterm"] }, { cwd: dir, killGraceMs: 300 });
  await a.start();
  await a.close();
  assert.equal(a.proc.signalCode, "SIGKILL");
});

test("a prompt with $$ $& {out} reaches the CLI unchanged; resume uses the native id", async () => {
  const dir = tmp();
  const log = join(dir, "cli.jsonl");
  const cfg = { headless: {
    start: ["node", FAKE_CLI, "--log", log, "--out", "{out}"],
    resume: ["node", FAKE_CLI, "--log", log, "--resume", "{session}"],
    input: "stdin", output: "json",
  } };
  const h = new HeadlessAgent("fake", cfg, { cwd: dir });
  await h.start();
  const prompt = "cost $$ and $& and {out} and {cwd} and `$(rm -rf x)`";
  await h.ask(prompt, 5000);
  await h.ask("second", 5000);
  const [first, second] = lines(log);
  assert.equal(first.prompt, prompt);
  assert.ok(!first.argv.some((x) => x.includes("$&")), "the prompt is not in argv");
  assert.equal(second.resume, "fake-native-1");
});

test("substitute is single-pass: values are inserted verbatim", () => {
  assert.deepEqual(substitute(["-C", "{cwd}", "-o", "{out}"], { cwd: "/a/$&/{out}", out: "/o/$$" }), ["-C", "/a/$&/{out}", "-o", "/o/$$"]);
});

test("permission policy decides by path", () => {
  const cwd = tmp();
  const runDir = tmp();
  const at = (kind, ...paths) => decidePermission({ kind, locations: paths.map((path) => ({ path })) }, { cwd, runDir }).allow;
  assert.equal(at("edit", "/tmp/scratch.md"), true, "writes outside cwd and runDir are allowed");
  assert.equal(at("edit", join(cwd, "src/a.js")), false, "in-target edit denied");
  assert.equal(at("edit", "src/a.js"), false, "relative paths resolve against cwd");
  assert.equal(at("delete", join(runDir, "state.json")), false, "run dir is protected");
  assert.equal(at("read", join(cwd, "src/a.js")), true, "in-target read allowed");
  assert.equal(at("execute"), true);
  assert.equal(at("edit"), false, "edit without locations denied");
  assert.equal(at("move", "/tmp/x", join(cwd, "y")), false, "any in-target location denies");
  assert.equal(at("other", join(cwd, "x")), false);
  assert.equal(at("switch_mode"), false);
  assert.equal(decidePermission({ title: "read file" }, { cwd, runDir }).allow, false, "missing kind denied, title ignored");
  assert.equal(decidePermission({ kind: "write" }, { cwd, runDir }).allow, false, "kind outside the enum denied");
});
