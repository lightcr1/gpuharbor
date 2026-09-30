// Installed by ./scripts/connect-pi --with-modelinfo. Remove it with ./scripts/connect-pi --remove.
// Adds /modelinfo: which model GPUHarbor is running right now. It only works while a
// GPUHarbor model is selected in PI; with any other model it says so and does nothing.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const PROVIDER = "gpuharbor";

export default function (pi: ExtensionAPI) {
	pi.registerCommand("modelinfo", {
		description: "Show which model GPUHarbor is running (GPUHarbor models only)",
		handler: async (_args, ctx) => {
			const model = ctx.model;
			if (!model || model.provider !== PROVIDER) {
				ctx.ui.notify("/modelinfo only works while a GPUHarbor model is selected.", "warning");
				return;
			}
			const auth = await ctx.modelRegistry.getApiKeyAndHeaders(model);
			if (!auth.ok) {
				ctx.ui.notify(`Cannot read the GPUHarbor token: ${auth.error}`, "error");
				return;
			}
			const base = (model.baseUrl || "").replace(/\/v1\/?$/, "");
			try {
				const response = await fetch(`${base}/api/running-model`, {
					headers: { Authorization: `Bearer ${auth.apiKey ?? ""}` },
					signal: AbortSignal.timeout(10_000),
				});
				if (!response.ok) {
					ctx.ui.notify(`GPUHarbor answered HTTP ${response.status}.`, "error");
					return;
				}
				const info = await response.json();
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
				if (!info.served_names.includes(model.id)) {
					lines.push(`Note: PI has "${model.id}" selected, which the running model does not serve. Pick "${info.served_names[0]}" with /model.`);
				}
				ctx.ui.notify(lines.join("\n"), info.served_names.includes(model.id) ? "info" : "warning");
			} catch (error) {
				ctx.ui.notify(`Cannot reach GPUHarbor at ${base}: ${(error as Error).message}`, "error");
			}
		},
	});
}
