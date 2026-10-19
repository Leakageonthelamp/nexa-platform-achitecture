# Admin & Partner — system overview

Plain reading of [`admin-partner-hld.drawio`](admin-partner-hld.drawio) and [`admin-partner-lld.drawio`](admin-partner-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

Admin login and partner tokens. The caller is always waiting, so nothing here is a message, and a token never rides the bus.

<!-- ai:anchor:features -->
## Features

### Admin login
- **Contact:** Staff ask
- **Technology:** gRPC
- **From:** HLD Azure adapter and Refresh family · LLD Admin login, Refresh and revoke
- Sign-in goes through the company directory, which keeps the second factor
- A short admin token is signed here
- Refresh rotates the session
- Using an old refresh token twice ends the whole session

### Grants
- **Contact:** Staff ask
- **Technology:** gRPC
- **From:** HLD Grant change · LLD Grant change
- Assign, change, or remove a role for a brand
- The audit row is in the same commit
- A token already issued is not rewritten
- The new role appears on the next token

### Partner token
- **Contact:** Partners ask
- **Technology:** gRPC
- **From:** HLD private_key_jwt and Partner client · LLD Partner token, Register, rotate, or suspend
- The partner signs a short-lived proof with its own key
- Only the public key is kept here
- The token lasts minutes and has no refresh
- Suspending the client bites on the next request

### Company directory
- **Contact:** This domain asks
- **Technology:** HTTP
- **From:** HLD Azure adapter
- Only the admin sign-in calls it
- The customer world never does
- A customer token is rejected at the edge

<!-- ai:anchor:shared -->
## Shared

**The principal and the client** — the admin person, the grant, and the partner client

On the bar: who the admin is, which brands they may touch, and the partner’s public key. The audit row is the record. It is not published.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Staff** — solid, both ends, `asks`. Login, refresh, revoke, and grants.
- **Partners** — solid, both ends, `asks`. A token, or a new public key.
- **Company directory** — solid, `HTTP`. Admin sign-in only.

Nothing on this page is Kafka. There is no nightly check.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — Principals, grants, partner clients, and the audit row.
- **Valkey** — The admin refresh family and the one-time sign-in proof.
- **Vault** — Two signing keys, one for admins and one for partners. Not the customer key.

No Kafka card.

<!-- ai:anchor:not-here -->
## Not here

The customer, the one-time code, and the customer signing key. Other domains trust the headers the edge already set. They do not call here to check a token.
