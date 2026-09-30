# PI coding agent (optional)

[PI](https://pi.dev) runs on your computer, not in the GPUHarbor stack, so GPUHarbor
cannot configure it from the inside the way it does for OpenHands. One script does it
for you instead.

## Connect

Start GPUHarbor, then:

```bash
./scripts/connect-pi
```

The script adds a provider named `gpuharbor` to PI's `models.json`
(`~/.pi/agent/models.json`), with one entry per enabled model profile. Start the model
in GPUHarbor, then pick it in PI with `/model`, or `pi --provider gpuharbor --model default`.

```bash
./scripts/connect-pi --dry-run      # show the result, change nothing
./scripts/connect-pi --remove       # take the provider out again
./scripts/connect-pi --url https://192.0.2.10:8443   # GPUHarbor on another machine
```

Run it again after you add, edit or delete a model profile.

## What it changes, and what it does not

- Only `providers.gpuharbor` is written. Other providers and settings in `models.json`
  stay as they are, a `models.json.bak` is made first, and a file that is not valid
  JSON is never overwritten.
- The inference token is **not copied** into `models.json`. PI runs a small command that
  reads `MODEL_ACCESS_TOKEN` from GPUHarbor's `.env` each time, so a rotated token
  works without running the script again.
- Only the model-only inference token is used. It cannot start, stop or delete pods.
  The control token and the RunPod key never reach PI.
- The script refuses plain `http://` to anything but this machine. For another machine
  use HTTPS ([TLS.md](../TLS.md)); if the certificate is not trusted, run
  `./scripts/trust-ca`.
- Requests use the classic `system` role and `max_tokens`, without `reasoning_effort`,
  because vLLM and llama.cpp do not know the hosted-provider variants.

## Tools

PI sends its tools (read, bash, edit, write) with every request. That only works with
profiles that parse tool calls (`enable_auto_tool_choice`). The script prints a note
for profiles that do not, and PI's tools will not work with them.

## Limits

PI can run commands and change files with your user's rights. Use it in a dedicated
workspace with no `.env` files or SSH keys within reach, and review what it changes.
The served name in PI (for example `default`) must belong to the model that is
running, the same as in OpenHands.
