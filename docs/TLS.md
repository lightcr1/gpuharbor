# TLS

HTTPS is the default. `./scripts/install` creates a local certificate authority,
starts an nginx proxy and puts everything behind it:

| Service | HTTPS address | Needs |
|---|---|---|
| Dashboard and `/v1` API | `https://localhost:8443` | always |
| Open WebUI | `https://localhost:8444` | `--webui` |
| OpenHands | `https://localhost:8445` | `--openhands` |

The plain HTTP ports of all services are bound to this machine only, so from the
network only TLS is reachable. Session cookies are marked `Secure`.

```bash
./scripts/install                     # dashboard over HTTPS
./scripts/install --webui             # plus Open WebUI
./scripts/install --bind-ip 0.0.0.0 --https 192.0.2.10 --tls-port 9443
# LAN and VPN at once: both names in the certificate, listen on every interface
./scripts/install --bind-ip 0.0.0.0 --https 192.0.2.10 --tls-name 100.64.0.7 --tls-bind 0.0.0.0
./scripts/install --no-https          # plain HTTP on localhost, for a quick test
```

`192.0.2.10` is the RFC 5737 documentation address, use your own LAN or VPN
address. `localhost`, `127.0.0.1` and `::1` are always in the certificate.

## Trusting the certificate

The certificate is signed by a CA that only exists on your machine, so browsers
warn until you trust `tls/local-ca.crt`. The script deletes the CA key after
signing, so a leaked `tls/` folder cannot issue certificates your devices trust.
Run it again to renew the certificate (valid 825 days).

- **Chrome, Edge, Brave:** Settings → Privacy and security → Security → Manage
  certificates → Authorities → Import `tls/local-ca.crt`, and allow it for
  websites.
- **Firefox:** Settings → Privacy & Security → View Certificates → Authorities →
  Import, tick "Trust this CA to identify websites".
- **Linux system store:** `sudo cp tls/local-ca.crt /usr/local/share/ca-certificates/gpuharbor.crt && sudo update-ca-certificates`
- **macOS:** open the file in Keychain Access, set it to "Always Trust".
- **Windows:** double-click the file → Install Certificate → Local Machine →
  "Trusted Root Certification Authorities".
- **Phones:** send the `.crt` file to the device and install it under
  Settings → Security → Install certificate (only import a CA you created).

## How the stack is selected

The installer writes `COMPOSE_FILE` into `.env`, for example
`compose.yml:compose.tls.yml:compose.openwebui.yml:compose.openwebui.tls.yml`.
That means a plain `docker compose up -d` (also from `set-runpod-key`) always
starts the same stack. You do not have to remember `-f` flags.

## Manual steps

```bash
./scripts/generate-local-tls 192.0.2.10,harbor.lan   # extra names, comma separated
./scripts/init-env --bind-ip 192.0.2.10 --https-host 192.0.2.10 \
    --overlay compose.tls.yml
docker compose up -d --build
```

Ports come from `.env`: `TLS_PORT` (8443), `WEBUI_TLS_PORT` (8444),
`OPENHANDS_TLS_PORT` (8445), bound to `TLS_BIND_IP`.

## Notes

- nginx does not send `Strict-Transport-Security` on purpose. The certificate is
  local, and HSTS would apply to every port of `localhost` and make certificate
  errors impossible to click through. Add it yourself behind a real domain.
- Keep this off the public internet. Use a VPN, or a normal reverse proxy with a
  trusted certificate if you need a domain name.
- Never commit `tls/`. It is in `.gitignore`.
