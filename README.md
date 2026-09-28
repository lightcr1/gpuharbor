# GPUHarbor

**A self-hosted control plane for curated AI models on RunPod.**

GPUHarbor starts, stops and configures a single GPU pod, exposes its model through
an authenticated OpenAI-compatible API, and makes model/runtime choices visible
in a compact web dashboard. Open WebUI and OpenHands are optional integrations,
not mandatory parts of the stack.

> Early local prototype. Not yet published. GPUHarbor is an independent community
> project and is not affiliated with or endorsed by RunPod.

## License

The open core is licensed under **Apache-2.0** (`LICENSE`). Planned Pro features
such as multi-provider management, teams and cost automation are a separate,
proprietary component and are not part of this repository. See
[docs/LICENSING.md](docs/LICENSING.md) for the open-core boundary and its
trade-offs.

## Why GPUHarbor?

- Change models, context size, parallelism, GPU, region and volume in the UI.
- Add, export and import custom model profiles without editing Python code.
- Receive new built-ins on upgrades without overwriting custom models or overrides.
- Use curated vLLM, llama.cpp/GGUF and experimental Bonsai runtime presets.
- Preview the exact redacted pod request before spending money.
- Keep billable actions hard-disabled until explicitly enabled.
- Connect any OpenAI-compatible client through one stable endpoint.
- Add Open WebUI, OpenHands, both, or neither.

## Bundled model profiles

| Profile | Runtime | Intended use | Status |
|---|---|---|---|
| Qwen3.8 27B FP8 | vLLM | balanced default | not GPU-verified |
| Qwen3 Coder 30B FP8 | vLLM | coding and agents | not GPU-verified |
| HauhauCS 35B Aggressive Q6 | llama.cpp | chat and coding | experimental |
| Ternary Bonsai 2 27B PTQ1_0 | Bonsai fork | chat and coding | experimental |

The repositories, requested files and model-card licenses were checked against
the public upstream APIs; GPU execution is still unverified. See
[model management](docs/MODELS.md) and [third-party inventory](docs/THIRD_PARTY.md).

## Local, non-billable start

```bash
cp .env.example .env
# Replace every secret. Keep RUNPOD_ALLOW_BILLABLE_ACTIONS=false.
docker compose up --build -d
```

Open `http://127.0.0.1:8080`. You can edit profiles and inspect plans without
creating a pod. A live start remains blocked while the billable-action switch is
false or runtime images are not configured as immutable digests.

## Optional integrations

```bash
# Open WebUI
docker compose -f compose.yml -f compose.openwebui.yml up -d --build

# OpenHands (privileged; read the security guide first)
docker compose -f compose.yml -f compose.openhands.yml up -d --build

# Both
docker compose -f compose.yml -f compose.openwebui.yml -f compose.openhands.yml up -d --build
```

Read the [Open WebUI](docs/integrations/open-webui.md),
[OpenHands](docs/integrations/openhands.md), [TLS](docs/TLS.md) and
[security](docs/SECURITY.md) and [safe-upgrade](docs/UPGRADES.md) guides first.
The exact local validation state is recorded in [CURRENT_STATUS.md](docs/CURRENT_STATUS.md).

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest
```

No Git remote is configured in the local prototype. The publication guard blocks
commits and pushes Monday-Friday from 07:00 through 17:59 in `Europe/Zurich`.
After Git is initialized, enable the versioned hooks with:

```bash
git config core.hooksPath .githooks
```

The guard does not rewrite or fake timestamps.
