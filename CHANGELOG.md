# Changelog

All notable changes will be documented here once releases begin.

## 0.1.5 - 2026-09-29

The goal of this release: install with one command, and have the models work in Open
WebUI and OpenHands without configuring anything.

### Added

- **HTTPS by default.** `./scripts/install` and `./scripts/setup` create a local CA and
  start the TLS proxy; `--no-https` opts out. The plain HTTP ports of all services are
  bound to this machine, so only TLS is reachable from the network.
- **OpenHands is connected automatically.** The controller writes one LLM profile per
  model (`gpuharbor-<id>`) into OpenHands, activates the one for the running model and
  keeps them in sync when models change. Settings fit local models (native tool calls
  only where the vLLM profile enables them, sensible output length, long cold-start
  timeout, no hosted-provider options). Profiles you made yourself are never touched.
- **Open WebUI and OpenHands behind the same proxy:** `https://localhost:8444` and
  `:8445`, selected with `install --webui` / `--openhands`. The dashboard header links to
  them.
- **Dashboard:** a *Getting started* checklist and a *Connect an app* card with base URL,
  model name and API key (show/copy).
- `./scripts/doctor` checks Docker, `.env`, certificate and containers and says what to
  fix. `./scripts/trust-ca` trusts the local certificate on Linux/macOS (asks before sudo).
- The installer checks Docker and Compose 2.24+, waits until the dashboard answers, offers
  to trust the certificate, and writes `COMPOSE_FILE` into `.env` so a plain
  `docker compose up -d` keeps the chosen stack. `setup` now uses the same code.
- Readable generated admin password (`ABCD-EFGH-JKMN-PQRS-TUVW`), `init-env --show-login`
  and `--reset-password`.
- A third theme, **Harbor light**, price hint under the GPU picker, translated badges.
- `generate-local-tls` keeps a valid certificate (and the CA your devices trust), accepts
  several names and always covers `localhost`, `127.0.0.1` and `::1`.
  `docs/TLS.md` explains trusting the CA per browser and OS.

### Security

- Constant-time credential checks that never raise on non-ASCII input and never accept an
  empty secret (controller and runtime gateway). Runtime images `0.1.4` contain the fix and
  are pinned in `.env.example` (verified on a real GPU pod).
- The controller refuses to start with empty or template-placeholder credentials.
- Sessions are tracked server-side: logout revokes the cookie.
- Strict Content-Security-Policy (no inline code); DOM text nodes instead of `innerHTML`.
- nginx rate-limits `/api/login`; `generate-local-tls` deletes the CA key after signing.

### Fixed

- Open WebUI and OpenHands could not reach the controller: the Compose service name
  `controller` was rejected as an untrusted host (HTTP 400).
- Upgrading with `install --webui` failed on older `.env` files; `init-env` now adds
  settings introduced by newer versions.
- `set-runpod-key` no longer drops the TLS overlay when it restarts the stack.
- `/v1` errors use the OpenAI error shape with actionable messages ("No model is running.
  Start a pod in the GPUHarbor dashboard first.").
- The tests no longer read a developer's real `.env`.

### Changed

- nginx no longer sends `Strict-Transport-Security`: with a local CA it would pin every
  port of `localhost` and make certificate errors impossible to bypass.
- Dashboard and docs styles and scripts moved to `/static/`, one shared `theme.css`.
- `runtime-digests.txt` moved to `runtime/digests.txt`; base image is Python 3.14.

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
