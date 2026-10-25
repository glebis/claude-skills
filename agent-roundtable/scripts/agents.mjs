// Transports for one debating agent. Both expose the same surface:
//   await agent.start()
//   await agent.ask(prompt, timeoutMs) -> { text, stopReason }   (throws on any failure)
//   agent.needsContext   true when the next turn must carry the rebuilt debate context
//   await agent.close()  waits for the process to exit, SIGKILL after the grace period
//
// AcpAgent keeps one live ACP session. HeadlessAgent runs the CLI once per turn and
// continues the same native CLI session by id (`codex exec resume`, `--resume`).

import { spawn, execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync, mkdtempSync, realpathSync } from "node:fs";
import { join, resolve, relative, isAbsolute, dirname } from "node:path";
import { tmpdir } from "node:os";
import { Readable, Writable } from "node:stream";
import * as acp from "@agentclientprotocol/sdk";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export class TurnTimeout extends Error {}

// Rejects after ms; clear() stops the timer so it never holds the event loop open.
function deadline(ms, label) {
  let t;
  const promise = new Promise((_, rej) => (t = setTimeout(() => rej(new TurnTimeout(`${label} timed out after ${ms / 1000}s`)), ms)));
  promise.catch(() => {});
  return { promise, clear: () => clearTimeout(t) };
}

// ---------- child processes ----------

// Every child the runner starts, so the SIGINT/SIGTERM handlers can reap them.
const children = new Set();

// Spawned in its own process group so close() also reaches grandchildren
// (agent CLIs start their own tool subprocesses).
export function spawnTracked(cmd, args, opts = {}) {
  const proc = spawn(cmd, args, { ...opts, detached: true });
  proc.exited = new Promise((r) => proc.once("exit", (code, signal) => r({ code, signal })));
  proc.spawned = new Promise((res, rej) => { proc.once("spawn", res); proc.once("error", rej); });
  proc.spawned.catch(() => {});
  children.add(proc);
  proc.exited.then(() => children.delete(proc));
  return proc;
}

const hasExited = (proc) => proc.exitCode !== null || proc.signalCode !== null;

function signalGroup(proc, sig) {
  try { process.kill(-proc.pid, sig); } catch { try { proc.kill(sig); } catch {} }
}

// SIGTERM the group, wait up to graceMs, then SIGKILL. Resolves once the leader is gone.
export async function killTree(proc, graceMs = 5000) {
  if (!proc?.pid) return;
  if (!hasExited(proc)) {
    signalGroup(proc, "SIGTERM");
    const gone = await Promise.race([proc.exited.then(() => true), sleep(graceMs).then(() => false)]);
    if (!gone) {
      signalGroup(proc, "SIGKILL");
      await Promise.race([proc.exited, sleep(2000)]);
    }
  }
  signalGroup(proc, "SIGKILL"); // stragglers left in the group after the leader exited
}

export async function killAllChildren(graceMs = 5000) {
  await Promise.all([...children].map((p) => killTree(p, graceMs)));
}

// ---------- prompt delivery ----------

// Single pass with a function replacer: a value is inserted verbatim even when it
// contains `$&`, `$$` or another placeholder. The prompt itself never goes into argv.
export function substitute(argv, vals) {
  return argv.map((a) => a.replace(/\{(out|cwd|session|promptFile)\}/g, (m, k) => (vals[k] ?? m)));
}

// ---------- permission policy (best effort, decided by path) ----------

const TOOL_KINDS = new Set(["read", "edit", "delete", "move", "search", "execute", "think", "fetch", "switch_mode", "other"]);
const FREE_KINDS = new Set(["read", "search", "fetch", "think", "execute"]);
const WRITE_KINDS = new Set(["edit", "delete", "move", "other"]);

// realpath of the longest existing prefix, so /tmp and /private/tmp compare equal
// and a not-yet-created file still resolves through its parent's symlinks.
function canonical(p) {
  let head = resolve(p);
  const tail = [];
  for (;;) {
    try { return join(realpathSync(head), ...tail); } catch {}
    const up = dirname(head);
    if (up === head) return resolve(p);
    tail.unshift(head.slice(up.length).replace(/^[/\\]/, ""));
    head = up;
  }
}

export function isInside(path, dir) {
  const rel = relative(canonical(dir), canonical(path));
  return rel === "" || (!rel.startsWith("..") && !isAbsolute(rel));
}

// Returns { allow, reason }. Never looks at the tool's title.
export function decidePermission(toolCall, { cwd, runDir }) {
  const kind = toolCall?.kind;
  if (!kind || !TOOL_KINDS.has(kind)) return { allow: false, reason: `kind ${JSON.stringify(kind ?? null)} unknown` };
  if (FREE_KINDS.has(kind)) return { allow: true, reason: kind };
  if (!WRITE_KINDS.has(kind)) return { allow: false, reason: `kind ${kind} not allowed` };
  const paths = (toolCall.locations ?? []).map((l) => (isAbsolute(l.path) ? l.path : resolve(cwd, l.path)));
  if (!paths.length && kind !== "other") return { allow: false, reason: `${kind} without locations` };
  const inside = paths.find((p) => isInside(p, cwd) || (runDir && isInside(p, runDir)));
  if (inside) return { allow: false, reason: `${kind} inside the target or run dir: ${inside}` };
  return { allow: true, reason: paths.length ? `${kind} outside the target: ${paths.join(", ")}` : kind };
}

// ---------- ACP ----------

const AUTH_REQUIRED = -32000; // ACP error code for "authentication required"

export class AcpAgent {
  constructor(id, cfg, { cwd, runDir, log = () => {}, drainMs = 30_000, killGraceMs = 5000 }) {
    Object.assign(this, { id, cfg, cwd, runDir, log, drainMs, killGraceMs, transport: "acp", needsContext: true });
  }

  async start() {
    const [cmd, ...args] = this.cfg.acp;
    this.proc = spawnTracked(cmd, args, { cwd: this.cwd, stdio: ["pipe", "pipe", "pipe"] });
    this.stderr = "";
    this.proc.stderr.on("data", (d) => (this.stderr = (this.stderr + d).slice(-4000)));
    this.died = this.proc.exited.then(({ code, signal }) => {
      throw new Error(`${this.id} agent exited (code ${code}, signal ${signal})${this.stderr ? ` | stderr: ${this.stderr.slice(-300).trim()}` : ""}`);
    });
    this.died.catch(() => {});
    await this.proc.spawned;

    const stream = acp.ndJsonStream(Writable.toWeb(this.proc.stdin), Readable.toWeb(this.proc.stdout));
    this.conn = acp
      .client({ name: "agent-roundtable" })
      .onNotification(acp.methods.client.session.update, () => {}) // routed to ActiveSession
      .onRequest(acp.methods.client.session.requestPermission, async ({ params }) => this.permission(params))
      .connect(stream);
    const ctx = this.conn.agent;

    const init = await this.bounded(ctx.request(acp.methods.agent.initialize, { protocolVersion: 1, clientCapabilities: {} }), 60_000, "initialize");
    this.info = init.agentInfo;
    try {
      this.session = await this.bounded(ctx.buildSession(this.cwd).start(), 120_000, "session/new");
    } catch (e) {
      // Authenticate only on the protocol's auth error and an advertised method, never on message text.
      const offered = (init.authMethods ?? []).some((m) => m.id === this.cfg.authMethod);
      if (e?.code !== AUTH_REQUIRED || !offered) throw e;
      await this.bounded(ctx.request(acp.methods.agent.authenticate, { methodId: this.cfg.authMethod }), 120_000, "authenticate");
      this.session = await this.bounded(ctx.buildSession(this.cwd).start(), 120_000, "session/new");
    }
  }

  bounded(promise, ms, label) {
    const t = deadline(ms, `${this.id} ${label}`);
    return Promise.race([promise, t.promise, this.died]).finally(t.clear);
  }

  permission(params) {
    const { allow, reason } = decidePermission(params.toolCall, { cwd: this.cwd, runDir: this.runDir });
    const option = params.options.find((o) => o.kind === (allow ? "allow_once" : "reject_once"))
      ?? params.options.find((o) => o.kind.startsWith(allow ? "allow" : "reject"));
    this.log(`${this.id} permission ${params.toolCall?.kind ?? "?"} "${params.toolCall?.title ?? ""}" -> ${allow ? "allow" : "reject"} (${reason})`);
    return option ? { outcome: { outcome: "selected", optionId: option.optionId } } : { outcome: { outcome: "cancelled" } };
  }

  // One reader per session: the reader started here is the only consumer of the
  // session's update queue until it sees this turn's `stop`. On timeout the turn is
  // cancelled and the same reader drains to `stop`; if that takes longer than
  // drainMs the session is discarded and the agent killed, so a late update can
  // never land in a later turn.
  async ask(prompt, timeoutMs) {
    if (this.discarded) throw new Error(`${this.id} session was discarded after an undrained turn`);
    const session = this.session;
    let text = "";
    session.prompt(prompt).catch(() => {}); // the same rejection reaches the reader
    const reader = (async () => {
      for (;;) {
        const msg = await session.nextUpdate();
        if (msg.kind === "stop") return { text, stopReason: msg.stopReason };
        const u = msg.update;
        if (u.sessionUpdate === "agent_message_chunk" && u.content?.type === "text") text += u.content.text;
        else if (u.sessionUpdate === "tool_call") this.log(`${this.id} tool ${u.kind ?? ""} ${u.title ?? ""}`);
      }
    })();
    reader.catch(() => {});

    const t = deadline(timeoutMs, `${this.id} turn`);
    try {
      const out = await Promise.race([reader, t.promise, this.died]);
      this.needsContext = false;
      return out;
    } catch (e) {
      if (e instanceof TurnTimeout) await this.drain(reader);
      else this.discarded = true; // crash or rejected prompt: the ladder replaces this agent
      throw e;
    } finally {
      t.clear();
    }
  }

  async drain(reader) {
    await this.conn.agent.notify(acp.methods.agent.session.cancel, { sessionId: this.session.sessionId }).catch(() => {});
    const drained = await Promise.race([
      reader.then(() => true, () => true),
      this.died.then(() => false, () => false),
      sleep(this.drainMs).then(() => false),
    ]);
    if (drained) { this.log(`${this.id} cancelled turn drained`); return; }
    this.discarded = true;
    this.log(`${this.id} cancelled turn did not stop within ${this.drainMs / 1000}s; discarding the session`);
    await this.close();
  }

  async close() {
    try { this.session?.dispose(); } catch {}
    try { this.conn?.close(); } catch {}
    await killTree(this.proc, this.killGraceMs);
  }
}

// ---------- headless with native resume ----------

// Pulls { text, sessionId, stopReason } out of the CLI's output.
//   codex-jsonl: `codex exec --json`; the id is thread.started.thread_id, the text is the -o file.
//   json:        one JSON object per line (claude --output-format json, cmd NDJSON);
//                the last line with a result/finalText field wins.
export function parseHeadlessOutput(format, stdout, outFile) {
  const objects = stdout.split("\n").map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter((o) => o && typeof o === "object");
  if (format === "codex-jsonl") {
    const started = objects.find((o) => o.type === "thread.started" && o.thread_id);
    const text = outFile && existsSync(outFile) ? readFileSync(outFile, "utf8") : "";
    const failed = objects.find((o) => o.type === "turn.failed" || o.type === "error");
    if (failed) throw new Error(`turn failed: ${JSON.stringify(failed).slice(0, 300)}`);
    return { text, sessionId: started?.thread_id ?? null, stopReason: "end_turn" };
  }
  if (format === "json") {
    const result = [...objects].reverse().find((o) => typeof (o.finalText ?? o.result) === "string");
    if (!result) throw new Error(`no result in output: ${stdout.slice(-300)}`);
    if (result.is_error) throw new Error(`agent reported an error: ${String(result.result).slice(0, 300)}`);
    const stop = result.stopReason ?? result.stop_reason ?? "end_turn";
    return { text: result.finalText ?? result.result, sessionId: result.sessionId ?? result.session_id ?? null, stopReason: stop };
  }
  return { text: stdout, sessionId: null, stopReason: "end_turn" };
}

export class HeadlessAgent {
  constructor(id, cfg, { cwd, log = () => {}, sessionId = null, killGraceMs = 5000 }) {
    Object.assign(this, { id, cfg, cwd, log, sessionId, killGraceMs, transport: "headless" });
    this.h = cfg.headless;
  }

  // A fresh CLI session has no memory of the debate; the runner rebuilds it.
  get needsContext() { return !this.sessionId; }

  async start() {
    if (!this.h?.start) throw new Error(`${this.id} has no headless adapter`);
    if (!this.h.resume) throw new Error(`${this.id} headless has no native resume`);
    execFileSync("/bin/sh", ["-c", 'command -v "$0"', this.h.start[0]], { stdio: "ignore" }); // throws if missing
  }

  async ask(prompt, timeoutMs) {
    const dir = mkdtempSync(join(tmpdir(), "roundtable-"));
    const out = join(dir, "last.md");
    const promptFile = join(dir, "prompt.md");
    if (this.h.input === "file") writeFileSync(promptFile, prompt);
    const template = this.sessionId ? this.h.resume : this.h.start;
    const argv = substitute(template, { out, cwd: this.cwd, session: this.sessionId ?? "", promptFile });

    const p = spawnTracked(argv[0], argv.slice(1), { cwd: this.cwd, stdio: ["pipe", "pipe", "pipe"] });
    this.proc = p;
    let stdout = "", stderr = "";
    p.stdout.on("data", (d) => (stdout += d));
    p.stderr.on("data", (d) => (stderr = (stderr + d).slice(-4000)));
    p.stdin.on("error", () => {});
    p.stdin.end(this.h.input === "file" ? "" : prompt);

    const t = deadline(timeoutMs, `${this.id} headless turn`);
    let exit;
    try {
      exit = await Promise.race([p.exited, t.promise, p.spawned.then(() => new Promise(() => {}))]);
    } catch (e) {
      await killTree(p, this.killGraceMs);
      throw e;
    } finally {
      t.clear();
    }
    if (exit.code !== 0) throw new Error(`${this.id} exited ${exit.code ?? exit.signal}: ${stderr.slice(-500).trim()}`);
    const r = parseHeadlessOutput(this.h.output, stdout, out);
    if (r.sessionId && r.sessionId !== this.sessionId) {
      if (this.sessionId) this.log(`${this.id} native session changed ${this.sessionId} -> ${r.sessionId}`);
      this.sessionId = r.sessionId;
    }
    if (!this.sessionId) throw new Error(`${this.id} output has no native session id; cannot resume`);
    return { text: r.text, stopReason: r.stopReason };
  }

  async close() {
    await killTree(this.proc, this.killGraceMs);
  }
}
