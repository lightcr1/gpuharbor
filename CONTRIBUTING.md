# Contributing

## License of your contribution

By contributing you agree your work is licensed under Apache-2.0. Sign off your
commits (`git commit -s`) to certify the Developer Certificate of Origin. Larger
contributions also need a Contributor License Agreement, so the separate closed
component stays possible. Do not contribute code you cannot license this way.

## Ground rules

1. Never commit `.env`, TLS private keys, tokens, controller state or chat data.
2. Keep `RUNPOD_ALLOW_BILLABLE_ACTIONS=false` in tests and examples.
3. Mock RunPod in tests. Only run a real pod when the maintainer approves the
   cost.
4. Add tests for lifecycle, auth and registry changes.
5. Runtime image changes are security sensitive: pin a digest and document where
   the image comes from.
6. Do not widen the OpenHands workspace boundary or expose services publicly by
   default.
7. Keep business and roadmap-of-paid-features material out of this repository.

## Before you push

```bash
pytest
./scripts/check-compose
```

Or everything at once:

```bash
./scripts/check-local-release
```

The maintainer's local workflow also blocks commits and pushes Monday to Friday
from 07:00 to 18:00 Europe/Zurich. That is an operational habit, not a rule for
other contributors.
