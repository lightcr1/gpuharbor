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

Open `https://localhost:8443` (or `http://127.0.0.1:8080` with `--no-https`). User is `admin`. The install script generated a
random password; show it with `./scripts/init-env --show-login` and set a new one
with `./scripts/init-env --reset-password`. The controller refuses to start with
the placeholder values from `.env.example`.

Stop with `docker compose down`.

## Where is the password, and how do I open `.env`?

`.env` is a plain text file in the GPUHarbor folder. It stores your passwords and
settings. The name starts with a dot, so it is hidden by default.

- **Terminal (Linux, macOS, WSL):**

  ```bash
  nano .env     # edit (save: Ctrl+O, Enter; leave: Ctrl+X)
  cat .env      # only read
  ```

- **File manager:** switch on "show hidden files" (usually `Ctrl+H`), then open
  `.env`.
- **Windows Notepad:** *File → Open*, paste the full path (for example
  `C:\gpuharbor\.env`), then Open.

Find the line `GPUHARBOR_ADMIN_PASSWORD=...`. Everything after the `=` is your
login password. Keep this file private; it also holds the RunPod key and the
control tokens.

## Set the RunPod API key

Create a key in the RunPod console under **Settings → API Keys**, then:

```bash
./scripts/set-runpod-key
```

The input is hidden, so the key stays out of your shell history, and only that
one line in `.env` is replaced. The controller is restarted afterwards. Press
**Check availability** in the dashboard to confirm it works; that call is free
and read-only.

## Reach it from another device

Only `127.0.0.1` is bound by default. To use the dashboard from a laptop or
phone, add the address you type in the browser and listen on your network:

```bash
./scripts/add-host 192.0.2.10 --bind-ip 0.0.0.0
docker compose up -d   # HTTPS: use ./scripts/install --bind-ip 0.0.0.0 --https 192.0.2.10 instead
```

Then open `https://192.0.2.10:8443` (or `http://192.0.2.10:8080` if you installed with `--no-https`). `192.0.2.10` is the documentation example
address from RFC 5737, not a real address — replace it with your own LAN or VPN
address. `add-host` keeps every
existing entry in `GPUHARBOR_TRUSTED_HOSTS` and adds the new one. To allow more
devices later, just repeat it:

```bash
grep GPUHARBOR_TRUSTED_HOSTS .env           # list what is allowed
./scripts/add-host 192.168.1.5 100.64.0.7   # add more
docker compose up -d
```

The address must match exactly what the browser sends. `--bind-ip 0.0.0.0` binds
every interface; a single LAN or VPN address also works.

Keep this on a trusted LAN or a VPN such as Tailscale or WireGuard. Plain HTTP
with a password does not belong on the public internet, so do not forward the
port on your router.

If you see `Invalid host header`, the address is missing from
`GPUHARBOR_TRUSTED_HOSTS` in `.env`.

## HTTPS

HTTPS is on by default: `./scripts/install` creates a local certificate authority
under `tls/` and starts an nginx TLS proxy, so the dashboard is at
`https://localhost:8443`. Open WebUI (`--webui`) is on `:8444`, OpenHands
(`--openhands`) on `:8445`. Your browser warns until you trust
`tls/local-ca.crt`; [TLS.md](TLS.md) shows how for each browser and OS.

```bash
./scripts/install --bind-ip 0.0.0.0 --https 192.0.2.10 --tls-port 9443   # other devices
./scripts/install --no-https                                             # plain HTTP, localhost only
```

Use your own address instead of `192.0.2.10`. If port 8443 is taken, set
`TLS_PORT`. The installer records the chosen stack in `COMPOSE_FILE` inside
`.env`, so a plain `docker compose up -d` keeps using it.

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
