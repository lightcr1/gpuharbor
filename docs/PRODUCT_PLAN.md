# GPUHarbor product plan

## Product promise

A user can connect a RunPod account, choose or define a model in a browser,
inspect placement and safety checks, start exactly one GPU pod, and consume the
model through one stable OpenAI-compatible endpoint. Chat and coding frontends
remain replaceable clients rather than mandatory platform components.

## Product boundaries

### Core

- authenticated controller dashboard and API
- one managed pod, duplicate-create protection and explicit destructive actions
- model/runtime registry with persistent UI edits
- launch-time context, concurrency, GPU, datacenter and volume overrides
- immutable runtime images and separate control/inference/runtime credentials
- redacted plan, read-only availability check and default billable-action lock
- automatic idle stop
- OpenAI-compatible authenticated proxy

### Optional Open WebUI

Open WebUI is a consumer of `/v1`, owns chat accounts/history, and can be
installed or removed without changing GPUHarbor state. Its Compose overlay has a
separate persistent volume and receives only the inference token.

### Optional OpenHands

OpenHands is another `/v1` consumer and receives only the inference token. It is
explicitly privileged because its standard sandbox flow needs Docker access.
The first release must mark it experimental and document dedicated-host/VM use.
Pod lifecycle control is not delegated to an agent by default.

### Administrator-only configuration

API credentials, session secrets, runtime image digests and network exposure do
not belong in the browser. Allowing these fields in the UI would turn a stolen
web session into arbitrary code execution or account takeover. Model settings
are editable; executable images remain deployment configuration.

## UX flows

### First start

1. Copy `.env.example`, generate distinct credentials, leave billing disabled.
2. Start only the controller.
3. Log in, review bundled models and edit/add profiles.
4. Inspect a redacted launch plan and read-only GPU availability.
5. Build/pin required runtime images.
6. Explicitly enable billable actions only for a controlled canary.

### Model management

1. Choose **New model** or edit an inactive profile.
2. Select vLLM, llama.cpp or experimental Bonsai runtime.
3. Enter repository, aliases, capabilities and safe runtime options.
4. Configure context, concurrency, GPU priority and storage.
5. Save; server-side schema validation rejects unsafe filenames, unknown
   runtimes, unsupported parsers and invalid resource ranges.
6. At launch, temporarily override operational values without changing preset.

### Integrations

1. Start the controller plus exactly the desired Compose overlays.
2. Integrations discover models through the OpenAI-compatible endpoint.
3. GPUHarbor remains the only holder of the RunPod control credential.
4. Removing an integration does not remove models, pods or the other client.

## Release gates

### Architecture gate

- provider code separated sufficiently for later providers
- no Jarvis-specific endpoints, paths, IPs or assumptions
- registry migrations/versioning designed before changing the schema after 0.1

### Security gate

- secret scanner clean
- authenticated mutation endpoints and CSRF review
- immutable runtime images
- OpenHands threat model reviewed
- destructive flows require explicit confirmation
- no secrets in examples, logs, screenshots or Git history

### Quality gate

- unit tests for registry, auth, lifecycle, redaction and duplicate protection
- controller container and all Compose combinations build
- browser smoke test on desktop and mobile
- real canary for each runtime/GPU combination, with measured VRAM and startup
  time clearly distinguished from estimates

### Legal gate

- project license selected
- model licenses and gated-access requirements documented
- third-party Bonsai fork and container redistribution reviewed
- independent-project RunPod disclaimer visible
- final name checked across GitHub, package registries and trademarks

### Publication gate

- no remote until the owner approves the complete local release candidate
- no commit or push Monday-Friday 07:00-18:00 Europe/Zurich
- no timestamp rewriting; commit only in an allowed window
- first public state includes documentation, tests, screenshots and a coherent
  history rather than incremental private setup work

## Milestones

1. **Local foundation:** registry, controller, UI, overlays, tests.
2. **Hardening:** auth tests, CSRF review, TLS example, dependency pins.
3. **Runtime validation:** build vLLM/llama/Bonsai images and run paid canaries
   only after explicit cost approval.
4. **Release candidate:** naming/license decisions, polished bilingual docs,
   screenshots and migration notes.
5. **Private review:** initialize Git and create commits only in allowed windows;
   still no remote.
6. **Public launch:** owner-approved repository, topics, `v0.1.0`, announcement
   material and issue templates.

## Known decisions still owned by the project owner

- The working name is **GPUHarbor**. Exact GitHub repository and organization
  names as well as PyPI/npm package names were available when checked; complete
  a trademark review before publication.
- Select Apache-2.0, MIT or another compatible project license.
- Decide which runtime images the project will build and publish versus require
  users to build themselves.
- Approve budget, GPU and region for each real canary test.
