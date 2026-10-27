import { Agent } from "@earendil-works/pi-agent-core";
import { createModels, type CredentialStore } from "@earendil-works/pi-ai";
import { openrouterProvider } from "@earendil-works/pi-ai/providers/openrouter";

export async function runPiAgent(prompt: string, apiKey: string, modelId: string) {
  if (!apiKey) throw new Error("OPENROUTER_API_KEY must be configured as a Worker secret");
  const credentials: CredentialStore = {
    read: async provider => provider === "openrouter" ? { type: "api_key", key: apiKey } : undefined,
    modify: async (_provider, fn) => fn(undefined),
    delete: async () => {},
    list: async () => [{ providerId: "openrouter", type: "api_key" }],
  };
  const models = createModels({ credentials });
  models.setProvider(openrouterProvider());
  const model = models.getModel("openrouter", modelId);
  if (!model || !modelId.startsWith("deepseek/")) throw new Error("Configure a supported DeepSeek catalog model");
  const agent = new Agent({
    initialState: {
      systemPrompt: "You are a concise Pi assistant running inside a Cloudflare Workflow. You have no external research, filesystem or shell tools. Do not claim tool actions you did not perform.",
      model,
      thinkingLevel: "off",
      messages: [],
      tools: [],
    },
    streamFn: (selected, context, options) => models.streamSimple(selected, context, {
      ...options,
      maxTokens: 2048,
      signal: options?.signal ? AbortSignal.any([options.signal, AbortSignal.timeout(150000)]) : AbortSignal.timeout(150000),
    }),
  });
  try {
    await agent.prompt(prompt);
    const last = agent.state.messages[agent.state.messages.length - 1];
    if (!last || last.role !== "assistant" || last.stopReason === "error" || last.stopReason === "aborted") {
      throw new Error("Pi model request failed; check model access, credits and the Worker secret");
    }
    const text = last.content.filter(part => part.type === "text").map(part => part.text).join("").trim();
    if (!text) throw new Error("Pi returned no assistant text");
    return { engine: "pi-agent-core", provider: "openrouter", model: modelId, text };
  } finally {
    agent.abort();
  }
}
