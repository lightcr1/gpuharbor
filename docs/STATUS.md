# Status

Last checked: 2026-09-29.

## Working

- Controller with dashboard, login, CSRF tokens and a cost lock.
- Model catalog stored on disk: shipped profiles, your own profiles and overrides.
- RunPod lifecycle: create, start, stop, delete, plus duplicate-pod protection.
- Idle stop after `RUNPOD_IDLE_STOP_MINUTES` without model traffic.
- OpenAI-compatible endpoint for any client.
- Optional Open WebUI, OpenHands Agent Canvas and local HTTPS.
- Published runtime images, so a fresh install does not build anything.
- 98 tests and a CI workflow on GitHub.
- Dashboard and docs available in English and German (`/docs` and `/docs/de`),
  the sidebar highlights the current section.
- Settings dialog with an opt-in update-notification toggle (off by default) and
  an update pill in the header.
- Helper scripts documented in `docs/SCRIPTS.md`.
- Runtime image status is visible read-only in the dashboard.
- The model editor can look a repository up on Hugging Face and propose runtime,
  context, volume, licence and GPUs.

## Runtime images

These are on GHCR, tagged `0.1.0` for linux/amd64. They are referenced by digest
in `.env.example`, so RunPod pulls them directly.

| Runtime | Image |
|---|---|
| vLLM | `ghcr.io/lightcr1/gpuharbor-runtime-vllm@sha256:a35d491bf6f4fc535cda18a85947b112300225b2ecc039b83d8311117082816f` |
| llama.cpp | `ghcr.io/lightcr1/gpuharbor-runtime-llama-cpp@sha256:6367ffb83e9e4b4981df883ba988840a8ca4ab91518b6ee16bbe211eb9e1596a` |
| Bonsai | `ghcr.io/lightcr1/gpuharbor-runtime-bonsai@sha256:a83dc25c8a5ca4e6926d36bf6e2796fa8879a5b979c51083bdea1eeb46427fe1` |

GHCR packages are private when first pushed. RunPod pulls without credentials, so
they were set to public in the web UI. Verify with:

```bash
docker logout ghcr.io
docker pull ghcr.io/lightcr1/gpuharbor-runtime-llama-cpp:0.1.0
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
