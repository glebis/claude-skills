#!/usr/bin/env node
// Fake ACP agent for the integration tests. Behaviour per prompt comes from
// --plan (comma list, consumed in order across restarts via --state):
//   ok        reply with --status (a roundtable-status JSON body) and end_turn
//   late      after 400 ms send "LATE-TEXT", then stop (cancelled if a cancel came in)
//   hang      never answer and ignore cancel
//   crash     send a chunk, then exit mid-turn
//   reject    fail the prompt request with FAKE-REJECT-42
//   cancelled answer at once with stopReason "cancelled"
// --touch FILE=CONTENT writes a file during the first prompt.
// Every prompt is appended to --log as one JSON line.
import { appendFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { Readable, Writable } from "node:stream";
import { parseArgs } from "node:util";
import * as acp from "@agentclientprotocol/sdk";

const { values: o } = parseArgs({ options: {
  plan: { type: "string", default: "ok" }, state: { type: "string" }, log: { type: "string" },
  status: { type: "string", default: '{"stance":"converged"}' }, name: { type: "string", default: "fake" },
  "ignore-sigterm": { type: "boolean", default: false },
  touch: { type: "string" }, // FILE=CONTENT written during the first prompt, to trip edit detection
} });
if (o["ignore-sigterm"]) process.on("SIGTERM", () => {});
const plan = o.plan.split(",");
const nextStep = () => {
  const n = o.state && existsSync(o.state) ? Number(readFileSync(o.state, "utf8")) : 0;
  if (o.state) writeFileSync(o.state, String(n + 1));
  return { n, step: plan[Math.min(n, plan.length - 1)] };
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let cancelled = false;

const chunk = (client, sessionId, text) => client.notify(acp.methods.client.session.update, {
  sessionId, update: { sessionUpdate: "agent_message_chunk", content: { type: "text", text } },
});

acp.agent({ name: o.name })
  .onRequest(acp.methods.agent.initialize, () => ({ protocolVersion: 1, agentCapabilities: {}, agentInfo: { name: o.name, version: "0.0.0" }, authMethods: [] }))
  .onRequest(acp.methods.agent.session.new, () => ({ sessionId: `sess-${process.pid}` }))
  .onNotification(acp.methods.agent.session.cancel, () => { cancelled = true; })
  .onRequest(acp.methods.agent.session.prompt, async ({ params, client }) => {
    cancelled = false;
    const prompt = params.prompt.map((b) => b.text ?? "").join("");
    const { n, step } = nextStep();
    if (o.log) appendFileSync(o.log, JSON.stringify({ pid: process.pid, n, step, prompt }) + "\n");
    const sid = params.sessionId;
    if (o.touch && n === 0) { const i = o.touch.indexOf("="); writeFileSync(o.touch.slice(0, i), o.touch.slice(i + 1)); }
    switch (step) {
      case "ok":
        await chunk(client, sid, `reply ${n} from ${o.name}\n`);
        await chunk(client, sid, "```roundtable-status\n" + o.status + "\n```\n");
        return { stopReason: "end_turn" };
      case "late":
        await sleep(400);
        await chunk(client, sid, "LATE-TEXT");
        return { stopReason: cancelled ? "cancelled" : "end_turn" };
      case "hang":
        return new Promise(() => {});
      case "crash":
        await chunk(client, sid, "partial");
        await sleep(50);
        process.exit(3);
      case "reject":
        throw new acp.RequestError(-32603, "FAKE-REJECT-42");
      case "cancelled":
        return { stopReason: "cancelled" };
    }
    throw new Error(`unknown plan step ${step}`);
  })
  .connect(acp.ndJsonStream(Writable.toWeb(process.stdout), Readable.toWeb(process.stdin)));
