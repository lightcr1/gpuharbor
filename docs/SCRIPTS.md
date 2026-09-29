# Scripts

Everything lives in `scripts/` and is run from the GPUHarbor folder. They are
plain Python or shell scripts; nothing is installed system-wide. Python scripts
use the interpreter you use to start them.

In every example, `192.0.2.10` is the RFC 5737 documentation address — replace it
with your own LAN or VPN address.

| Script | Purpose |
|---|---|
| [`install`](#install) | Install or update the stack in one command |
| [`setup`](#setup) | Interactive assistant with questions |
| [`doctor`](#doctor) | Check the installation and say what to fix |
| [`trust-ca`](#trust-ca) | Trust the local HTTPS certificate on this computer |
| [`init-env`](#init-env) | Create or update `.env` (secrets, addresses) |
| [`add-host`](#add-host) | Allow more addresses to reach the dashboard |
| [`set-runpod-key`](#set-runpod-key) | Store the RunPod API key safely |
| [`generate-local-tls`](#generate-local-tls) | Create the local HTTPS certificate |
| [`check-compose`](#check-compose) | Validate the Compose files |
| [`check-local-release`](#check-local-release) | Run all checks before releasing |
| [`publish-runtime-images`](#publish-runtime-images) | Push runtime images to GHCR |

## install

Installs and starts GPUHarbor (or updates an existing install). It creates
`.env`, generates the TLS certificate when asked, and runs `docker compose up`.
Your `.env` and data are kept.

```bash
./scripts/install                                  # local, HTTPS by default
./scripts/install --webui --openhands              # plus the integrations, also over HTTPS
./scripts/install --no-https                       # plain HTTP on localhost
./scripts/install --trust                          # also trust the certificate without asking
./scripts/install --bind-ip 192.0.2.10             # reachable on LAN or VPN
./scripts/install --bind-ip 0.0.0.0 --https 192.0.2.10 --tls-port 9443
./scripts/install --no-start                       # prepare files only
./scripts/install --pull                           # pull base images first
```

## setup

The same as `install`, but it asks questions (bind address, HTTPS, Open WebUI,
OpenHands, start now). Every answer can also be given as a flag, so it works
unattended with `--yes`.

```bash
./scripts/setup
./scripts/setup --dry-run --bind 192.0.2.10
```

## doctor

Checks Docker and Compose, your `.env`, the certificate and the running containers,
and prints `ok`, `note` or `FAIL` with a hint for each. It changes nothing and does not
contact RunPod. Exit code 1 means a problem was found.

```bash
./scripts/doctor              # everything
./scripts/doctor --offline    # only files and settings, no Docker calls
```

## trust-ca

Installs `tls/local-ca.crt` as a trusted authority for the system and for Chrome,
Chromium and Firefox (Linux, macOS). It prints every command and asks before it
uses `sudo`. On Linux the browser stores need `certutil` (`libnss3-tools`).

```bash
./scripts/trust-ca            # ask, then install
./scripts/trust-ca --dry-run  # only print the steps
./scripts/trust-ca --remove   # undo
```

Other devices need the same file imported by hand, see [TLS.md](TLS.md).

## init-env

Writes `.env` from `.env.example` and fills in random secrets. Existing real
values are never overwritten, so running it again is safe. It also sets the bind
address and the trusted hosts.

```bash
./scripts/init-env --bind-ip 192.0.2.10
./scripts/init-env --bind-ip 0.0.0.0 --https-host 192.0.2.10 --tls-port 9443
./scripts/init-env --add-trusted-host 192.168.1.5
./scripts/init-env --force            # regenerate every secret
./scripts/init-env --show-login       # print the admin user and password
./scripts/init-env --overlay compose.tls.yml   # select the Compose stack (written to COMPOSE_FILE)
./scripts/init-env --reset-password   # new admin password, everything else kept
```

Useful flags: `--bind-ip`, `--https-host`, `--tls-port`, `--trusted-hosts`,
`--add-trusted-host`, `--env`, `--example`, `--force`.

## add-host

Adds one or more addresses to `GPUHARBOR_TRUSTED_HOSTS` without removing the
existing ones, so the dashboard is reachable from them. The address must be
exactly what you type in the browser.

```bash
./scripts/add-host 192.168.1.5
./scripts/add-host 192.168.1.5 vpn.example.ts.net --bind-ip 0.0.0.0
grep GPUHARBOR_TRUSTED_HOSTS .env      # list what is allowed
docker compose up -d                   # apply
```

## set-runpod-key

Reads the RunPod API key with a hidden prompt (so it stays out of your shell
history) and replaces only the `RUNPOD_API_KEY` line in `.env`. The controller is
restarted afterwards unless you pass `--no-restart`.

```bash
./scripts/set-runpod-key
```

## generate-local-tls

Creates a local certificate authority and a server certificate signed by it,
under `tls/`. Use the exact IP or hostname you will type in the browser.

```bash
./scripts/generate-local-tls 192.0.2.10
./scripts/generate-local-tls harbor.local tls
```

Import `tls/local-ca.crt` on the devices that should trust the certificate. The CA key is deleted after
signing; never commit the `tls/` folder.

## check-compose

Checks that every Compose combination (base, TLS, Open WebUI, OpenHands and all
together) is valid. Needs Docker with the Compose plugin.

```bash
./scripts/check-compose
```

## check-local-release

Runs the whole pre-release check: tests, byte-compilation, Markdown link check,
JavaScript syntax check, `check-compose` and a scan for secrets and stale names.

```bash
./scripts/check-local-release
```

## publish-runtime-images

Tags locally built runtime images and pushes them to GHCR. Building the vLLM
image needs a lot of disk, so this is done by hand, not in CI.

```bash
./scripts/publish-runtime-images --owner lightcr1 --tag 0.1.0
./scripts/publish-runtime-images --dry-run
```

Prerequisites: `docker login ghcr.io -u <user>` with a token that has
`write:packages`, and the runtime images built locally (see the script header).
