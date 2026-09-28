# Open WebUI (optional)

Open WebUI is not required. It talks to GPUHarbor's authenticated,
OpenAI-compatible endpoint and keeps its own users and chats.

## Start

Set a reviewed `OPEN_WEBUI_IMAGE` (preferably by digest) and a random
`WEBUI_SECRET_KEY` in `.env`, then:

```bash
docker compose -f compose.yml -f compose.openwebui.yml up -d --build
```

It listens on `http://127.0.0.1:3000` by default; GPUHarbor stays on port 8080.
Only change `HOST_BIND_IP` on a trusted LAN or VPN.

## Data

Users and chats live in the `open-webui-data` volume. Removing the overlay does
not delete it. Model profiles belong to GPUHarbor and are unaffected.

The license of Open WebUI forbids removing its branding above a small-deployment
exception, so use the upstream image as-is.
