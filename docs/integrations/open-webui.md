# Open WebUI (optional)

Open WebUI is not required by GPUHarbor. It connects to GPUHarbor's authenticated,
OpenAI-compatible `/v1` endpoint and stores its own users and conversations.

## Start

1. Set a reviewed, preferably digest-pinned `OPEN_WEBUI_IMAGE` and a random
   `WEBUI_SECRET_KEY` in `.env`.
2. Start the base stack plus the overlay:

```bash
docker compose -f compose.yml -f compose.openwebui.yml up -d --build
```

Open WebUI listens on `http://127.0.0.1:3000` by default. GPUHarbor remains on
`http://127.0.0.1:8080`. Change `HOST_BIND_IP` only for a trusted LAN/VPN; do
not expose either service directly to the public internet.

## Data and removal

Chats and users live in the `open-webui-data` volume. Removing the overlay does
not delete that volume. GPUHarbor model profiles are independent of Open WebUI.
