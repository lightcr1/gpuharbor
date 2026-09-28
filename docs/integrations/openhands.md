# OpenHands Agent Canvas (optional)

OpenHands can execute generated code and modify files. It is deliberately absent
from the default GPUHarbor stack. The integration follows OpenHands Agent Canvas
1.24.0 and mounts only a dedicated projects directory plus its own state volume;
it does **not** mount the host Docker socket.

## Before enabling

- Use a dedicated workspace without `.env` files, SSH keys or unrelated repos.
- Keep Agent Canvas bound to localhost or a trusted VPN.
- Generate a separate `OPENHANDS_BACKEND_API_KEY`; never reuse GPUHarbor's
  control, RunPod, inference or runtime credentials.
- Recheck the pinned Agent Canvas image when upgrading or on non-amd64 systems.
- Commit/review agent changes manually; do not grant automatic deployment rights.

## Start

```bash
mkdir -p workspace
# Set OPENHANDS_BACKEND_API_KEY in .env first.
docker compose -f compose.yml -f compose.openhands.yml up -d --build
```

Open `http://127.0.0.1:3001/canvas` (or the root URL if redirected by the current
Agent Canvas release). The backend key may be requested by the UI.

## Configure GPUHarbor as the model provider

In the OpenHands model/LLM settings, add an OpenAI-compatible provider:

- Model: `openai/code` for a profile exposing `code`, or `openai/chat`
- Base URL: `http://controller:8080/v1`
- API key: the value of `MODEL_ACCESS_TOKEN`

Only the inference token is entered into OpenHands. It cannot start, stop or
delete pods. Start the desired model in GPUHarbor before running an agent task.
Model/provider settings are owned by OpenHands and may change between releases;
this is why GPUHarbor does not write undocumented OpenHands state files.

## Isolation limits

Removing the Docker socket is safer than the former integration, but generated
code still has read/write access to every repository under
`OPENHANDS_PROJECTS_PATH` and whatever network access the Agent Canvas runtime
provides. For sensitive work, run it in a dedicated VM and review upstream's
self-hosting security guide.
