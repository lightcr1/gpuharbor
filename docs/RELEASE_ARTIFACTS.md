# Planned release artifacts

Nothing is published yet. Names below are the intended layout and require owner
approval, registry ownership and an allowed publication window.

## Source and controller

- Source repository: GPUHarbor controller, UI, Compose overlays, runtime
  Dockerfiles, tests and documentation.
- Controller image: `ghcr.io/<owner>/gpuharbor-controller:<version>` plus an
  immutable digest.

A PyPI package is not required for the first Docker-first release. The Python
project metadata exists for building the controller wheel inside its image. Do
not publish npm packages; the UI has no separate JavaScript package.

## GPU runtime images

- `ghcr.io/<owner>/gpuharbor-runtime-vllm:<version>`
- `ghcr.io/<owner>/gpuharbor-runtime-llama-cpp:<version>`
- `ghcr.io/<owner>/gpuharbor-runtime-bonsai:<version>` (experimental)

### Published 0.1.0 (linux/amd64)

| Runtime | Image + digest |
|---|---|
| vLLM | `ghcr.io/lightcr1/gpuharbor-runtime-vllm@sha256:a35d491bf6f4fc535cda18a85947b112300225b2ecc039b83d8311117082816f` |
| llama.cpp | `ghcr.io/lightcr1/gpuharbor-runtime-llama-cpp@sha256:6367ffb83e9e4b4981df883ba988840a8ca4ab91518b6ee16bbe211eb9e1596a` |
| Bonsai | `ghcr.io/lightcr1/gpuharbor-runtime-bonsai@sha256:a83dc25c8a5ca4e6926d36bf6e2796fa8879a5b979c51083bdea1eeb46427fe1` |

These digests are baked into `.env.example`, so a normal install works without
building anything. They are published images, not yet GPU-verified; see
[CURRENT_STATUS.md](CURRENT_STATUS.md).

These images are pulled by RunPod, not by the machine running the controller.
Maintainers build them once and publish with
`./scripts/publish-runtime-images --owner <owner> --tag <version>`, which also
prints the digests to paste into `.env` and documentation.

Building the vLLM image pulls a base image of roughly 20 GB. That normally
exceeds the free disk of a GitHub-hosted runner, so image builds are not part of
the default CI workflow; CI runs the test suite instead. Use a larger/self-hosted
runner if you want image builds in CI.

Existing private `lightcr1/runpod-qwen-runtime` images remain separate and are
not silently retagged as public GPUHarbor releases.

## Optional upstream images

GPUHarbor references reviewed upstream images for Open WebUI and OpenHands Agent
Canvas. It does not rebuild, rebrand or republish them. Their licenses, versions
and architecture-specific digests are documented separately.

## Model delivery

GPUHarbor never packages or redistributes model weights. Built-in catalog entries
contain repository IDs, exact GGUF filenames where applicable, runtime choice and
resource defaults. On first pod start:

1. RunPod pulls the selected GPUHarbor runtime image.
2. vLLM or `huggingface_hub` downloads the model directly from Hugging Face.
3. The model cache is stored on the pod's persistent `/workspace` volume.
4. Later starts reuse that cache while the volume exists.

Public models need no Hugging Face credential. Gated/private models require the
owner's own token and upstream access grant.
