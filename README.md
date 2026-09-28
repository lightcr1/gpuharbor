# GPUHarbor

[![CI](https://github.com/lightcr1/gpuharbor/actions/workflows/ci.yml/badge.svg)](https://github.com/lightcr1/gpuharbor/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**A self-hosted control plane for curated AI models on RunPod.**

GPUHarbor starts, stops and configures a single GPU pod, exposes its model through
an authenticated OpenAI-compatible API, and makes model/runtime choices visible
in a compact web dashboard. Open WebUI and OpenHands are optional integrations,
not mandatory parts of the stack.

> Early prototype (`0.1.0-dev`). GPUHarbor is an independent community project and
> is not affiliated with or endorsed by RunPod.

## License

The open core is licensed under **Apache-2.0** (`LICENSE`). Planned Pro features
such as multi-provider management, teams and cost automation are a separate,
proprietary component and are not part of this repository. See
[docs/LICENSING.md](docs/LICENSING.md) for the open-core boundary and its
trade-offs.

## Why GPUHarbor?

- Change models, context size, parallelism, GPU, region and volume in the UI.
- Add, export and import custom model profiles without editing Python code.
- Receive new built-ins on upgrades without overwriting custom models or overrides.
- Use curated vLLM, llama.cpp/GGUF and experimental Bonsai runtime presets.
- Preview the exact redacted pod request before spending money.
- Keep billable actions hard-disabled until explicitly enabled.
- Connect any OpenAI-compatible client through one stable endpoint.
- Add Open WebUI, OpenHands, both, or neither.

## Bundled model profiles

| Profile | Runtime | Intended use | Status |
|---|---|---|---|
| Qwen3.8 27B FP8 | vLLM | balanced default | not GPU-verified |
| Qwen3 Coder 30B FP8 | vLLM | coding and agents | not GPU-verified |
| HauhauCS 35B Aggressive Q6 | llama.cpp | chat and coding | experimental |
| Ternary Bonsai 2 27B PTQ1_0 | Bonsai fork | chat and coding | experimental |

The repositories, requested files and model-card licenses were checked against
the public upstream APIs; GPU execution is still unverified. See
[model management](docs/MODELS.md) and [third-party inventory](docs/THIRD_PARTY.md).

## Install

Prerequisites: Docker with the Compose plugin. Nothing here touches RunPod or
spends money.

One command for a single machine:

```bash
git clone https://github.com/lightcr1/gpuharbor.git
cd gpuharbor
./scripts/install
```

The installer generates `.env` with independent random secrets, optionally
creates TLS certificates, builds and starts the stack, and prints the URLs and
the login user. It is safe to run again: real values are never overwritten.

Common variants:

```bash
# Reach the dashboard from another device in your LAN/VPN
./scripts/install --bind-ip 10.10.40.100

# LAN/VPN access plus HTTPS on port 9443
./scripts/install --bind-ip 0.0.0.0 --https 10.10.40.100 --tls-port 9443

# Only prepare .env and certificates, do not start anything
./scripts/install --no-start

# Reachable from anywhere on your own network (no public exposure)
./scripts/install --bind-ip 0.0.0.0
```

Manual equivalent:

```bash
./scripts/init-env --bind-ip 127.0.0.1
docker compose up --build -d
```

Open `http://127.0.0.1:8080`, or `http://<bind-ip>:8080` when you changed the
bind address. Login user is `admin`; the password is `GPUHARBOR_ADMIN_PASSWORD`
in `.env`. You can edit profiles and inspect plans without creating a pod. A
live start remains blocked while the billable-action switch is false or runtime
images are not configured as immutable digests.

Stop the stack with `docker compose down`.

## Reach it from another device

By default only `127.0.0.1` is bound, so other devices cannot connect. To reach
the dashboard from your laptop or phone:

1. Pick the machine's LAN or VPN address, for example `10.10.40.100`.
2. Run `./scripts/init-env --bind-ip 10.10.40.100` (or re-run `./scripts/install`
   with `--bind-ip`). The address is added to `GPUHARBOR_TRUSTED_HOSTS`
   automatically.
3. Open `http://10.10.40.100:8080`.

`--bind-ip 0.0.0.0` binds every interface. Keep the host on a trusted LAN or a
VPN such as Tailscale or WireGuard. Do **not** forward this port on your router;
plain HTTP plus a password is not meant for the public internet.

If a request returns "Invalid host header", the address you used is missing from
`GPUHARBOR_TRUSTED_HOSTS` in `.env`.

## Enable HTTPS

HTTPS is a Compose overlay and stays optional:

```bash
./scripts/install --bind-ip 0.0.0.0 --https 10.10.40.100 --tls-port 9443
```

This creates a local certificate authority in `tls/` and an nginx TLS proxy.
Import `tls/local-ca.crt` into the devices that should trust it, then open
`https://10.10.40.100:9443/`. The installer also sets
`GPUHARBOR_COOKIE_SECURE=true`, which only works over HTTPS.

Alternative manual start once certificates exist:

```bash
docker compose -f compose.yml -f compose.tls.yml up -d --build
```

Details, including public-domain setups, are in [docs/TLS.md](docs/TLS.md).
Never commit the `tls/` directory; it is already gitignored.

## Publish runtime images

A pod start needs runtime images with an immutable `sha256` digest in a
registry. Build them once on a machine with enough disk, then publish:

```bash
./scripts/publish-runtime-images --owner <your-ghcr-owner> --tag 0.1.0
```

The script needs `docker login ghcr.io` with a token that has `write:packages`,
prints the resulting digests and writes them to `runtime-digests.txt`. Put those
digests into `.env` (`RUNTIME_IMAGE_VLLM`, `RUNTIME_IMAGE_LLAMA_CPP`,
`RUNTIME_IMAGE_BONSAI`) before enabling billable actions. See
[docs/RELEASE_ARTIFACTS.md](docs/RELEASE_ARTIFACTS.md).

## Optional integrations

```bash
# Open WebUI
docker compose -f compose.yml -f compose.openwebui.yml up -d --build

# OpenHands (privileged; read the security guide first)
docker compose -f compose.yml -f compose.openhands.yml up -d --build

# Both
docker compose -f compose.yml -f compose.openwebui.yml -f compose.openhands.yml up -d --build
```

Read the [Open WebUI](docs/integrations/open-webui.md),
[OpenHands](docs/integrations/openhands.md), [TLS](docs/TLS.md) and
[security](docs/SECURITY.md) and [safe-upgrade](docs/UPGRADES.md) guides first.
The exact local validation state is recorded in [CURRENT_STATUS.md](docs/CURRENT_STATUS.md).

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest
```

No Git remote is configured in the local prototype. The publication guard blocks
commits and pushes Monday-Friday from 07:00 through 17:59 in `Europe/Zurich`.
After Git is initialized, enable the versioned hooks with:

```bash
git config core.hooksPath .githooks
```

The guard does not rewrite or fake timestamps.
