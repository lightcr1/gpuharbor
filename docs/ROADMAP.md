# Roadmap

## 0.1 foundation

- [x] Local controller skeleton and cost lock
- [x] Versioned, update-safe UI model catalog, overrides and import/export
- [x] Curated vLLM, llama.cpp and Bonsai profiles
- [x] Optional Open WebUI and OpenHands overlays
- [x] Complete mocked lifecycle and authentication tests
- [x] Verify controller build and Compose combinations
- [x] Add reverse-proxy/TLS deployment example
- [x] Inventory dependency and model licenses (final legal review remains)
- [x] Project core licensed under Apache-2.0 with a documented open-core boundary
- [x] Build controller and all three runtime images locally
- [x] Smoke-test Open WebUI, OpenHands and TLS overlays locally
- [ ] GPU canary tests and measured VRAM/cost data (owner cost approval required)

## Later

- Provider abstraction beyond RunPod (keep the single-provider core and a
  separate closed Pro component; do not build a second provider before demand)
- Trademark policy and Contributor License Agreement signing before public launch
- Runtime image build/release automation
- Cost history and budget limits
- Localization files instead of embedded UI strings
- Safer remote OpenHands sandbox backend
