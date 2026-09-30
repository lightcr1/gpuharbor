# PI coding agent (optional)

[PI](https://pi.dev) runs on your computer, not in the GPUHarbor stack, so GPUHarbor
cannot configure it from the inside the way it does for OpenHands. One script does it
for you instead.

## Connect

`./scripts/install --pi` (or the question in `./scripts/setup`) does this for you and
checks that PI is installed. To do it by hand, start GPUHarbor, then:

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

If PI reports a certificate error over HTTPS, start it with
`NODE_EXTRA_CA_CERTS=<GPUHarbor folder>/tls/local-ca.crt pi` (Node does not use the
system certificate store the way `./scripts/trust-ca` sets it up).

## What it changes, and what it does not

- Only `providers.gpuharbor` is written. Other providers and settings in `models.json`
  stay as they are, a `models.json.bak` is made first, and a file that is not valid
  JSON is never overwritten.
- The inference token is stored in `models.json` (mode 600, like PI's own `auth.json`).
  If you change `MODEL_ACCESS_TOKEN`, run the script again. With `--token-from-env`
  the token is not copied: PI runs a small command that reads it from GPUHarbor's
  `.env` on every request (about 70 ms), which breaks if you move the GPUHarbor folder.
- Only the model-only inference token is used. It cannot start, stop or delete pods.
  The control token and the RunPod key never reach PI.
- The script refuses plain `http://` to anything but this machine. For another machine
  use HTTPS ([TLS.md](../TLS.md)); if the certificate is not trusted, run
  `./scripts/trust-ca`.
- Requests use the classic `system` role and `max_tokens`, without `reasoning_effort`,
  because vLLM and llama.cpp do not know the hosted-provider variants.

## Optional: /modelinfo

The script asks whether to add a `/modelinfo` command (default: no). Or use
`--with-modelinfo` / `--no-modelinfo`. It is one small file,
`~/.pi/agent/extensions/gpuharbor-modelinfo.ts`, that shows which model GPUHarbor is
running: name, repository, runtime, context, GPU, and a note if the model selected in PI
is not the one running. It only works while a GPUHarbor model is selected in PI; with
any other model it says so and does nothing. PI cannot hide a command, so it stays in the
command list. `--remove` deletes the file again, and a file with that name that this
script did not create is never touched. It asks GPUHarbor via `GET /api/running-model`
(inference token only, no pod ID or account details).

## Tools

PI sends its tools (read, bash, edit, write) with every request. On vLLM this needs a
profile with tool-call parsing (`enable_auto_tool_choice`); the script prints a note for
vLLM profiles without it.

## Limits

PI can run commands and change files with your user's rights. Use it in a dedicated
workspace with no `.env` files or SSH keys within reach, and review what it changes.
The served name in PI (for example `default`) must belong to the model that is
running, the same as in OpenHands.
