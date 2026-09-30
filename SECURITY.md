# Security

GPUHarbor holds a RunPod API key and can spend money, so the defaults are
cautious.

## Defaults

- Billable actions are off until you set `RUNPOD_ALLOW_BILLABLE_ACTIONS=true`.
- The RunPod key only ever lives in the controller, never in a pod or a browser.
- Control, inference and runtime credentials are three separate secrets.
- Runtime images must be an immutable `sha256` digest before a pod can start.
- The controller container drops all Linux capabilities, has a read-only root
  filesystem, and only writes to `/data` and a small temp directory.

## Browser and API

- Session cookies are HttpOnly and SameSite=Lax.
- Changes made with a session need a CSRF token. API clients using the control
  token do not.
- Failed logins are rate limited per client address.
- Allowed `Host` headers come from `GPUHARBOR_TRUSTED_HOSTS`.
- Responses carry a strict CSP (`script-src 'self'`, `style-src 'self'`, no inline
  code), frame-deny, nosniff, referrer and permissions headers. Dashboard and API
  responses are not cached.
- The controller refuses to start while a credential is empty or still the
  `replace-with-…` placeholder from `.env.example`.
- Credentials are compared in constant time, and malformed or non-ASCII values
  are answered with 401 instead of an error.
- Set `GPUHARBOR_COOKIE_SECURE=true` when you use HTTPS.
- Data coming back from RunPod is scrubbed for fields that look like tokens,
  keys, passwords or authorization headers before it reaches the browser.

The login limiter keeps its state in memory, which is fine for one controller
process. Running several replicas behind the public internet is not a supported
setup.

## Models and runtimes

You can edit model profiles in the browser, but not command-line arguments or
container images. vLLM parser options are an allowlist. The `trust_remote_code`
switch is visible in the UI because it is a real decision: it lets Python shipped
inside a model repository run on the pod. Only enable it for repositories you
trust.

The runtime gateway binds the actual model server to loopback and exposes only
authenticated `/v1/*` and `/health`.

## Network

HTTPS is the default: `./scripts/install` puts the dashboard, Open WebUI and
OpenHands behind an nginx TLS proxy and limits every plain HTTP port to this
machine. Keep it on localhost, a LAN, or a VPN. For LAN access use the TLS overlay and set
your exact hosts; see [docs/TLS.md](docs/TLS.md). Do not put the controller,
Open WebUI or OpenHands on the public internet.

Open WebUI gets only the inference token. OpenHands gets its own backend key and
can run code, so give it an empty workspace and review what it changes.
The PI coding agent (`scripts/connect-pi`) also gets only the inference token, stored in
PI's `gpuharbor.json` with mode 600. PI can run commands too; use a dedicated workspace.

## Reporting

Report vulnerabilities privately to the maintainer. Do not open a public issue
with credentials or a working exploit.
