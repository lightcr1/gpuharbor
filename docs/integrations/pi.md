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

It installs a small extension (`~/.pi/agent/extensions/gpuharbor.ts`) and a settings file
(`~/.pi/agent/gpuharbor.json`). When PI starts, the extension asks GPUHarbor which
models run and lists them as the provider `gpuharbor`, each with its own name, context
size and output limit. Pick one with `/model`, or
`pi --provider gpuharbor --model <served name>`. If several models run, PI lists all of
them; if none runs, it lists none.

The list is read when PI starts or reloads (`/reload`). After you switch the model in
GPUHarbor, reload PI.

```bash
./scripts/connect-pi --dry-run      # show what would be written, change nothing
./scripts/connect-pi --remove       # take it out again
./scripts/connect-pi --url https://192.0.2.10:8443   # GPUHarbor on another machine
```

Run it again if you change `MODEL_ACCESS_TOKEN`.

PI runs on the same computer, so the script uses GPUHarbor's local port
`http://127.0.0.1:8080`. With HTTPS that port is reachable from this machine only, and no
certificate is involved. For GPUHarbor on another machine use
`--url https://<host>:<port>` and start PI with
`NODE_EXTRA_CA_CERTS=<GPUHarbor folder>/tls/local-ca.crt` (Node ignores the system
certificate store that `./scripts/trust-ca` fills).

## /modelinfo

The extension adds `/modelinfo`: name, repository, runtime, context and GPU of the
running model, and a note if the model selected in PI is not the one running. It only
works while a GPUHarbor model is selected in PI; with any other model it says so and does
nothing. PI cannot hide a command, so it stays in the command list.

## What it changes, and what it does not

- Two files in PI's agent folder are written: the extension and `gpuharbor.json`.
  `models.json` and your other providers are not touched. An entry `gpuharbor` left in
  `models.json` by an earlier version is moved out (with a backup).
- The inference token is stored in `gpuharbor.json` (mode 600, like PI's own `auth.json`).
  With `--token-from-env` it is not copied: PI runs a small command that reads it from
  GPUHarbor's `.env` on every request (about 70 ms), which breaks if you move the
  GPUHarbor folder.
- Only the model-only inference token is used. It cannot start, stop or delete pods.
  The control token and the RunPod key never reach PI.
- The script refuses plain `http://` to anything but this machine.
- `--remove` deletes the extension and settings. A file with the same name that this
  script did not create is never touched or overwritten.
- Requests use the classic `system` role and `max_tokens`, without `reasoning_effort`,
  because vLLM and llama.cpp do not know the hosted-provider variants.

## Tools

PI sends its tools (read, bash, edit, write) with every request. On vLLM this needs a
profile with tool-call parsing (`enable_auto_tool_choice`); `/modelinfo` says when it is
off.

## Limits

PI can run commands and change files with your user's rights. Use it in a dedicated
workspace with no `.env` files or SSH keys within reach, and review what it changes.
