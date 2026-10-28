# Identity & Profile

Identity & Profile is the customer. One Go app holds the Minor ID: the login, the customer signing key, the one-time code, the profile, addresses, contacts, and PDPA consent. One account works in every brand. A brand sees another brand's rows only when the customer has opted in to that sharing.

Every caller is waiting, so every door is gRPC. Kong reads the public half of the customer signing key over HTTP. Notification and Delivery read contacts and the drop-off address live, at the moment they need them. Nobody keeps a copy, and nothing personal is put on the bus.

| | |
| --- | --- |
| **Owns** | The customer, the login, the customer signing key, OTP generate and verify, addresses, contacts, and PDPA consent. |
| **Does not own** | Admin or partner identity, message delivery, points, stored value, or saved cards. |
| **How it is called** | `customer-bff` signs in, joins a brand, and edits the profile. `admin-bff` does a support edit or a PDPA delete, after the grant in `X-Roles`. Notification calls `BatchGetContacts`. Delivery calls `GetAddress`. StartSignIn calls Notification `SendOtp`, because the shopper is waiting. |
| **Kafka** | None. Identity publishes nothing and consumes nothing. A join is not announced; Loyalty learns the customer from `order.events`. |

## v3 additions: Minor ID per brand

Baseline v3 (2026-10-24): one Minor ID works across all brands and can be **enabled or disabled per brand**. A customer may stay in one brand. The profile is shared across brands with PDPA consent. Loyalty and the wallet stay separate per brand (D-11, confirmed). See [`identity-model.md`](../../docs/design/identity-model.md). The HLD and LLD page 3 (`JoinBrand`) do not show the membership status yet (see [`architecture.md` §14](../../docs/architecture.md#14-known-drift)).
## v-next (2026-10-25): guest token for table ordering (proposal)

For postpaid QR table ordering ([`postpaid-table-ordering.md`](../../docs/design/postpaid-table-ordering.md), P-45), Identity would sign a **guest token**: a customer-family JWT with scope `dine_in`, a session and member claim, and a 5-minute life, issued by one new call, `IssueGuestToken`, callable by `guest-bff` only. Identity keeps no guest state and no personal data. A diner who signs in joins the table session with the normal customer token and the brand's membership (D-11, P-40). This extends the meaning of the customer token family and is flagged in the rulebook. The HLD does not show it yet.

## Diagrams

**Overview** — `identity-customer-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Sign in, the profile, closing the account, and a live read of contacts or the address. Every line waits. Nothing here is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**SHLD** — `identity-customer-shld.drawio` *(not yet drawn: this file is not in the repo)*

Who holds a Minor ID, what this domain keeps, and how a customer signs up once and then joins a second brand.

**HLD** — `identity-customer-hld.drawio`

One page: the five doors, the one schema, the tokens, and why there is no command in and no fact out.

**LLD** — `identity-customer-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | StartSignIn |
| 2 | VerifyOtp (sign in or register) |
| 3 | JoinBrand |
| 4 | UpdateProfile |
| 5 | DeleteCustomer |
| 6 | BatchGetContacts and GetAddress |

Address writes, consent writes, and RefreshToken follow the same commit as UpdateProfile. Their pages are still to add.
