import { WorkflowEntrypoint, type WorkflowEvent, type WorkflowStep } from "cloudflare:workers";
import { runPiAgent } from "./pi-agent";

type Params = { prompt: string };
type Env = { OPENROUTER_API_KEY: string; PI_MODEL: string; AGENT_WORKFLOW: Workflow<Params> };

export class BackgroundAgentWorkflow extends WorkflowEntrypoint<Env, Params> {
  async run(event: WorkflowEvent<Params>, step: WorkflowStep) {
    const prompt = await step.do("validate-input", async () => {
      const value = event.payload?.prompt;
      if (typeof value !== "string" || !value.trim() || value.length > 12000) {
        throw new Error("prompt must contain 1–12000 characters");
      }
      return value;
    });
    return await step.do("pi-agent", { retries: { limit: 0, delay: "1 second" }, timeout: "3 minutes" }, async () => {
      return await runPiAgent(prompt, this.env.OPENROUTER_API_KEY, this.env.PI_MODEL);
    });
  }
}

// Invoke through authenticated Cloudflare Workflows APIs. No public agent endpoint.
export default { fetch: () => new Response("Use the authenticated Workflows API", { status: 404 }) };
