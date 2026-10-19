# Identity & Profile

Identity & Profile is the customer. One Go app holds the Minor ID: the login, the customer signing key, the one-time code, the profile, addresses, contacts, and PDPA consent. One account works in every brand. A brand sees another brand's rows only when the customer has opted in to that sharing.

Every caller is waiting, so every door is gRPC. Kong reads the public half of the customer signing key over HTTP. Notification and Delivery read contacts and the drop-off address live, at the moment they need them. Nobody keeps a copy, and nothing personal is put on the bus.

| | |
| --- | --- |
| **Owns** | The customer, the login, the customer signing key, OTP generate and verify, addresses, contacts, and PDPA consent. |
| **Does not own** | Admin or partner identity, message delivery, points, stored value, or saved cards. |
| **How it is called** | `customer-bff` signs in, joins a brand, and edits the profile. `admin-bff` does a support edit or a PDPA delete, after the grant in `X-Roles`. Notification calls `BatchGetContacts`. Delivery calls `GetAddress`. StartSignIn calls Notification `SendOtp`, because the shopper is waiting. |
| **Kafka** | None. Identity publishes nothing and consumes nothing. A join is not announced; Loyalty learns the customer from `order.events`. |

## Diagrams

**SHLD** — `identity-customer-shld.drawio`

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
