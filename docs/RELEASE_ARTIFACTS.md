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

These images are pulled by RunPod, not by the machine running the controller.
Maintainers build/test them locally; normal users select the published immutable
digests. Existing private `lightcr1/runpod-qwen-runtime` images remain separate
and are not silently retagged as public GPUHarbor releases.

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
