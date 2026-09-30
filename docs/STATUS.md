# Status

Last checked: 2026-09-29.

## Working

- Controller with dashboard, login, CSRF tokens and a cost lock.
- Model catalog stored on disk: shipped profiles, your own profiles and overrides.
- RunPod lifecycle: create, start, stop, delete, plus duplicate-pod protection.
- Idle stop after `RUNPOD_IDLE_STOP_MINUTES` without model traffic.
- OpenAI-compatible endpoint for any client.
- HTTPS by default (local CA), with `install`, `doctor` and `trust-ca`.
- Open WebUI: verified with a running pod on a real GPU.
- OpenHands: the profile sync is tested against a real OpenHands container and a full Compose stack.
- Optional Open WebUI, OpenHands Agent Canvas and local HTTPS.
- PI coding agent: `./scripts/connect-pi`, also offered by `install` and `setup`.
- Published runtime images, so a fresh install does not build anything.
- 138 tests and a CI workflow on GitHub.
- Dashboard and docs available in English and German (`/docs` and `/docs/de`),
  the sidebar highlights the current section.
- Settings dialog with an opt-in update-notification toggle (off by default) and
  an update pill in the header.
- Helper scripts documented in `docs/SCRIPTS.md`.
- Runtime image status is visible read-only in the dashboard.
- The model editor can look a repository up on Hugging Face and propose runtime,
  context, volume, licence and GPUs.

## Runtime images

These are on GHCR, tagged `0.1.4` for linux/amd64. They are referenced by digest
in `.env.example`, so RunPod pulls them directly.

| Runtime | Image |
|---|---|
| vLLM | `ghcr.io/lightcr1/gpuharbor-runtime-vllm@sha256:47046f391746a94e442b238ad5b57d84d69c4854670858bed459e3cbc98254e4` |
| llama.cpp | `ghcr.io/lightcr1/gpuharbor-runtime-llama-cpp@sha256:83816656a93f6d6e959ce9c0e17352eb3c4d1fa665114eed6946453ce7b9e31e` |
| Bonsai | `ghcr.io/lightcr1/gpuharbor-runtime-bonsai@sha256:d1ad005bc0f3a213be68b199665de35c3ce7c0c66a8af7c9fcc858fc94725662` |

GHCR packages are private when first pushed. RunPod pulls without credentials, so
they were set to public in the web UI. Verify with:

```bash
docker logout ghcr.io
docker pull ghcr.io/lightcr1/gpuharbor-runtime-llama-cpp:0.1.4
```

To publish new images, build them on a machine with enough disk and run
`./scripts/publish-runtime-images --owner <owner> --tag <version>`. The vLLM base
image is about 20 GB, which is more than a free GitHub-hosted runner has, so image
builds are not part of CI.

## Not verified yet

- Only Qwen3.8 27B FP8 has run on a real GPU (NVIDIA A40, EU-SE-1). The other
  profiles have not.
- No measured VRAM, throughput or cost numbers.
- Tool calling has not been exercised end to end.

## Known limits

- RunPod GPU availability changes constantly. A profile can fail to place even
  when everything is configured correctly.
- GPU, datacenter and volume cannot be changed on a running pod. Delete and
  recreate it instead.
- A stopped pod still costs money for its volume.
- OpenHands runs generated code. Use a dedicated workspace.
