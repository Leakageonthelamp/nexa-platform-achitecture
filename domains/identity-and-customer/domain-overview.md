# Identity & Profile — system overview

Plain reading of [`identity-customer-hld.drawio`](identity-customer-hld.drawio) and [`identity-customer-lld.drawio`](identity-customer-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

One account for every brand: the login, the profile, the addresses, and consent. Every caller is waiting, so nothing here is a message.

<!-- ai:anchor:features -->
## Features

### Sign in
- **Contact:** Customers ask
- **Technology:** gRPC
- **From:** HLD Customer API · LLD StartSignIn, VerifyOtp
- A one-time code is sent while the shopper waits
- The code confirms a sign-in, or registers a new account in one commit
- A repeat of the same attempt returns the first result
- Social sign-in is planned, not shipped

### Profile
- **Contact:** Customers ask
- **Technology:** gRPC
- **From:** HLD Customer API and Admin API · LLD JoinBrand, UpdateProfile, DeleteCustomer
- An existing account joins another brand without a second sign-up
- The shopper edits their own profile, addresses, and consent
- Customer service can edit, or close the account
- Closing the account anonymizes it

### Live read
- **Contact:** Notification and Delivery ask
- **Technology:** gRPC
- **From:** HLD Contacts API and Address API · LLD BatchGetContacts and GetAddress
- Contacts and consent, at the moment a message is sent
- The drop-off address, when a rider job is created
- A person with no consent for that purpose is left out
- Nobody keeps a copy

### Signing key
- **Contact:** The edge asks
- **Technology:** HTTP
- **From:** HLD JWKS endpoint
- The public half of the customer signing key
- Used to check a customer token
- Guest and partner apps never call this domain

<!-- ai:anchor:shared -->
## Shared

**The customer** — one account, and a row per brand they have joined

On the bar: the person, the login, brand membership, addresses, contacts, and consent. One commit. Nothing is published.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Customers** — solid, both ends, `asks`. Sign in, join a brand, edit the profile, close the account.
- **Customer service** — solid, both ends, `asks`. A support edit, or a privacy delete.
- **Notification** — solid, both ends, `asks`. Contacts at send time. Identity also asks Notification to deliver the one-time code, because the shopper is waiting.
- **Delivery** — solid, both ends, `asks`. The drop-off address.
- **The edge** — solid, `HTTP`. The public signing key.

Nothing on this page is Kafka. A join is not announced.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — The customer is stored here.
- **Valkey** — The one-time code and the refresh-token family. Never the truth.
- **Vault** — The customer signing key.

No Kafka card. This domain does not publish and does not consume.

<!-- ai:anchor:not-here -->
## Not here

Admin and partner login, message delivery, points, the member card, and stored value. A partner token is rejected on these routes.
