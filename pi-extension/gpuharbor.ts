// Installed by ./scripts/connect-pi. Remove it with ./scripts/connect-pi --remove.
// Lists the models GPUHarbor is running right now as the provider "gpuharbor" and adds /modelinfo.
// Settings come from gpuharbor.json next to this extension's agent folder (url, apiKey).
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const PROVIDER = "gpuharbor";
const agentDir = process.env.PI_CODING_AGENT_DIR || join(homedir(), ".pi", "agent");

type Settings = { url: string; apiKey: string };

function settings(): Settings | undefined {
	try {
		const value = JSON.parse(readFileSync(join(agentDir, "gpuharbor.json"), "utf8"));
		return typeof value.url === "string" && typeof value.apiKey === "string" ? value : undefined;
	} catch {
		return undefined;
	}
}

function token(apiKey: string): string {
	// Same syntax as models.json: a literal, or a leading !command.
	return apiKey.startsWith("!") ? execFileSync("sh", ["-c", apiKey.slice(1)], { encoding: "utf8" }).trim() : apiKey;
}

async function running(config: Settings, signal?: AbortSignal): Promise<any> {
	const response = await fetch(`${config.url}/api/running-model`, {
		headers: { Authorization: `Bearer ${token(config.apiKey)}` },
		signal: signal ?? AbortSignal.timeout(10_000),
	});
	if (!response.ok) throw new Error(`GPUHarbor answered HTTP ${response.status}`);
	return response.json();
}

const withCost = (models: any[]) => models.map((model) => ({ ...model, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 } }));

export default async function (pi: ExtensionAPI) {
	const config = settings();
	if (!config) return;

	const models = async (signal?: AbortSignal) => withCost((await running(config, signal)).pi_models ?? []);
	let initial: any[] = [];
	try {
		initial = await models();
	} catch {
		// GPUHarbor is not reachable yet; the list is filled on the next refresh.
	}
	pi.registerProvider(PROVIDER, {
		name: "GPUHarbor",
		baseUrl: `${config.url}/v1`,
		apiKey: config.apiKey,
		api: "openai-completions",
		...(initial.length ? { models: initial } : {}),
		refreshModels: async (context) => models(context.signal),
	} as any);

	pi.registerCommand("modelinfo", {
		description: "Show which model GPUHarbor is running (GPUHarbor models only)",
		handler: async (_args, ctx) => {
			const model = ctx.model;
			if (!model || model.provider !== PROVIDER) {
				ctx.ui.notify("/modelinfo only works while a GPUHarbor model is selected.", "warning");
				return;
			}
			try {
				const info = await running(config);
				if (!info.running) {
					ctx.ui.notify("No model is running. Start one in the GPUHarbor dashboard.", "warning");
					return;
				}
				const lines = [
					`Running: ${info.name} (${info.model_id})`,
					`Runtime: ${info.runtime}, context ${info.context_length} tokens`,
					`Names: ${info.served_names.join(", ")}`,
				];
				if (info.gpu) lines.push(`GPU: ${info.gpu}`);
				if (info.tool_calls === false) lines.push("Tool calls are not enabled for this profile.");
				const match = info.served_names.includes(model.id);
				if (!match) lines.push(`Note: PI has "${model.id}" selected, which the running model does not serve. Pick "${info.served_names[0]}" with /model.`);
				ctx.ui.notify(lines.join("\n"), match ? "info" : "warning");
			} catch (error) {
				ctx.ui.notify(`Cannot reach GPUHarbor at ${config.url}: ${(error as Error).message}`, "error");
			}
		},
	});
}
