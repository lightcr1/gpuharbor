# Changelog

All notable changes will be documented here once releases begin.

## Unreleased

- Align the numeric fields in the start panel so all four inputs share one line.
- Fix a literal `&amp;` on the German delete button and re-render option lists
  when the language changes.

- Added the GPUHarbor controller, authenticated dashboard and OpenAI-compatible proxy.
- Added versioned, update-safe built-ins, custom profiles, overrides, reset,
  import/export, automatic legacy migration and launch-time resource overrides.
- Added curated Qwen, HauhauCS and Ternary Bonsai profiles.
- Added vLLM, llama.cpp and experimental Bonsai runtime definitions.
- Added billable-action lock, duplicate-pod protection and idle stop.
- Added optional Open WebUI, OpenHands Agent Canvas and local TLS overlays.
- Added CSRF protection, login throttling, trusted-host checks, security headers,
  recursive secret redaction and immutable runtime-image enforcement.
- Added reproducible controller dependency lock and local test suite.
- Added interactive `scripts/setup` assistant (bind address, HTTPS, Open WebUI,
  OpenHands) and a `/docs` page in the controller explaining every field.
- Added region-based datacenter selection, GPU checkboxes from the live RunPod
  catalog, field help texts, an output-mode switch and a model-ready indicator.
- Added a favicon and a `/api/model/ready` endpoint.
- English dashboard and docs with a German switch; runtime image status shown
  read-only in the dashboard.
- "Look up on Hugging Face" in the model editor proposes runtime, context,
  volume, license, GGUF filenames and GPUs for a repository.
