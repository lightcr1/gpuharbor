## What does this change?

<!-- One or two sentences. -->

## How was it tested?

<!-- e.g. ./scripts/check-local-release, or a manual check on a live pod -->

## Checklist

- [ ] No secrets, `.env` files, TLS keys or controller state in the diff.
- [ ] `RUNPOD_ALLOW_BILLABLE_ACTIONS` is still `false` in examples and tests.
- [ ] RunPod is mocked in tests; no real pod was started without approval.
- [ ] `./scripts/check-local-release` passes.
- [ ] Runtime image changes pin a digest and are documented.
