# Admin & Partner HLD — presenter script

Source: [`admin-partner-hld.drawio`](admin-partner-hld.drawio). About 10 minutes, then questions. Screen-share the diagram and leave it zoomed out until a section says to zoom.

The sentence on the title is the whole talk: **login is sync, and the bus is not involved.**

This domain owns no topic. The full list lives in [`kafka-topics.md`](../../docs/kafka-topics.md), and its "What is not a topic" table names the admin topics that were removed.

---

## 0. Open (45 seconds)

Point at the title, then the grey subtitle.

> Two engines in one domain. Admin owns the principal, the grant, and the session. Partner owns the OAuth client.
>
> The caller is always waiting, so nothing here is a topic. The bus never carries a token, a secret, or a client assertion.

Walk the four pills once:

1. Orange — gRPC. Login, grant, and token. The client waits.
2. Blue — JWKS and HTTP. The Kong PEP and Azure AD.
3. Purple — no command. An admin is waiting.
4. Green — no fact. Audit stays in Postgres.

---

## 1. Callers (2 minutes)

Zoom to **1. Callers**.

> Cloudflare, then Kong, the only PEP. `iss` picks the JWKS, the public half of the two Vault keys. A customer `iss` is rejected here. Kong fronts both BFFs. It does not call Azure.
>
> **partner-bff** handles `client_credentials` with `private_key_jwt`. No redirect, and no refresh token.
>
> **Azure AD** keeps admin MFA. The Azure adapter is the only caller. The core never imports the Azure SDK.
>
> **admin-bff** uses auth code plus PKCE with S256, and handles grant, revoke, session, and the partner client.

> No customer token on these routes. Identity owns that key and that world.

---

## 2. Kafka in (30 seconds)

> No Kafka in. Every call on this page has a person or a partner waiting for the result, so it is gRPC.
>
> A grant, a revoke, a rotate, and a login are not commands. Publishing them would put a security event on the bus, and no consumer needs it that cannot read Postgres.

---

## 3. The engines (4 minutes)

Zoom to **3. Admin & Partner**. Left column is Admin, right column is Partner.

> **Admin principal**: IdP subject, email, name. The first login has no grants. There is no `brand_id` on the principal. The grant carries it. **Partner client**: `client_id`, the brands, and the scopes. We store the public key only. No redirect, and no long-lived API key.
>
> **Azure adapter**: one provider, and the port stays. OIDC and SAML are not shipped. It is the only thing that calls Azure. **private_key_jwt**: verify the assertion, then drop it. It is never stored.
>
> **Admin JWT**: `iss=admin`, ES512, short TTL, and `roles[]` is fixed until the next token. **Partner JWT**: `iss=partner`, a different ES512 key, 5 minutes, and no refresh token. The client asks again.
>
> **Refresh family** is the admin session, on the left, in Valkey. Reuse kills the whole family. **Register, rotate, suspend** is gRPC from admin-bff. It writes the client row, and the audit row is in the same transaction. The old public key works until the grace period ends.
>
> **Grant change** is gRPC: assign, revoke, update. It does not rewrite a live JWT. **audit_log** is written in the same transaction as the change. The lake reads Postgres, not the bus.
>
> **Vault** holds two keys: `admin-es512` and `partner-es512`. Neither is the customer key. Kong already has the public half.

Point at the bottom note.

> An admin revoke kills the refresh family and bites at the next refresh. A partner suspend bites on the next token request. Either way a stolen access token can live out its 5 minutes.

---

## 4. Facts out and 5. Consumers (1 minute)

> No facts. A login, a grant, and a token are not domain events. The audit row is the record. Nothing secret is on the bus, because this domain does not publish.
>
> No consumers. Kong does not project a denylist from this domain. There is no fraud worker. A spike in grants is an audit query, not a stream processor.

---

## 6. Data, decisions, not this domain (1 minute)

> One Aurora cluster, with an admin schema and a partner schema. Valkey holds the refresh family, the one-time auth code, and the PKCE verifier. Vault holds the two signing keys.

Read the bold words in **Decisions**: zero topics, no denylist projector, no fraud worker, Azure only, one Aurora with two schemas, no brand on the principal, no partner refresh.

**Not this domain**: Identity owns the customer. Catalog, Order, and Payment trust the headers Kong injected. Break-glass admin is seeded outside this login path. Which partners use this token, rather than `partner-adapter`, is still open (O-09).

---

## 7. Close (30 seconds)

> Every call is sync. Kong is the only PEP. No topic, no Ack, no token on the bus. Audit is Postgres.

Stop talking. Take questions.

---

## If they ask

**How fast does a revoke bite?**
For an admin, at the next refresh. For a partner, on the next token request. In the worst case, the 5-minute access token runs out.

**Why not a denylist in Kong?**
It would need a projector and a topic carrying security events. Five-minute tokens plus a refresh revoke cover it.

**Does a grant change show up immediately?**
On the next token. We do not rewrite one that has already been issued.

**Can a customer token reach admin routes?**
No. Kong picks the JWKS by `iss` and rejects the customer issuer here.

**Does a partner get a refresh token?**
No. `client_credentials` asks again. The refresh family is the admin session.
