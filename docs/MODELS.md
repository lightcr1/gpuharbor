# Models and runtimes

GPUHarbor separates model metadata from runtime images. Shipped built-ins are
read-only; custom models and built-in overrides live in a versioned persistent
user catalog. This prevents image updates from overwriting owner data. Models
can be created, edited, exported, imported and reset in the dashboard; runtime
definitions remain administrator-controlled because a runtime image executes
code on the GPU pod.

Editable model fields include repository ID, runtime, GGUF filename, served
model names, capabilities, default context length, parallel sequences, GPU
memory utilization, allowed GPU types, volume size, license/gating metadata and verification status.
Launch-time overrides for context, parallelism, GPU, datacenter and volume are
available in the dashboard without modifying the saved preset.

The bundled catalog contains four curated starting points. `verified: false`
means their current combination of image, GPU and settings has not yet passed a
recorded GPUHarbor GPU test. Do not interpret `stable` as a performance guarantee.

The bundled source repositories, requested files and public license metadata were
checked on 2026-09-28; see `THIRD_PARTY.md`. This does not replace a final legal
review or a real GPU compatibility test.

Runtime images cannot be changed in the browser. They must be configured as
immutable `sha256` digests in `.env`; this prevents a compromised dashboard
account from selecting arbitrary executable images. Upgrade and migration rules
are documented in [UPGRADES.md](UPGRADES.md).
