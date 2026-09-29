# Changelog

All notable changes will be documented here once releases begin.

## Unreleased

- Added a Settings dialog (sidebar plus content) with an opt-in
  update-notification toggle. The choice is stored in the data volume;
  `GPUHARBOR_UPDATE_CHECK` now only seeds the default.
- Added `docs/SCRIPTS.md` and a Scripts section to the in-app documentation.
- Added two selectable themes — **Harbor blue** and **RunPod violet** — switchable
  under Settings → Appearance and shared with the documentation.
- Added `scripts/add-host` and documented how to add and list reachable addresses
  in `GPUHARBOR_TRUSTED_HOSTS`; `scripts/init-env` no longer drops existing hosts.
- Added an opt-in update check against the GitHub releases API and an update pill
  in the dashboard.
- Documentation: the sidebar highlights the current section, the first steps
  explain how to open `.env`, and the Open WebUI wiring is documented.
- Replaced the personal example address with the documentation placeholder
  `192.0.2.10` and removed the local publish-window guard.

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
