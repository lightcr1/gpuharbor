# Third-party components

Checked against public APIs on 2026-09-28. This is a technical inventory, not
legal advice. Recheck before any release.

## Bundled model profiles

| Model | License (model card) | Gated | Checked |
|---|---|---:|---|
| `Qwen/Qwen3.8-27B-FP8` | Apache-2.0 | no | repo and files exist |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | Apache-2.0 | no | repo and files exist |
| `HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive` | Apache-2.0 | no | requested `.gguf` exists |
| `prism-ml/Ternary-Bonsai-2-27B-gguf` | Apache-2.0 | no | requested `.gguf`, LICENSE, NOTICE exist |

"Checked" means the repository and filenames were there and the model card lists
that license. It does not mean the model ran, or that it produces good output.
GPUHarbor does not ship model weights.

## Runtimes and integrations

| Component | License | Notes |
|---|---|---|
| vLLM | Apache-2.0 | base for the vLLM runtime image |
| llama.cpp (`ggml-org`) | MIT | base for the GGUF runtime image |
| PrismML llama.cpp fork | MIT | Bonsai build, pinned to commit `bdc23b56…`; experimental |
| OpenHands Agent Canvas | MIT | optional; runs generated code |
| Open WebUI | custom license | optional; branding must stay, see below |

Open WebUI's license allows use but forbids removing or replacing its branding
above a stated small-deployment exception, unless you have permission. GPUHarbor
uses the upstream image unchanged and does not rebrand it.

## Before releasing

Read the full upstream license and notice files, not just the API metadata. Keep
the notices the images and models require. Recheck image tags, digests and the
pinned Bonsai commit. Do not imply that RunPod, the model authors, OpenHands or
Open WebUI endorse this project.
