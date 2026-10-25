#!/usr/bin/env node
// agent-roundtable runner: drives a multi-agent audit debate over ACP, falling
// back to headless CLI calls per agent. The orchestrating Claude session acts as
// moderator through files in the run directory (see SKILL.md "Run directory").
//
//   node roundtable.mjs run --brief brief.md --agents codex,cmd --run-dir DIR [options]
//   node roundtable.mjs doctor [--agents codex,cmd,...]

import { spawn, execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync, mkdtempSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { tmpdir } from "node:os";
import { Readable, Writable } from "node:stream";
import { parseArgs } from "node:util";
import { fileURLToPath } from "node:url";
import * as acp from "@agentclientprotocol/sdk";
import { openingPrompt, critiquePrompt, vetoPrompt, parseStatus } from "./prompts.mjs";
import { assessConsensus } from "./consensus.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REGISTRY = JSON.parse(readFileSync(join(HERE, "..", "agents.json"), "utf8"));
process.env.PATH = `${join(HERE, "node_modules", ".bin")}:${process.env.PATH}`;

const FORBIDDEN_TOOL_KINDS = new Set(["edit", "delete", "move"]);
const ROLES = ["auditor", "devils-advocate", "architect", "qa"];

const { positionals, values: opt } = parseArgs({
  allowPositionals: true,
  options: {
    brief: { type: "string" },
    agents: { type: "string", default: "codex,cmd" },
    format: { type: "string", default: "panel" }, // panel | pingpong | roles
    roles: { type: "string" }, // comma list aligned with --agents, for format=roles
    rounds: { type: "string", default: "3" },
    "min-rounds": { type: "string", default: "2" },
    mode: { type: "string", default: "auto" }, // auto | active
    transport: { type: "string", default: "auto" }, // auto | acp | headless
    cwd: { type: "string", default: process.cwd() },
    "run-dir": { type: "string" },
    "turn-timeout": { type: "string", default: "900" }, // seconds per agent turn
    "budget-min": { type: "string", default: "60" }, // wall clock for the debate rounds
    "wait-timeout": { type: "string", default: "3600" }, // seconds to wait for moderator files
    "no-veto": { type: "boolean", default: false },
  },
});

// ---------- small utilities ----------

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => new Date().toISOString();

function withTimeout(promise, ms, label) {
  let t;
  return Promise.race([
    promise.finally(() => clearTimeout(t)),
    new Promise((_, rej) => (t = setTimeout(() => rej(new Error(`${label} timed out after ${ms / 1000}s`)), ms))),
  ]);
}

async function waitForFile(path, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (existsSync(path)) {
      await sleep(500); // let the writer finish
      return readFileSync(path, "utf8");
    }
    await sleep(2000);
  }
  return null;
}

function gitStatus(cwd) {
  try {
    return execFileSync("git", ["status", "--porcelain", "--untracked-files=all"], { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  } catch {
    return null; // not a git repo; the edit guard is skipped
  }
}

// ---------- agents ----------

class AcpAgent {
  constructor(id, cfg, cwd, log) {
    Object.assign(this, { id, cfg, cwd, log, transport: "acp" });
  }

  async start() {
    const [cmd, ...args] = this.cfg.acp;
    this.proc = spawn(cmd, args, { cwd: this.cwd, stdio: ["pipe", "pipe", "pipe"] });
    this.stderr = "";
    this.proc.stderr.on("data", (d) => (this.stderr = (this.stderr + d).slice(-4000)));
    const spawned = new Promise((res, rej) => {
      this.proc.once("spawn", res);
      this.proc.once("error", rej);
    });
    await spawned;

    const stream = acp.ndJsonStream(Writable.toWeb(this.proc.stdin), Readable.toWeb(this.proc.stdout));
    this.conn = acp
      .client({ name: "agent-roundtable" })
      .onNotification(acp.methods.client.session.update, () => {}) // routed to ActiveSession
      .onRequest(acp.methods.client.session.requestPermission, async ({ params }) => this.decidePermission(params))
      .connect(stream);
    const ctx = this.conn.agent;

    const init = await withTimeout(
      ctx.request(acp.methods.agent.initialize, { protocolVersion: 1, clientCapabilities: {} }),
      60_000,
      `${this.id} initialize`,
    );
    this.info = init.agentInfo;
    try {
      this.session = await withTimeout(ctx.buildSession(this.cwd).start(), 120_000, `${this.id} session/new`);
    } catch (e) {
      if (!this.cfg.authMethod || !/auth/i.test(e.message)) throw e;
      await withTimeout(ctx.request(acp.methods.agent.authenticate, { methodId: this.cfg.authMethod }), 120_000, `${this.id} authenticate`);
      this.session = await withTimeout(ctx.buildSession(this.cwd).start(), 120_000, `${this.id} session/new`);
    }
  }

  decidePermission(params) {
    const kind = params.toolCall?.kind ?? "other";
    const allow = !FORBIDDEN_TOOL_KINDS.has(kind);
    const option = params.options.find((o) => o.kind === (allow ? "allow_once" : "reject_once"))
      ?? params.options.find((o) => o.kind.startsWith(allow ? "allow" : "reject"));
    this.log(`${this.id} permission ${kind} "${params.toolCall?.title ?? ""}" -> ${allow ? "allow" : "reject"}`);
    return option ? { outcome: { outcome: "selected", optionId: option.optionId } } : { outcome: { outcome: "cancelled" } };
  }

  async ask(prompt, timeoutMs) {
    const done = this.session.prompt(prompt);
    done.catch(() => {}); // surfaced through the update loop
    const collect = (async () => {
      let text = "";
      for (;;) {
        const msg = await this.session.nextUpdate();
        if (msg.kind === "stop") return { text, stopReason: msg.stopReason };
        const u = msg.update;
        if (u.sessionUpdate === "agent_message_chunk" && u.content?.type === "text") text += u.content.text;
        else if (u.sessionUpdate === "tool_call") this.log(`${this.id} tool ${u.kind ?? ""} ${u.title ?? ""}`);
      }
    })();
    try {
      return await withTimeout(collect, timeoutMs, `${this.id} turn`);
    } catch (e) {
      await this.conn.agent.notify(acp.methods.agent.session.cancel, { sessionId: this.session.sessionId }).catch(() => {});
      throw e;
    }
  }

  close() {
    try { this.conn?.close(); } catch {}
    this.proc?.kill();
  }
}

class HeadlessAgent {
  // Stateless CLI: every turn resends the whole conversation so far.
  constructor(id, cfg, cwd, log) {
    Object.assign(this, { id, cfg, cwd, log, transport: "headless", history: [] });
  }

  async start() {
    const bin = this.cfg.headless[0];
    execFileSync("/bin/sh", ["-c", `command -v ${bin}`], { stdio: "ignore" }); // throws if missing
  }

  async ask(prompt, timeoutMs) {
    const full = this.history.length
      ? `${this.history.map((h) => `## Earlier turn\n### Prompt\n${h.prompt}\n### Your reply\n${h.reply}`).join("\n\n")}\n\n## Current turn\n${prompt}`
      : prompt;
    const out = join(mkdtempSync(join(tmpdir(), "roundtable-")), "last.md");
    const argv = this.cfg.headless.map((a) => a.replace("{prompt}", full).replace("{out}", out).replace("{cwd}", this.cwd));
    const text = await new Promise((res, rej) => {
      const p = spawn(argv[0], argv.slice(1), { cwd: this.cwd, stdio: ["pipe", "pipe", "pipe"] });
      let stdout = "", stderr = "";
      const t = setTimeout(() => { p.kill(); rej(new Error(`${this.id} headless turn timed out`)); }, timeoutMs);
      p.stdout.on("data", (d) => (stdout += d));
      p.stderr.on("data", (d) => (stderr = (stderr + d).slice(-4000)));
      p.on("error", rej);
      p.on("close", (code) => {
        clearTimeout(t);
        if (code !== 0) return rej(new Error(`${this.id} exited ${code}: ${stderr.slice(-500)}`));
        res(this.cfg.outputFile && existsSync(out) ? readFileSync(out, "utf8") : stdout);
      });
      if (this.cfg.stdin) p.stdin.end(full);
      else p.stdin.end();
    });
    this.history.push({ prompt, reply: text });
    return { text, stopReason: "end_turn" };
  }

  close() {}
}

async function startAgent(id, cwd, transport, log) {
  const cfg = REGISTRY[id];
  if (!cfg) throw new Error(`unknown agent "${id}" (known: ${Object.keys(REGISTRY).filter((k) => !k.startsWith("_")).join(", ")})`);
  if (transport !== "headless") {
    const a = new AcpAgent(id, cfg, cwd, log);
    try {
      await a.start();
      log(`${id} connected over ACP (${a.info?.name ?? "?"} ${a.info?.version ?? ""})`);
      return a;
    } catch (e) {
      a.close();
      log(`${id} ACP failed: ${e.message}${a.stderr ? ` | stderr: ${a.stderr.slice(-300).trim()}` : ""}`);
      if (transport === "acp") throw e;
    }
  }
  const h = new HeadlessAgent(id, cfg, cwd, log);
  await h.start();
  log(`${id} using headless fallback`);
  return h;
}

// ---------- debate ----------

async function run() {
  if (!opt.brief || !opt["run-dir"]) throw new Error("run needs --brief and --run-dir");
  const runDir = resolve(opt["run-dir"]);
  const cwd = resolve(opt.cwd);
  for (const d of ["rounds", "moderator", "veto"]) mkdirSync(join(runDir, d), { recursive: true });
  const logFile = join(runDir, "events.log");
  const log = (m) => { const line = `${now()} ${String(m).replace(/\s*\n\s*/g, " ⏎ ").slice(0, 400)}`; appendFileSync(logFile, line + "\n"); console.error(line); };

  const brief = readFileSync(opt.brief, "utf8");
  writeFileSync(join(runDir, "brief.md"), brief);
  const ids = opt.agents.split(",").map((s) => s.trim()).filter(Boolean);
  const roles = opt.roles ? opt.roles.split(",") : ROLES;
  const maxRounds = Number(opt.rounds);
  const turnMs = Number(opt["turn-timeout"]) * 1000;
  const waitMs = Number(opt["wait-timeout"]) * 1000;
  const deadline = Date.now() + Number(opt["budget-min"]) * 60_000;
  if (opt.format === "pingpong" && ids.length !== 2) throw new Error("pingpong needs exactly 2 agents");

  const state = { status: "starting", format: opt.format, mode: opt.mode, maxRounds, round: 0, agents: {}, warnings: [], stopReason: null };
  const save = () => writeFileSync(join(runDir, "state.json"), JSON.stringify(state, null, 2));
  save();

  const agents = {};
  await Promise.all(ids.map(async (id, i) => {
    try {
      agents[id] = await startAgent(id, cwd, opt.transport, log);
      agents[id].prefix = id.toUpperCase();
      agents[id].role = opt.format === "roles" ? roles[i % roles.length] : null;
      state.agents[id] = { transport: agents[id].transport, role: agents[id].role, ok: true };
    } catch (e) {
      state.agents[id] = { ok: false, error: e.message };
      log(`${id} unavailable: ${e.message}`);
    }
  }));
  const live = ids.filter((id) => agents[id]);
  if (live.length < 2) { state.status = "failed"; state.stopReason = "fewer than 2 agents available"; save(); throw new Error(state.stopReason); }
  save();

  const baseline = gitStatus(cwd);
  const latest = {}; // id -> { text, status }

  const turn = async (round, id, prompt) => {
    const a = agents[id];
    writeFileSync(join(runDir, "rounds", `r${round}-${id}.prompt.md`), prompt);
    try {
      const { text } = await a.ask(prompt, turnMs);
      const status = parseStatus(text);
      latest[id] = { text, status };
      writeFileSync(join(runDir, "rounds", `r${round}-${id}.md`), text);
      if (!status.parsed) log(`${id} r${round}: invalid roundtable-status (${status.error})`);
      return { agent: id, ...status };
    } catch (e) {
      // Keep the old text so peers can still answer it, but drop the stale vote.
      if (latest[id]) latest[id].status = null;
      log(`${id} r${round} failed: ${e.message}`);
      return null;
    }
  };
  const peersOf = (id) => live.filter((p) => p !== id && latest[p])
    .map((p) => ({ label: REGISTRY[p].label, prefix: agents[p].prefix, text: latest[p].text }));

  let moderatorNote = null;
  for (let round = 1; round <= maxRounds; round++) {
    if (Date.now() > deadline) { state.stopReason = "budget exhausted"; break; }
    state.round = round; state.status = "debating"; save();
    log(`round ${round} start`);

    let speakers;
    if (opt.format === "pingpong") speakers = [live[(round - 1) % 2]];
    else speakers = live;

    // Peers are snapshotted before anyone speaks, so parallel speakers all see the previous round.
    const peerSnapshot = Object.fromEntries(speakers.map((id) => [id, peersOf(id)]));
    const results = await Promise.all(speakers.map((id) => {
      const a = agents[id];
      const parts = [];
      if (!latest[id]) parts.push(openingPrompt({ brief, prefix: a.prefix, role: a.role, format: opt.format }));
      if (peerSnapshot[id].length) parts.push(critiquePrompt({ round, peers: peerSnapshot[id], moderatorNote, prefix: a.prefix }));
      return turn(round, id, parts.join("\n\n"));
    }));

    const after = gitStatus(cwd);
    if (baseline !== null && after !== baseline) {
      const w = `round ${round}: working tree changed during the debate — an agent may have edited files`;
      state.warnings.push(w); log(w);
    }

    // Consensus is judged on every agent's most recent status, not just this round's speakers.
    const statuses = live.filter((id) => latest[id]?.status).map((id) => ({ agent: id, ...latest[id].status }));
    const verdict = assessConsensus(statuses, { round, maxRounds, minRounds: Number(opt["min-rounds"]), expectedAgents: live });
    writeFileSync(join(runDir, "rounds", `r${round}.summary.json`), JSON.stringify({ round, answered: results.filter(Boolean).length, statuses, verdict }, null, 2));
    log(`round ${round} consensus: ${verdict.converged} (${verdict.reason})`);
    if (verdict.converged) { state.stopReason = `consensus: ${verdict.reason}`; break; }
    if (round === maxRounds) { state.stopReason = "round limit"; break; }

    const notePath = join(runDir, "moderator", `r${round}.md`);
    if (opt.mode === "active") {
      state.status = "awaiting_moderator"; state.waitingFor = notePath; save();
      log(`waiting for moderator note ${notePath}`);
      moderatorNote = await waitForFile(notePath, waitMs);
      if (moderatorNote === null) { state.stopReason = "moderator timeout"; break; }
    } else {
      moderatorNote = existsSync(notePath) ? readFileSync(notePath, "utf8") : null;
    }
    if (moderatorNote?.trim().split("\n")[0].trim().toUpperCase() === "STOP") { state.stopReason = "moderator stopped"; break; }
  }
  delete state.waitingFor;
  log(`debate ended: ${state.stopReason}`);

  if (!opt["no-veto"]) {
    const synthPath = join(runDir, "synthesis.md");
    state.status = "awaiting_synthesis"; state.waitingFor = synthPath; save();
    log(`waiting for synthesis ${synthPath}`);
    const synthesis = await waitForFile(synthPath, waitMs);
    delete state.waitingFor;
    if (synthesis === null) {
      state.warnings.push("no synthesis written; veto round skipped");
    } else {
      state.status = "veto"; save();
      const votes = await Promise.all(live.map(async (id) => {
        try {
          const { text } = await agents[id].ask(vetoPrompt({ synthesis, prefix: agents[id].prefix }), turnMs);
          writeFileSync(join(runDir, "veto", `${id}.md`), text);
          const s = parseStatus(text);
          return { agent: id, approve: s.parsed && s.stance === "converged" && s.blocking.length === 0, blocking: s.blocking, parsed: s.parsed, error: s.error };
        } catch (e) {
          log(`${id} veto failed: ${e.message}`);
          return { agent: id, approve: null, error: e.message };
        }
      }));
      writeFileSync(join(runDir, "veto.json"), JSON.stringify(votes, null, 2));
      state.veto = votes;
    }
  }

  state.status = "done"; save();
  live.forEach((id) => agents[id].close());
  log("done");
}

// ---------- doctor ----------

async function doctor() {
  // `doctor` checks every registered agent; `doctor codex,cmd` checks a subset.
  const ids = positionals[1] ? positionals[1].split(",") : Object.keys(REGISTRY).filter((k) => !k.startsWith("_"));
  const log = () => {};
  const rows = await Promise.all(ids.map(async (id) => {
    const row = { agent: id, acp: "-", headless: "-" };
    const a = new AcpAgent(id, REGISTRY[id], process.cwd(), log);
    try { await a.start(); row.acp = `ok (${a.info?.name ?? "?"} ${a.info?.version ?? ""})`.trim(); }
    catch (e) { row.acp = `FAIL: ${e.message.slice(0, 120)}`; }
    finally { a.close(); }
    try { await new HeadlessAgent(id, REGISTRY[id], process.cwd(), log).start(); row.headless = "binary found"; }
    catch { row.headless = "binary missing"; }
    return row;
  }));
  for (const r of rows) console.log(`${r.agent.padEnd(9)} acp: ${r.acp}\n${"".padEnd(9)} headless: ${r.headless}`);
}

const cmd = positionals[0];
const main = cmd === "doctor" ? doctor : cmd === "run" ? run : null;
if (!main) {
  console.error("usage: roundtable.mjs run --brief FILE --run-dir DIR [--agents a,b] [--format panel|pingpong|roles] [--mode auto|active] ...\n       roundtable.mjs doctor");
  process.exit(2);
}
main().then(() => process.exit(0), (e) => { console.error(e.stack ?? e); process.exit(1); });
