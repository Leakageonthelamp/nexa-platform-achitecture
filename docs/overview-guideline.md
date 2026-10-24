# System overview — guideline

**v1 · 2026-10-19.** (Paths updated 2026-10-24 for the v3 repo layout. The rules are unchanged.) This file is the rulebook for a system overview: one draw.io page of a single domain. It shows what the domain does, who touches each feature, whether that touch waits or travels by Kafka, and which technology was chosen for that feature.

- **Reference file:** [`domains/wallet/wallet-overview.drawio`](../domains/wallet/wallet-overview.drawio). Copy its shapes and styles. Don't invent a new look.
- **This is not an SHLD.** An SHLD is the page for a manager. The SHLD guideline is not in this repo yet (earlier text linked a `SHLD-guideline.md` that was never committed). An overview may name gRPC, Kafka, and Aurora. An SHLD may not. An overview does not replace the SHLD, the HLD, or the LLD.
- **If this file and an HLD disagree on facts,** `architecture.md` wins, then [`kafka-topics.md`](kafka-topics.md), then the domain's `description.md`, then the HLD. The page never shows a cache, a bucket, a topic, or a vendor those files do not name.

---

## 1. What the page answers

A reader who has not seen the HLD can answer these from the page alone:

1. What is this domain, in one sentence?
2. What are its few features?
3. Who acts on each feature, and do they wait for an answer or send a message?
4. Which technology was chosen for that feature?
5. Which infrastructure does this domain actually contract with?

Four feature cards is the target. Three is fine. Five is too many: merge two.

---

## 2. Look

White page, **1600** wide, Arial, no shadow. Hairline borders. One ink colour. Copy these from the reference; don't pick new ones.

| Role | Fill | Stroke | Text |
| --- | --- | --- | --- |
| Page | `#FFFFFF` | — | — |
| Card | `#FFFFFF` | `#E6E8EC` | `#1A1A1A` name, `#4B5563` bullets |
| Contact line on a card | — | — | `#1E3F73`, 12px |
| Tech chip | `#F4F7FB` | `#E6E8EC` | `#1A1A1A`, 12px bold |
| Shared bar | `#FAFBFC` | `#E6E8EC` | — |
| Muted line (Not here, footer) | — | — | `#6B7280` / `#C5CAD1` |
| Solid arrow | — | `#B0B7C0`, 1.25px | label `#4B5563` on white |
| Kafka arrow | — | `#1E3F73`, dashed `6 4` | same label style |

Corners stay small (`absoluteArcSize=1`, `arcSize=12` on cards, `8` on chips). No grey header band, no drop shadow, no rainbow, no second row of tiny icons under a card.

---

## 3. Top to bottom

Keep this order. The reference file has the spacing; copy the page and move blocks rather than inventing a new grid.

1. **Title.** The words `System overview`. 28px bold.
2. **Subtitle.** One sentence: what this domain is, in plain words.
3. **Legend, one line.** `Solid line · another domain asks and waits. Dashed line · Kafka.` Nothing else. No icon key.
4. **Four feature cards**, left to right.
5. **The shared bar.** The one thing every feature reads or writes. Name it, and put the one rule a reader must remember on the second line.
6. **The neighbours.** The other domains that ask, and the one place a Kafka message goes out. The nightly check, when the domain has one, sits here and is labelled `inside Wallet` (or the equivalent: it is not another domain).
7. **Infrastructure.** Only the contracts that exist. See §7.
8. **Not here.** One grey line: what a reader might expect, and who owns it. Include a caller that never reaches this domain, when that is a real rule.
9. **Footer.** `Tryout · system overview · YYYY-MM-DD`.

---

## 4. A feature card

Left to right in the header: a 28px mark, the feature name, and a **tech chip** on the right (icon 16×16, then the technology name).

Under the header, two blocks:

1. **Contact line**, navy, one short clause. Who acts, and whether they ask or a message arrives. Examples: `Payments asks`, `Kafka from Payments`, `Customer service asks`, `Customers read`.
2. **Bullet list** of what the feature does. About four bullets. Each bullet is one short line. Use a real list (`ul` / `li`), not a paragraph and not a row of commas.

The chip is the technology **for this feature**, not the stack of the whole service. A feature that waits uses gRPC. A feature that is a message uses Kafka. Don't put both on the chip. If a neighbour both asks and sends a message, the card that waits gets gRPC, the card that is the message gets Kafka, and the neighbour box shows the one that matches its arrow.

---

## 5. Lines

| Line | Means | Direction |
| --- | --- | --- |
| Solid, both ends | Another domain asks and waits | Between the shared bar and that domain |
| Dashed, one arrowhead, navy | Kafka | The arrowhead points the way the message travels. A consume points **into** this domain. A publish points **out**. |
| Solid, no label | A feature reads or writes the shared bar | From the feature card down to the bar |

Every cross-domain line has a short label on a white background: `asks`, `Kafka`, `inside <domain>`. The label matches the arrow.

A line from this domain toward a neighbour does not mean "they told us." Check the HLD before drawing the arrowhead.

---

## 6. Technology chips

Use the smallest true label. Copy the icon from the reference file instead of drawing a new one.

| The sources say | Chip | Copy the icon from |
| --- | --- | --- |
| The caller waits for the answer (gRPC) | `gRPC` | `tech-spend-ico` in the reference |
| A message is produced or consumed (Kafka) | `Kafka` | `infra-kafka-logo` |
| The state is stored (Aurora PostgreSQL) | the logo sits on the shared bar, not a chip on every card | `infra-pg-logo` |
| A check inside the service, on a schedule, not a separate product | `Daily job` | no vendor logo; the card's own mark is enough |

Do not add a chip for a technology the domain does not use. Wallet has no Valkey and no S3. The next domain might. Read its HLD before adding a cache or a bucket.

Go is the language of the service. It is not a chip on a feature.

---

## 7. Infrastructure

A row under the neighbours, labelled `Infrastructure`. One card per real contract. Two is the usual count. A third needs a sentence in the HLD that names it.

Each card:

- The logo is **30×30**, **16px** from the left edge, vertically centred.
- The name is bold. One grey line says what the contract is. `The ledger is stored here.` `The dashed lines run on this.`
- The label starts after the logo (`spacingLeft` 62 when the logo is 30px and the gap is 16px).

Copy the logo data URI from a diagram that already has it. Do not redraw it, and do not link out to a website.

| Logo | File | Cell |
| --- | --- | --- |
| PostgreSQL (use this for Aurora PostgreSQL) | `domains/admin-and-partner/admin-partner-hld.drawio` | `n50` |
| Apache Kafka | `domains/brand-and-store/brand-store-hld.drawio` | `n46` |

More logos, when a later domain needs them, were meant to be listed in an SHLD guideline §7. That guideline is not in this repo yet. Until it is, copy a logo from any existing diagram that already has it.

In the draw.io style string the image is `image=data:image/svg+xml,<base64>` or `image=data:image/png,<base64>`. There is no `;base64` in the middle. A semicolon ends the style, and the logo disappears.

No Ack pill. This page is not a consume flow. The Kafka logo on the Kafka card is the logo the page owes Kafka.

---

## 8. Words

Plain English. Short lines.

No service name, topic name, method name, header name, or table name. `customer-bff` stays `Customers`. `payment.events` stays `Kafka from Payments`. `Hold` may stay when it is the business word the HLD uses for a card hold.

The chip is allowed to say `gRPC`, `Kafka`, `Aurora PostgreSQL`, or `Daily job`. That is the point of the chip.

The subtitle is one sentence. The Not-here line is one sentence.

---

## 9. How to make the next one

1. Read `architecture.md`, then `kafka-topics.md`, then the domain `description.md`, then the HLD and the LLD. Do not read the overview page or the HLD script for the words. Write them into `domain-overview.md`: four features, the contact for each, the technology for each, the Kafka direction from the HLD edges, the infrastructure, and one Not-here line. Each feature names the HLD door and the LLD pages it absorbed.
2. Copy `domains/wallet/wallet-overview.drawio` to `domains/<domain>/<domain>-overview.drawio`. Change the diagram `id` and `name`. Keep the styles.
3. Replace the words from `domain-overview.md`. Keep the bullet lists as lists. Point each Kafka arrow the way the HLD edge travels.
4. Delete an infrastructure card the domain does not contract with. Add one only when the HLD names it, and copy its logo from §7.
5. Export a PNG and read it. Fix a clipped bullet, a chip sitting on a title, a logo sitting on text, and an arrow that crosses a card. Don't commit the PNG.
6. In the domain `description.md`, under `## Diagrams`, add `**Overview** — \`<file>\`` and two lines: what the page shows, and that it is not a replacement for the SHLD.

---

## 10. Editing the file

- Replace a whole `y="340"` with `y="356"`. Do not write the new number in front of the old one. `y="356340"` pushes the shape off the page and the export never finishes.
- A logo's `image=` value contains no extra semicolon. See §7.
- Shift a whole band together (the shared bar, the neighbours, the infrastructure, the footer) when a card grows. Leave the gaps that the arrows use.

---

## 11. Checklist

- [ ] Four questions in §1 are answered without the HLD open. The fifth too, when the domain has infrastructure.
- [ ] Four feature cards, each with a contact line, a bullet list, and one tech chip.
- [ ] Solid means a domain asks and waits. Dashed means Kafka, and the arrowhead points the way the message goes.
- [ ] Every cross-domain line is labelled.
- [ ] Infrastructure cards are only real contracts, each with a copied logo.
- [ ] No service, topic, method, or table name. The chip names are the exception.
- [ ] No shadow, no rainbow, no icon key, no Ack pill.
- [ ] PNG checked by eye. `description.md` mentions the file.

---

## 12. Worked example — Wallet

Reference: [`domains/wallet/wallet-overview.drawio`](../domains/wallet/wallet-overview.drawio).

| Feature | Contact | Technology | What the bullets say |
| --- | --- | --- | --- |
| Spend | Payments asks | gRPC | Hold, spend when the kitchen accepts, release on reject or timeout, refund onto the balance |
| Top up | Kafka from Payments | Kafka | Pay by card, the charge stays in Payments, credit after capture, ready straight away |
| Correct | Customer service asks | gRPC | Service only, credit or debit, a reason, only up to their limit |
| Look up | Customers read | gRPC | Own balance, own history, a shopper never writes, one wallet per brand |

The shared bar is **The ledger**. The rule on it is `available = balance − held`. The PostgreSQL logo sits on that bar because Aurora is where it is stored.

| Neighbour | Line | Label |
| --- | --- | --- |
| Payments | Solid, both ends | `asks` (hold, capture, release, refund) |
| Payments | Dashed, into the ledger | `Kafka` (a captured top-up) |
| Notifications | Dashed, out | `Kafka` (top-up, correction, or refund) |
| Nightly check | Solid, one way | `inside Wallet`, chip `Daily job` |

Infrastructure: **Aurora PostgreSQL** (the ledger is stored here) and **Kafka** (the dashed lines run on this). Nothing else. Orders do not call Wallet. That fact is on the Not-here line, with the card charge, the tax invoice, loyalty points, and the checkout timeout.
