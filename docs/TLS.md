# Local TLS reverse proxy

The base stack binds the controller to localhost HTTP. For LAN/VPN access, use
the optional TLS overlay instead of exposing port 8080 publicly.

## Create a local certificate

```bash
./scripts/generate-local-tls 192.0.2.10
```

Use the real LAN/VPN IP or DNS name. Keep `tls/local-ca.key` private and never
commit the `tls/` directory. Import only `tls/local-ca.crt` into clients that
should trust this local deployment.

Set the matching host and secure-cookie options in `.env`:

```env
HOST_BIND_IP=127.0.0.1
TLS_BIND_IP=192.0.2.10
GPUHARBOR_TRUSTED_HOSTS=localhost,127.0.0.1,192.0.2.10
GPUHARBOR_COOKIE_SECURE=true
```

Start:

```bash
docker compose -f compose.yml -f compose.tls.yml up -d --build
```

Open `https://192.0.2.10:8443`. Do not expose this directly to the internet;
prefer Tailscale, WireGuard or another authenticated VPN. The HTTP controller
port remains bound to localhost for local administration.

For public-domain deployments, use a trusted ACME certificate and a dedicated
reverse proxy instead of the local CA.
