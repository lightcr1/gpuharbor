# Third-party components and model metadata

Checked against the public upstream APIs on 2026-09-28. This inventory is a
technical aid, not legal advice. Recheck immediately before a public release.
GPUHarbor does not redistribute model weights in its controller repository.

## Bundled model profiles

| Model | Upstream metadata license | Gated | Repository/file check |
|---|---|---:|---|
| `Qwen/Qwen3.8-27B-FP8` | Apache-2.0 | no | repository and safetensors files found |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | Apache-2.0 | no | repository, FP8 shards and tool parser found |
| `HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive` | Apache-2.0 | no | requested `Q6_K_P.gguf` found |
| `prism-ml/Ternary-Bonsai-2-27B-gguf` | Apache-2.0 | no | requested `PTQ1_0.gguf`, LICENSE and NOTICE found |

“Found” verifies public metadata and filenames only. It does not mean the model
has passed a GPU start, quality, safety or compatibility test. The catalog keeps
`verified: false` until such a test is recorded.

## Runtime and integration source

| Component | Reported license | Notes |
|---|---|---|
| vLLM (`vllm-project/vllm`) | Apache-2.0 | Runtime base; image digest still requires GPU validation |
| llama.cpp (`ggml-org/llama.cpp`) | MIT | GGUF runtime base |
| PrismML llama.cpp fork | MIT | Bonsai build pins commit `bdc23b56…`; experimental |
| OpenHands | MIT | Optional integration; Docker socket is a major privilege boundary |
| Open WebUI | custom license / `NOASSERTION` | Redistribution conditions and branding restriction apply |

Open WebUI's current license requires preserving notices and generally forbids
removing or replacing Open WebUI branding above its stated small-deployment
exception unless separately licensed. GPUHarbor treats Open WebUI as an optional
upstream image and does not rebrand or redistribute its source.

## Before release

- Read complete upstream license and notice files, not only API metadata.
- Preserve notices required by runtime images and model distributions.
- Recheck image tags/digests and the pinned Bonsai commit.
- Do not imply endorsement by RunPod, model authors, OpenHands or Open WebUI.
