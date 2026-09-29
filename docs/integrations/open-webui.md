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

## Point it at GPUHarbor

The overlay already configures the connection for you:

- Base URL: `http://controller:8080/v1`
- API key: the value of `MODEL_ACCESS_TOKEN` (passed automatically)

Open `http://127.0.0.1:3000`, then pick the model by its **served name** from the
GPUHarbor profile (for example `chat`). The model pod must be running in GPUHarbor
first; on first start it downloads the weights and takes a few minutes.

Running Open WebUI outside this compose file? Add an OpenAI-compatible connection
manually in **Settings → Connections** with the same base URL and token. If Open
WebUI runs on the host rather than in a container, use
`http://127.0.0.1:8080/v1`.

## Data

Users and chats live in the `open-webui-data` volume. Removing the overlay does
not delete it. Model profiles belong to GPUHarbor and are unaffected.

The license of Open WebUI forbids removing its branding above a small-deployment
exception, so use the upstream image as-is.
