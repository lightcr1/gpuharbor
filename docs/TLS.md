# TLS

The base stack serves plain HTTP on localhost. For LAN or VPN access, use the
TLS overlay.

Easiest path:

```bash
./scripts/setup                    # answer the HTTPS questions
./scripts/install --bind-ip 0.0.0.0 --https 192.0.2.10 --tls-port 9443
```

`192.0.2.10` is the RFC 5737 documentation address — use your own address.

This creates a local certificate authority in `tls/`, sets
`GPUHARBOR_COOKIE_SECURE=true`, starts the overlay and prints the HTTPS URL.
Import `tls/local-ca.crt` on the devices that should trust it.

Manual steps, if you want them:

```bash
./scripts/generate-local-tls 192.0.2.10
```

Use the real LAN or VPN address as the argument. The script deletes the CA key after signing, so a leaked `tls/` folder cannot
issue certificates your devices trust. Run it again to renew the certificate.
Then set the values in `.env`:

```env
HOST_BIND_IP=127.0.0.1
TLS_BIND_IP=192.0.2.10
TLS_PORT=8443
GPUHARBOR_TRUSTED_HOSTS=localhost,127.0.0.1,192.0.2.10
GPUHARBOR_COOKIE_SECURE=true
```

and start it:

```bash
docker compose -f compose.yml -f compose.tls.yml up -d --build
```

Open `https://192.0.2.10:8443`. If 8443 is taken, change `TLS_PORT`.

Keep this off the public internet. Use a VPN, or a real reverse proxy with a
trusted certificate if you need a domain name. The plain HTTP port stays bound to
localhost for local administration.
