# Security model

## Defaults

- Billable RunPod actions are disabled by default.
- The RunPod account key is available only to the controller.
- Control, inference and internal runtime credentials are separate.
- Runtime images must use immutable sha256 digests before a pod can start.
- The controller and optional integrations bind to localhost unless changed.
- The controller container drops Linux capabilities and uses a read-only root
  filesystem; only `/data` and a small temporary filesystem are writable.

## Browser and API protection

- Dashboard sessions use HttpOnly, SameSite=Lax cookies.
- Every session-authenticated POST/PUT/PATCH/DELETE requires a per-session CSRF
  token. Control-token API clients do not use browser CSRF tokens.
- Login failures are rate-limited in memory per client address.
- Trusted `Host` values are configured through `GPUHARBOR_TRUSTED_HOSTS`.
- Responses apply CSP, frame denial, MIME-sniffing, referrer and permissions
  headers. API/dashboard responses are not cached.
- Set `GPUHARBOR_COOKIE_SECURE=true` when using the TLS overlay.
- RunPod status, catalog and plan responses are recursively scrubbed for fields
  whose names indicate tokens, keys, passwords, secrets or authorization data.

The in-memory login limiter is suitable for a single controller process. A
multi-replica internet service would require a shared limiter, but direct public
internet exposure is outside GPUHarbor's supported deployment model.

## Model and runtime boundary

Model profiles may choose validated repositories, aliases and resource values,
but cannot provide arbitrary command-line arguments or executable images.
vLLM parser options use an explicit allowlist. `trust_remote_code` is visible in
the UI because enabling it permits model-repository Python code to run inside
the GPU pod; enable it only for reviewed repositories.

The runtime gateway binds the actual model server to loopback and exposes only
authenticated `/v1/*` and `/health` paths. Runtime images are administrator-only
configuration and must be immutable digests.

## Network exposure

Use localhost for one-machine setups. For LAN access, use the optional TLS
overlay described in [TLS.md](TLS.md), set the exact trusted hosts, and prefer a
VPN such as Tailscale or WireGuard. Do not expose the controller, Open WebUI or
OpenHands directly to the public internet.

## Optional integrations

- Open WebUI receives only `MODEL_ACCESS_TOKEN`, not RunPod control credentials.
- OpenHands Agent Canvas receives a separate backend key. Its model provider may
  use `MODEL_ACCESS_TOKEN`, which grants inference only.
- OpenHands can execute code and modify its mounted projects. Use a dedicated
  workspace or VM and review every change before deployment.

Report vulnerabilities privately to the repository owner once a public contact
channel exists. Never open public issues containing credentials or exploit data.
