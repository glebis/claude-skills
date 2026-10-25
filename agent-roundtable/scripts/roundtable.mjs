#!/usr/bin/env node
// agent-roundtable runner: drives a multi-agent audit debate. Each agent runs over
// ACP or a headless CLI with native resume (see agents.mjs); a failing agent is
// recovered along a fixed ladder and the run is labelled degraded. The
// orchestrating Claude session acts as moderator through files in the run
// directory (see SKILL.md "Run directory").
//
//   node roundtable.mjs run --brief brief.md --agents codex,cmd --run-dir DIR [options]
//   node roundtable.mjs doctor [codex,cmd,...]

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync, renameSync, readdirSync, statSync, realpathSync } from "node:fs";
import { join, dirname, resolve, relative, isAbsolute } from "node:path";
import { parseArgs } from "node:util";
import { fileURLToPath } from "node:url";
import { AcpAgent, HeadlessAgent, killAllChildren } from "./agents.mjs";
import { openingPrompt, critiquePrompt, vetoPrompt, recoveryPrompt, parseStatus } from "./prompts.mjs";
import { assessConsensus, blockingIds, isDeadlock } from "./consensus.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
process.env.PATH = `${join(HERE, "node_modules", ".bin")}:${process.env.PATH}`;

const ROLES = ["auditor", "devils-advocate", "architect", "qa"];
const MAX_FAILED_TURNS = 3;

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
    transport: { type: "string", default: "auto" }, // auto (registry default) | acp | headless
    cwd: { type: "string", default: process.cwd() },
    "run-dir": { type: "string" },
    registry: { type: "string", default: join(HERE, "..", "agents.json") },
    "turn-timeout": { type: "string", default: "900" }, // seconds per agent turn
    "drain-timeout": { type: "string", default: "30" }, // seconds to drain a cancelled ACP turn
    "kill-grace": { type: "string", default: "5" }, // seconds between SIGTERM and SIGKILL
    "budget-min": { type: "string", default: "60" }, // wall clock for the debate rounds
    "wait-timeout": { type: "string", default: "3600" }, // seconds to wait for moderator files
    "no-veto": { type: "boolean", default: false },
  },
});

const REGISTRY = JSON.parse(readFileSync(opt.registry, "utf8"));
const agentOpts = (extra) => ({ drainMs: Number(opt["drain-timeout"]) * 1000, killGraceMs: Number(opt["kill-grace"]) * 1000, ...extra });

// ---------- small utilities ----------

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => new Date().toISOString();

// tmp file + rename, so a reader only ever sees a complete file under the final name.
function writeAtomic(path, data) {
  const tmp = `${path}.${process.pid}.tmp`;
  writeFileSync(tmp, data);
  renameSync(tmp, path);
}

// Waits for a moderator file and returns it once its size has stopped changing,
// as a second guard behind the atomic tmp + mv the moderator is asked to use.
async function waitForFile(path, timeoutMs) {
  const end = Date.now() + timeoutMs;
  while (Date.now() < end) {
    if (existsSync(path)) {
      const size = statSync(path).size;
      await sleep(500);
      if (existsSync(path) && statSync(path).size === size) return readFileSync(path, "utf8");
      continue;
    }
    await sleep(Math.min(2000, Math.max(100, end - Date.now())));
  }
  return null;
}

const git = (cwd, args) => execFileSync("git", args, { cwd, stdio: ["ignore", "pipe", "ignore"], maxBuffer: 1 << 30 });
const EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904";

// Content fingerprint of tracked and untracked (not gitignored) files, runDir excluded.
// A further edit to an already dirty file changes it, unlike `git status`.
function fingerprint(cwd, runDir) {
  let top;
  try { top = git(cwd, ["rev-parse", "--show-toplevel"]).toString().trim(); } catch { return null; } // not a git repo
  const rel = relative(realpathSync(top), realpathSync(runDir)); // git prints realpaths (/private/var on macOS)
  const exclude = rel && !rel.startsWith("..") && !isAbsolute(rel) ? [`:(exclude,top)${rel}`] : [];
  const h = createHash("sha256");
  let base = "HEAD";
  try { git(top, ["rev-parse", "--verify", "HEAD"]); } catch { base = EMPTY_TREE; }
  h.update(git(top, ["diff", "--binary", base, "--", ".", ...exclude]));
  const untracked = git(top, ["ls-files", "--others", "--exclude-standard", "-z", "--", ".", ...exclude]).toString().split("\0").filter(Boolean);
  for (const f of untracked.sort()) {
    h.update(`\0${f}\0`);
    try { h.update(readFileSync(join(top, f))); } catch { h.update("<unreadable>"); }
  }
  return h.digest("hex");
}

// ---------- agents ----------

function makeAgent(id, transport, ctx, carry = {}) {
  const cfg = REGISTRY[id];
  return transport === "acp"
    ? new AcpAgent(id, cfg, agentOpts(ctx))
    : new HeadlessAgent(id, cfg, agentOpts({ ...ctx, sessionId: carry.sessionId ?? null }));
}

async function startAgent(id, transport, ctx) {
  const a = makeAgent(id, transport, ctx);
  try {
    await a.start();
    return a;
  } catch (e) {
    await a.close?.();
    if (a.stderr) e.message += ` | stderr: ${a.stderr.slice(-300).trim()}`;
    throw e;
  }
}

function defaultTransport(id) {
  const cfg = REGISTRY[id];
  if (opt.transport !== "auto") return opt.transport;
  return cfg.transport ?? (cfg.acp ? "acp" : "headless");
}

// ---------- debate ----------

async function run() {
  if (!opt.brief || !opt["run-dir"]) throw new Error("run needs --brief and --run-dir");
  const runDir = resolve(opt["run-dir"]);
  const cwd = resolve(opt.cwd);
  for (const f of ["state.json", "moderator", "synthesis.md"]) {
    if (existsSync(join(runDir, f))) throw new Error(`${join(runDir, f)} exists: this run dir was already used; pick a new --run-dir`);
  }
  for (const d of ["rounds", "moderator", "veto"]) mkdirSync(join(runDir, d), { recursive: true });
  const logFile = join(runDir, "events.log");
  const log = (m) => { const line = `${now()} ${String(m).replace(/\s*\n\s*/g, " ⏎ ").slice(0, 400)}`; appendFileSync(logFile, line + "\n"); console.error(line); };

  const brief = readFileSync(opt.brief, "utf8");
  writeAtomic(join(runDir, "brief.md"), brief);
  const ids = opt.agents.split(",").map((s) => s.trim()).filter(Boolean);
  for (const id of ids) if (!REGISTRY[id] || id.startsWith("_")) throw new Error(`unknown agent "${id}" (known: ${Object.keys(REGISTRY).filter((k) => !k.startsWith("_")).join(", ")})`);
  if (opt.format === "roles" && !opt.roles) log(`warning: --format roles without --roles; using the default lenses ${ROLES.join(", ")}`);
  const roles = opt.roles ? opt.roles.split(",") : ROLES;
  const maxRounds = Number(opt.rounds);
  const turnMs = Number(opt["turn-timeout"]) * 1000;
  const waitMs = Number(opt["wait-timeout"]) * 1000;
  const deadline = Date.now() + Number(opt["budget-min"]) * 60_000;
  if (opt.format === "pingpong" && ids.length !== 2) throw new Error("pingpong needs exactly 2 agents");

  const state = {
    status: "starting", result: null, format: opt.format, mode: opt.mode, maxRounds, round: 0,
    agents: {}, degraded: [], turns: [], warnings: [], stopReason: null,
    editDetection: "content fingerprint of tracked and untracked files (git diff HEAD + untracked contents), run dir excluded; gitignored files are NOT covered",
  };
  const save = () => writeAtomic(join(runDir, "state.json"), JSON.stringify(state, null, 2));
  save();

  const agents = {};
  const ctx = { cwd, runDir, log };
  const markDegraded = (id, what) => { if (!state.degraded.some((d) => d.agent === id && d.what === what)) state.degraded.push({ agent: id, what }); };

  // Cleanup runs on every exit path: normal end, thrown error, SIGINT/SIGTERM.
  const closeAll = () => Promise.all(Object.values(agents).map((a) => a.close().catch(() => {}))).then(() => killAllChildren(Number(opt["kill-grace"]) * 1000));
  const onSignal = (sig) => async () => {
    log(`received ${sig}; closing agents`);
    state.status = "failed"; state.stopReason = `interrupted by ${sig}`; save();
    await closeAll();
    process.exit(130);
  };
  process.once("SIGINT", onSignal("SIGINT"));
  process.once("SIGTERM", onSignal("SIGTERM"));

  try {
    await Promise.all(ids.map(async (id, i) => {
      const role = opt.format === "roles" ? roles[i % roles.length] : null;
      const want = defaultTransport(id);
      state.agents[id] = { ok: false, live: true, transport: want, role, lastError: null, failedTurns: 0, nativeSessionId: null };
      try {
        agents[id] = await startAgent(id, want, ctx);
      } catch (e) {
        log(`${id} ${want} failed to start: ${e.message}`);
        state.agents[id].lastError = e.message;
        const other = want === "acp" ? "headless" : "acp";
        if (opt.transport !== "auto") { state.agents[id].live = false; return; }
        try {
          agents[id] = await startAgent(id, other, ctx);
          state.warnings.push(`${id}: ${want} failed at start, using ${other}`);
        } catch (e2) {
          log(`${id} ${other} failed to start: ${e2.message}`);
          state.agents[id] = { ...state.agents[id], live: false, lastError: `${e.message}; ${other}: ${e2.message}` };
          return;
        }
      }
      Object.assign(agents[id], { prefix: id.toUpperCase(), role });
      Object.assign(state.agents[id], { ok: true, transport: agents[id].transport });
      log(`${id} started over ${agents[id].transport}${agents[id].info ? ` (${agents[id].info.name ?? "?"} ${agents[id].info.version ?? ""})` : ""}`);
    }));
    const live = () => ids.filter((id) => agents[id] && state.agents[id].live);
    if (live().length < 2) { state.status = "failed"; state.result = "failed"; state.stopReason = "fewer than 2 agents available"; save(); throw new Error(state.stopReason); }
    save();

    const baseline = fingerprint(cwd, runDir);
    if (baseline === null) state.warnings.push("target is not a git repo; edit detection is off");
    const checkEdits = (when) => {
      if (baseline === null) return;
      if (fingerprint(cwd, runDir) !== baseline) {
        const w = `${when}: working tree content changed during the debate — an agent may have edited files`;
        if (!state.warnings.includes(w)) { state.warnings.push(w); log(w); }
      }
    };
    const latest = {}; // id -> { text, status, round }

    // Context for an agent whose transport lost its memory: its own completed replies.
    const withContext = (id, prompt) => {
      const a = agents[id];
      if (!a.needsContext || !latest[id]) return prompt;
      const ownReplies = readdirSync(join(runDir, "rounds"))
        .map((f) => f.match(new RegExp(`^r(\\d+)-${id}\\.md$`)))
        .filter(Boolean)
        .map((m) => ({ round: Number(m[1]), text: readFileSync(join(runDir, "rounds", m[0]), "utf8") }))
        .sort((x, y) => x.round - y.round);
      if (!ownReplies.length) return prompt;
      const opening = openingPrompt({ brief, prefix: a.prefix, role: a.role, format: opt.format });
      return recoveryPrompt({ opening, ownReplies, prompt });
    };

    // Recovery ladder over the whole run: 1st failed attempt restarts the same transport,
    // 2nd moves to headless with native resume, 3rd drops the agent.
    const recover = async (id) => {
      const h = state.agents[id];
      const old = agents[id];
      await old.close().catch(() => {});
      for (;;) {
        if (h.failedTurns >= MAX_FAILED_TURNS) {
          h.live = false; h.ok = false; markDegraded(id, "dropped");
          log(`${id} dropped after ${h.failedTurns} failed attempts`);
          return false;
        }
        const target = h.failedTurns === 1 ? old.transport : "headless";
        try {
          const a = await startAgent(id, target, { ...ctx, sessionId: old.sessionId });
          Object.assign(a, { prefix: old.prefix, role: old.role });
          agents[id] = a;
          if (target !== old.transport) markDegraded(id, `switched to ${target}`);
          h.transport = target;
          log(`${id} recovered over ${target} (failed attempts: ${h.failedTurns})`);
          return true;
        } catch (e) {
          h.failedTurns++; h.lastError = `restart over ${target}: ${e.message}`;
          log(`${id} ${h.lastError}`);
          save();
        }
      }
    };

    // One turn with the recovery ladder. Returns { text, stopReason } or null if the agent was dropped.
    const attempt = async (id, prompt, label) => {
      const h = state.agents[id];
      for (;;) {
        const a = agents[id];
        const started = Date.now();
        const record = { label, agent: id, transport: a.transport, startedAt: new Date(started).toISOString() };
        try {
          const r = await a.ask(withContext(id, prompt), turnMs);
          record.stopReason = r.stopReason;
          if (r.stopReason !== "end_turn") throw new Error(`turn stopped with ${r.stopReason}`);
          Object.assign(record, { outcome: "ok", ms: Date.now() - started });
          Object.assign(h, { ok: true, transport: a.transport, nativeSessionId: a.sessionId ?? h.nativeSessionId });
          state.turns.push(record); save();
          return r;
        } catch (e) {
          Object.assign(record, { outcome: "failed", error: e.message, ms: Date.now() - started });
          state.turns.push(record);
          h.failedTurns++; h.ok = false; h.lastError = e.message;
          if (latest[id]) latest[id].status = null; // the stale vote never counts
          log(`${id} ${label} failed (${h.failedTurns}/${MAX_FAILED_TURNS}): ${e.message}`);
          save();
          if (!(await recover(id))) { save(); return null; }
          save();
        }
      }
    };

    const turn = async (round, id, prompt) => {
      writeAtomic(join(runDir, "rounds", `r${round}-${id}.prompt.md`), prompt);
      const r = await attempt(id, prompt, `r${round}`);
      if (!r) return null;
      const status = parseStatus(r.text);
      latest[id] = { text: r.text, status, round };
      writeAtomic(join(runDir, "rounds", `r${round}-${id}.md`), r.text);
      if (!status.parsed) log(`${id} r${round}: invalid roundtable-status (${status.error})`);
      return { agent: id, ...status };
    };
    const peersOf = (id) => live().filter((p) => p !== id && latest[p])
      .map((p) => ({ label: REGISTRY[p].label, prefix: agents[p].prefix, text: latest[p].text }));

    // Moderator notes are consumed once each, in order, at the start of the next round.
    const consumed = new Set();
    const unreadNotes = () => {
      const files = readdirSync(join(runDir, "moderator"))
        .map((f) => f.match(/^r(\d+)\.md$/)).filter(Boolean)
        .sort((x, y) => Number(x[1]) - Number(y[1]))
        .map((m) => m[0]).filter((f) => !consumed.has(f));
      files.forEach((f) => consumed.add(f));
      return files.map((f) => readFileSync(join(runDir, "moderator", f), "utf8"));
    };
    const degradedNote = () => state.degraded.length ? ` (degraded: ${state.degraded.map((d) => `${d.agent} ${d.what}`).join(", ")})` : "";

    let prevBlocking = null;
    let verdict = null;
    let pendingWait = null; // note file the moderator must write before the next round
    for (let round = 1; round <= maxRounds; round++) {
      if (pendingWait) {
        state.status = "awaiting_moderator"; state.waitingFor = pendingWait.path; state.waitingReason = pendingWait.reason; save();
        log(`waiting for moderator note ${pendingWait.path} (${pendingWait.reason})`);
        const note = await waitForFile(pendingWait.path, waitMs);
        delete state.waitingFor; delete state.waitingReason;
        pendingWait = null;
        if (note === null) { state.stopReason = "moderator timeout"; break; }
      }
      const notes = unreadNotes();
      if (notes.some((n) => n.trim().split("\n")[0].trim().toUpperCase() === "STOP")) { state.stopReason = "moderator stopped"; break; }
      const moderatorNote = notes.length ? notes.join("\n\n") : null;

      if (Date.now() > deadline) { state.stopReason = "budget exhausted"; break; }
      if (live().length < 2) { state.stopReason = "fewer than 2 agents left"; break; }
      state.round = round; state.status = "debating"; save();
      log(`round ${round} start`);

      const speakers = opt.format === "pingpong" ? [live()[(round - 1) % live().length]] : live();
      // Peers are snapshotted before anyone speaks, so parallel speakers all see the previous round.
      const peerSnapshot = Object.fromEntries(speakers.map((id) => [id, peersOf(id)]));
      const results = await Promise.all(speakers.map((id) => {
        const a = agents[id];
        const parts = [];
        if (!latest[id]) parts.push(openingPrompt({ brief, prefix: a.prefix, role: a.role, format: opt.format }));
        if (peerSnapshot[id].length) parts.push(critiquePrompt({ round, peers: peerSnapshot[id], moderatorNote, prefix: a.prefix }));
        return turn(round, id, parts.join("\n\n"));
      }));
      checkEdits(`round ${round}`);

      // Consensus is judged on every live agent's most recent status, not just this round's speakers.
      const statuses = live().filter((id) => latest[id]?.status).map((id) => ({ agent: id, ...latest[id].status }));
      verdict = assessConsensus(statuses, { round, maxRounds, minRounds: Number(opt["min-rounds"]), expectedAgents: live() });
      if (verdict.converged && state.degraded.length) verdict = { ...verdict, reason: verdict.reason + degradedNote() };
      const blocking = blockingIds(statuses);
      writeAtomic(join(runDir, "rounds", `r${round}.summary.json`), JSON.stringify({ round, answered: results.filter(Boolean).length, statuses, blocking, verdict, degraded: state.degraded }, null, 2));
      log(`round ${round} consensus: ${verdict.converged} (${verdict.reason})`);
      if (verdict.converged) { state.stopReason = `consensus: ${verdict.reason}`; break; }
      if (round === maxRounds) { state.stopReason = "round limit"; break; }
      if (live().length < 2) { state.stopReason = "fewer than 2 agents left"; break; }

      const notePath = join(runDir, "moderator", `r${round}.md`);
      if (isDeadlock(prevBlocking, blocking)) {
        // Even in auto mode: a human-shaped call is needed to break it.
        state.deadlocks = [...(state.deadlocks ?? []), { round, blocking }];
        pendingWait = { path: notePath, reason: `deadlock: same blocking set ${blocking.join(", ")} two rounds running` };
      } else if (opt.mode === "active") {
        pendingWait = { path: notePath, reason: "active mode" };
      }
      prevBlocking = blocking;
    }
    delete state.waitingFor;
    log(`debate ended: ${state.stopReason}`);

    if (!opt["no-veto"] && live().length) {
      const synthPath = join(runDir, "synthesis.md");
      state.status = "awaiting_synthesis"; state.waitingFor = synthPath; save();
      log(`waiting for synthesis ${synthPath}`);
      const synthesis = await waitForFile(synthPath, waitMs);
      delete state.waitingFor;
      if (synthesis === null) {
        state.warnings.push("no synthesis written; veto round skipped");
      } else {
        state.status = "veto"; save();
        const panel = ids.filter((id) => agents[id]).map((id) => ({
          prefix: id.toUpperCase(), label: REGISTRY[id].label, status: latest[id]?.status ?? null, text: latest[id]?.text ?? null,
          state: !state.agents[id].live ? "dropped" : state.degraded.find((d) => d.agent === id)?.what ?? "live",
        }));
        const votes = await Promise.all(live().map(async (id) => {
          const r = await attempt(id, vetoPrompt({ synthesis, prefix: agents[id].prefix, panel }), "veto");
          if (!r) return { agent: id, approve: null, error: state.agents[id].lastError };
          writeAtomic(join(runDir, "veto", `${id}.md`), r.text);
          const s = parseStatus(r.text);
          // attempt() only returns end_turn turns, so an approval always has stopReason end_turn.
          return { agent: id, approve: s.parsed && s.stance === "converged" && s.blocking.length === 0, stopReason: r.stopReason, blocking: s.blocking, parsed: s.parsed, error: s.error };
        }));
        writeAtomic(join(runDir, "veto.json"), JSON.stringify(votes, null, 2));
        state.veto = votes;
        checkEdits("veto");
      }
    }

    state.result = state.degraded.length ? "degraded" : verdict?.converged ? "consensus" : "no_consensus";
    state.status = "done"; save();
    log(`done: ${state.result}${degradedNote()}`);
  } catch (e) {
    if (state.status !== "failed") { state.status = "failed"; state.result = "failed"; state.stopReason ??= e.message; save(); }
    throw e;
  } finally {
    await closeAll();
  }
}

// ---------- doctor ----------

// Starts each agent over its default transport and sends a one-line prompt, so
// expired keys and failed logins show up here instead of in round 1.
async function doctor() {
  const ids = positionals[1] ? positionals[1].split(",") : Object.keys(REGISTRY).filter((k) => !k.startsWith("_"));
  const ctx = { cwd: process.cwd(), runDir: null, log: () => {} };
  const pingMs = 90_000;
  const rows = await Promise.all(ids.map(async (id) => {
    const cfg = REGISTRY[id];
    if (!cfg) return { agent: id, lines: ["unknown agent"] };
    const want = defaultTransport(id);
    const lines = [];
    for (const t of ["acp", "headless"]) {
      const tag = `${t}${t === want ? " (default)" : ""}`;
      if (t === "acp" && !cfg.acp) { lines.push(`${tag}: not configured`); continue; }
      if (t === "headless" && !cfg.headless) { lines.push(`${tag}: not configured (no native resume)`); continue; }
      let a;
      try {
        a = await startAgent(id, t, ctx);
        if (t !== want) { lines.push(`${tag}: starts${t === "headless" ? " (binary found)" : ""}`); continue; }
        const r = await a.ask("Reply with the single word PONG and nothing else.", pingMs);
        const ok = r.stopReason === "end_turn" && /PONG/i.test(r.text);
        lines.push(`${tag}: ${ok ? "ok" : "FAIL"} — replied ${JSON.stringify(r.text.trim().slice(0, 40))}, stopReason ${r.stopReason}${a.info ? ` (${a.info.name ?? "?"} ${a.info.version ?? ""})` : ""}`);
      } catch (e) {
        lines.push(`${tag}: FAIL: ${e.message.replace(/\s+/g, " ").slice(0, 160)}`);
      } finally {
        await a?.close().catch(() => {});
      }
    }
    return { agent: id, lines };
  }));
  for (const r of rows) console.log(r.lines.map((l, i) => `${(i ? "" : r.agent).padEnd(9)} ${l}`).join("\n"));
  await killAllChildren(1000);
}

const cmd = positionals[0];
const main = cmd === "doctor" ? doctor : cmd === "run" ? run : null;
if (!main) {
  console.error("usage: roundtable.mjs run --brief FILE --run-dir DIR [--agents a,b] [--format panel|pingpong|roles] [--mode auto|active] ...\n       roundtable.mjs doctor [a,b]");
  process.exit(2);
}
main().then(() => process.exit(0), (e) => { console.error(e.stack ?? e); process.exit(1); });
