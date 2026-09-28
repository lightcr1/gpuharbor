# Contributing

## License of contributions

By contributing you agree that your contribution is licensed under the
Apache-2.0 license of this repository. Sign off every commit
(`git commit -s`) to certify the Developer Certificate of Origin. Substantial
contributions additionally require a Contributor License Agreement so the
project can keep offering a separate closed Pro component. Do not contribute
code you cannot license this way.

GPUHarbor is public. These rules define the contribution flow.

1. Never commit `.env`, TLS private keys, tokens, controller state or chat data.
2. Keep `RUNPOD_ALLOW_BILLABLE_ACTIONS=false` in tests and examples.
3. Use mocked RunPod responses unless the owner explicitly approves a paid canary.
4. Add tests for lifecycle, authentication and registry changes.
5. Run:

```bash
pytest
./scripts/check-compose
```

6. Treat runtime-image changes as security-sensitive. Pin immutable digests and
   document upstream source/license details.
7. Do not weaken the OpenHands workspace boundary or expose services publicly by
   default.
8. Report security issues privately once a contact channel exists.
9. Do not add Pro or business-strategy material to this public repository; it
   belongs in the separate private project.

The local owner workflow also blocks commits and pushes Monday-Friday
07:00-18:00 Europe/Zurich. This scheduling policy is operational rather than a
requirement for future external contributors.
