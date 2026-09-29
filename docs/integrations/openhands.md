# OpenHands Agent Canvas (optional)

OpenHands can run generated code and change files. It is not part of the default
stack. The overlay follows Agent Canvas 1.24.0, mounts only a project directory
and its own state volume, and does not mount the host Docker socket.

## Before you start

- Use a dedicated workspace with no `.env` files, SSH keys or unrelated repos.
- Keep it on localhost or a VPN.
- Generate a separate `OPENHANDS_BACKEND_API_KEY`. Never reuse GPUHarbor's
  control, RunPod, inference or runtime secrets.
- Recheck the pinned image when you upgrade, and on non-amd64 machines.
- Review changes by hand. Do not give it automatic deployment rights.

## Start

```bash
mkdir -p workspace
./scripts/install --openhands
```

Open `https://localhost:8445` (it redirects to `/canvas`). It sits behind the same
HTTPS proxy as the dashboard; see [TLS.md](../TLS.md) for trusting the
certificate. With `--no-https` it is `http://127.0.0.1:3001/canvas`. The UI may
ask for the backend key.

## Point it at GPUHarbor

In the model settings, add an OpenAI-compatible provider:

- Model: `openai/code` if the profile serves `code`, otherwise `openai/chat`
- Base URL: `http://controller:8080/v1`
- API key: the value of `MODEL_ACCESS_TOKEN`

Only the inference token goes into OpenHands. It cannot start, stop or delete
pods. Start the model in GPUHarbor first.

## Limits

Generated code still reads and writes everything under the projects directory and
has whatever network access the runtime gives it. For anything sensitive, run it
in its own VM and read the upstream self-hosting guide.
