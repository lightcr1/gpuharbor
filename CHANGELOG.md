# Changelog

All notable changes will be documented here once releases begin.

## Unreleased

### Added

- **HTTPS by default.** `./scripts/install` and `./scripts/setup` create a local CA
  and start the TLS proxy; `--no-https` opts out. The plain HTTP ports of all
  services are bound to this machine, so only TLS is reachable from the network.
- Open WebUI (`https://localhost:8444`) and OpenHands (`https://localhost:8445`)
  behind the same proxy, selected with `install --webui` / `--openhands`.
- The installer writes `COMPOSE_FILE` into `.env`, so a plain `docker compose up -d`
  keeps the chosen stack. `init-env --overlay` sets it.
- `generate-local-tls` accepts several names and always covers `localhost`,
  `127.0.0.1` and `::1`. `docs/TLS.md` explains trusting the CA per browser and OS.

### Security

- Runtime images `0.1.4` (gateway token check no longer raises on non-ASCII input).
  Verified on a real GPU pod, then pinned in `.env.example`.

### Fixed

- Open WebUI and OpenHands could not reach the controller: the Compose service name
  `controller` was rejected as an untrusted host (HTTP 400). It is now always
  accepted.
- `set-runpod-key` no longer drops the TLS overlay when it restarts the stack.

### Changed

- nginx no longer sends `Strict-Transport-Security`: with a local CA it would pin
  every port of `localhost` and make certificate errors impossible to bypass.

## 0.1.4 - 2026-09-29

### Security

- Sessions are now tracked server-side: logging out revokes the cookie, so a
  copied cookie no longer stays valid for 12 hours. A restart signs everyone out.
- `generate-local-tls` deletes the CA key after signing the server certificate.
- Dependencies checked with `pip-audit`: no known vulnerabilities.

- Constant-time credential checks no longer raise on non-ASCII input (a crafted
  header used to cause a 500) and never accept an empty secret. The runtime
  gateway got the same fix; it ships with the next runtime image build.
- The controller refuses to start with empty or template-placeholder credentials.
- Strict Content-Security-Policy: the dashboard and docs no longer use inline
  scripts, styles or event handlers, so `unsafe-inline` is gone.
- Status and model messages are rendered with DOM text nodes instead of
  `innerHTML`, and the update link only accepts `https://` URLs.
- The nginx overlay rate-limits `/api/login` and forwards the real client address.
- `GPUHARBOR_UPDATE_REPO` is validated as `owner/name`.

### Added

- `scripts/init-env --show-login` prints the admin user and password;
  `--reset-password` sets a new one. The docs and README point to both.
- A third theme, **Harbor light**, for the dashboard and the documentation.
- Price hint under the GPU picker from the live RunPod catalog.
- Buttons are disabled while an action runs; model badges are translated; the
  compact output view is the default.

### Changed

- `runtime-digests.txt` moved to `runtime/digests.txt`.

- Dashboard and docs styles and scripts moved to `/static/`; one shared
  `theme.css` holds the design tokens for both themes.
- Dashboard layout cleaned up: consistent spacing and control heights, grouped
  actions with the destructive one set apart, outlined danger buttons, no
  truncated region select, tidier editor dialog, better small-screen layout.
- An expired session now returns to the sign-in form.
- Server messages are English throughout (some were German).

## 0.1.3 - 2026-09-29

- Added a Settings dialog (sidebar plus content) with an opt-in
  update-notification toggle. The choice is stored in the data volume;
  `GPUHARBOR_UPDATE_CHECK` now only seeds the default.
- Added two selectable themes — **Harbor blue** and **RunPod violet** — switchable
  under Settings → Appearance and shared with the documentation.
- Added an opt-in update check against the GitHub releases API and an update pill
  in the dashboard.
- Added `docs/SCRIPTS.md` and a Scripts section to the in-app documentation.
- Added `scripts/add-host`; `scripts/init-env` no longer drops existing trusted
  hosts and accepts `--add-trusted-host`.
- Documentation: the sidebar highlights the current section, the first steps
  explain how to open `.env`, and the Open WebUI wiring is documented.
- Replaced the personal example address with the documented RFC 5737 placeholder
  `192.0.2.10` and removed the local publish-window guard.
- Serve `/docs` and `/docs/de` with `Cache-Control: no-store`.
- Align the numeric fields in the start panel so all four inputs share one line.
- Fix a literal `&amp;` on the German delete button and re-render option lists
  when the language changes.

## 0.1.0 - 2026-09-28

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
