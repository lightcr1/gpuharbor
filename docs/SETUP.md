# Setup

You need Docker with the Compose plugin. The controller itself needs no GPU.

## Install

```bash
git clone https://github.com/lightcr1/gpuharbor.git
cd gpuharbor
./scripts/install
```

That writes `.env` with random secrets, starts the stack and prints the URL and
login. Run it again any time; real values are not overwritten.

Prefer questions and checkboxes:

```bash
./scripts/setup
```

Manual equivalent, if you want to see every step:

```bash
./scripts/init-env --bind-ip 127.0.0.1
docker compose up --build -d
```

Open `http://127.0.0.1:8080`. User is `admin`; the password is
`GPUHARBOR_ADMIN_PASSWORD` in `.env`.

Stop with `docker compose down`.

## Reach it from another device

Only `127.0.0.1` is bound by default. To use the dashboard from a laptop or
phone, bind the machine's LAN or VPN address:

```bash
./scripts/init-env --bind-ip 10.10.40.100
docker compose up -d
```

Then open `http://10.10.40.100:8080`. The address is added to
`GPUHARBOR_TRUSTED_HOSTS` for you. `--bind-ip 0.0.0.0` binds every interface.

Keep this on a trusted LAN or a VPN such as Tailscale or WireGuard. Plain HTTP
with a password does not belong on the public internet, so do not forward the
port on your router.

If you see `Invalid host header`, the address is missing from
`GPUHARBOR_TRUSTED_HOSTS` in `.env`.

## HTTPS

```bash
./scripts/setup                                              # interactive
./scripts/install --bind-ip 0.0.0.0 --https 10.10.40.100 --tls-port 9443
```

This creates a local certificate authority under `tls/` and starts an nginx TLS
proxy. Import `tls/local-ca.crt` on the devices that should trust it, then open
`https://10.10.40.100:9443/`. The installer also sets
`GPUHARBOR_COOKIE_SECURE=true`, which only makes sense over HTTPS.

If port 8443 is already taken, set `TLS_PORT` to a free port.

Manual start once certificates exist:

```bash
docker compose -f compose.yml -f compose.tls.yml up -d --build
```

For a public domain, use a normal reverse proxy with a trusted certificate
instead of the local CA. Details: [TLS.md](TLS.md).

Never commit `tls/`. It is in `.gitignore`.

## Optional extras

```bash
# Open WebUI
docker compose -f compose.yml -f compose.openwebui.yml up -d --build

# OpenHands Agent Canvas — runs generated code
docker compose -f compose.yml -f compose.openhands.yml up -d --build
```

See [Open WebUI](integrations/open-webui.md) and
[OpenHands](integrations/openhands.md).
