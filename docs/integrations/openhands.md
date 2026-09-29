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

Nothing to do: GPUHarbor connects OpenHands to your models by itself. The controller
writes one LLM profile per model (`gpuharbor-<id>`) through OpenHands' settings API and
activates the one for the running model. It sets sensible values for local models:
native tool calls only where the vLLM profile enables them, a fitting output length, a
long timeout for cold starts, and no hosted-provider options. Profiles you create
yourself are never changed, and if you activate one, GPUHarbor leaves your choice alone.
It keeps the profiles in sync when you add, edit or delete a model. The dashboard
header links to OpenHands and *Connect an app* shows the status.

Only if you want to do it by hand:

In the model settings, add an OpenAI-compatible provider:

- Model: `openai/` plus a served name of the profile, for example `openai/default`
- Base URL: `http://controller:8080/v1`
- API key: the value of `MODEL_ACCESS_TOKEN`

Only the inference token goes into OpenHands. It cannot start, stop or delete
pods. Start the model in GPUHarbor first.

## Limits

Generated code still reads and writes everything under the projects directory and
has whatever network access the runtime gives it. For anything sensitive, run it
in its own VM and read the upstream self-hosting guide.
