# Platform overview

One shared platform runs every brand, from the menu to the doorstep. The picture of what is being built for a manager is the SHLD (not yet drawn). This folder also has a system overview for the technical reading of that same platform.

## Diagrams

**Overview** — `mfg-eplatform-overview.drawio`

`domain-overview.md` is the plain reading of the platform HLD, checked against the rulebook. There is no platform LLD. Read that instead of the overview page.

Sign in, checkout, the kitchen and the rider, and telling the customer. A solid line is someone asking. A dashed line is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**SHLD** — `mfg-eplatform-shld.drawio` *(not yet drawn: this file is not in the repo)*

Who uses the platform, what it can do, who it depends on, and how one order runs.

**HLD** — `mfg-eplatform-hld.drawio`

The container picture: four edges, two adapters, the twelve topics, and one schema per domain. [`architecture.md`](../../docs/architecture.md) wins where they disagree.
