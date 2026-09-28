# Licensing model

GPUHarbor uses an **open-core** model. This document is the authoritative
description of the intended boundary. It is not legal advice; read the actual
`LICENSE` and `NOTICE` files and obtain legal review before a commercial launch.

## Open core (this repository)

- License: **Apache License 2.0** (`LICENSE`).
- Scope: controller, dashboard, model/runtime registry, single-provider RunPod
  integration, runtime gateway definitions, Compose overlays and documentation.
- You may use, modify and redistribute the core, including commercially, under
  the terms of Apache-2.0.
- Apache-2.0 includes an explicit patent grant and requires preserving license
  and notice information. It does **not** grant rights to the GPUHarbor name or
  logo.

### Honest trade-off

A permissive license means a third party may fork the core, rebrand it, and even
sell it, as long as they comply with Apache-2.0 and do not use our trademarks.
That is the deliberate cost of using a widely trusted license for reach and
adoption. If preventing hosted-service clones becomes more important than
adoption, the alternative would be a network copyleft license such as
AGPL-3.0. That decision can only be revisited while the project still has a
single author or a Contributor License Agreement is in place.

## Pro (not in this repository)

- License: **proprietary / commercial**, delivered under a separate agreement.
- Scope (planned): multiple providers and accounts at once, teams, cost
  overview, budget limits, alerts, usage history, schedules and pod automation.
- The Pro code is **not** published here. Planned multi-provider features are
  designed to live in a separate closed module or service, not behind a flag in
  the open core.

## Why the boundary is code, not a license key

The free tier supports one provider connection at a time. The cleanest way to
express that is architectural: the open core simply ships single-provider
orchestration. Multi-provider orchestration is provided by the Pro component.
This avoids weak "feature unlock" checks that anyone could patch out of an open
source binary, and it keeps the free tier genuinely useful rather than crippled.

## Contributions

- Contributions to the core are accepted under Apache-2.0.
- Because the project may later want to offer a closed Pro component or adjust
  licensing, contributions require a Developer Certificate of Origin sign-off
  (`git commit -s`) and, for substantial contributions, a Contributor License
  Agreement. Do not contribute code you cannot license this way.

## Trademarks and naming

The Apache-2.0 license does not grant permission to use the GPUHarbor name or
logos. A fork must not imply official endorsement or affiliation. A short
trademark policy will be added before the first public release.

## Provider integrations

Third-party provider APIs are used under their own terms. The open core includes
only the RunPod integration. Additional providers are added only when there is
clear demand, and their terms must be reviewed before integration.
