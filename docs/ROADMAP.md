# Roadmap

## Done

- Controller, dashboard, cost lock, model catalog with overrides.
- Curated vLLM, llama.cpp and Bonsai profiles.
- Optional Open WebUI, OpenHands and local HTTPS.
- Update-safe catalog, import/export, region selection, GPU picker.
- Bilingual dashboard and docs (English and German) with a current-section
  sidebar highlight.
- Runtime image status shown read-only.
- Model editor can look a repository up on Hugging Face and propose fields.
- Settings dialog with an opt-in update-notification toggle and an update pill.
- `scripts/add-host` and `docs/SCRIPTS.md`.
- Published runtime images.
- CI and 121 tests.

## Next

- Test the remaining profiles on a real GPU and record the numbers.
- Screenshots for the settings dialog.

## Later

- A second provider. Keep the core single-provider and put multi-provider into
  the separate closed component instead of building a second integration before
  anyone asks for it.
- Contributor License Agreement and a trademark policy before any commercial
  launch.
- Automated runtime image builds.
