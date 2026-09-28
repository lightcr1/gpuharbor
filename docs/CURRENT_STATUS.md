# Current status

Checked on 2026-09-28. GPUHarbor is published at
<https://github.com/lightcr1/gpuharbor> (public, Apache-2.0, branch `main`).
Runtime images are published to GHCR; no GPU pod has been started yet.

## Published images

- `ghcr.io/lightcr1/gpuharbor-runtime-vllm@sha256:a35d491b…`
- `ghcr.io/lightcr1/gpuharbor-runtime-llama-cpp@sha256:6367ffb8…`
- `ghcr.io/lightcr1/gpuharbor-runtime-bonsai@sha256:a83dc25c…`

The digests are wired into `.env.example`, so a fresh install can start a pod
without building images. Full digests: [RELEASE_ARTIFACTS.md](RELEASE_ARTIFACTS.md).

## Verified without RunPod cost

- 50 unit/API/security/registry/runtime/installer tests pass.
- Controller image builds from exact Python dependency locks.
- vLLM, llama.cpp and experimental Bonsai runtime images build locally.
- Runtime gateway options reject unsupported argument injection.
- Controller, Open WebUI v0.11.4 and OpenHands Agent Canvas 1.24.0 start
  together and their local HTTP interfaces respond.
- TLS overlay passes certificate verification and security-header checks.
- Persistent custom model catalog survives controller restart and creates an
  atomic backup.
- Built-in update/override/reset/orphan/legacy-migration behavior is tested.
- All Compose combinations and dashboard JavaScript syntax validate.
- Controller and runtime Python locks report no known vulnerabilities through
  `pip-audit` at the check date.
- Secret-pattern scan is clean and no stale former-name references remain.
- All four bundled Hugging Face repositories and requested GGUF files exist;
  public metadata reports Apache-2.0 and no gating.

## Licensing

- Open core: Apache-2.0 (`LICENSE`), with the open-core boundary described in
  `docs/LICENSING.md`.
- Pro: separate proprietary component, not present in this repository.
- Remaining owner gate: trademark policy, Contributor License Agreement and a
  final legal review before any commercial launch.

## Deliberately not verified yet

- The published runtime images have not yet served a model on a GPU.
- No GPU pod has been created or started by GPUHarbor.
- Model loading, VRAM use, token generation, tool calling, throughput and
  measured cost require explicitly approved paid GPU canaries.
- Open WebUI/OpenHands reached their UIs, but end-to-end inference requires a
  running GPU model.
- Trademark policy, Contributor License Agreement signing and a final legal
  review before any commercial launch.
- Screenshots, release tags and announcements are deferred until deliberately
  prepared.

## Local image sizes

- controller: approximately 163 MB
- vLLM runtime: approximately 21.5 GB
- llama.cpp runtime: approximately 4.41 GB
- Bonsai runtime: approximately 4.49 GB

Runtime images are maintainer artifacts. Normal users should have RunPod pull
published immutable images directly from a registry; model weights are fetched
separately on the GPU pod and cached on its persistent volume.
