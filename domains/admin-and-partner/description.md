# Admin & Partner

Admin & Partner decides who may operate the platform, and which partner may call it. Admin owns the principal, the grant, and the session. Partner owns the OAuth client. Kong is the only place a request is allowed through or stopped. This domain is the only one that calls Azure AD.

Login is synchronous. The caller is always waiting, so nothing here is a Kafka topic. The bus never carries a token, a secret, or a client assertion. The audit row in Postgres is the record.

| | |
| --- | --- |
| **Owns** | Admin principal, role, grant, session, audit. Partner org, OAuth client, scopes, and the partner public key. Two Vault keys: `admin-es512` and `partner-es512`. |
| **Does not own** | The customer, `minor_id`, social login, OTP, or the customer signing key. Those stay in Identity. |
| **How it is called** | Admin login is authorization code + PKCE. A partner token is `client_credentials` + `private_key_jwt`. Both are gRPC. A grant change does not rewrite a live JWT. |
| **Kafka** | None. |

## Diagrams

**Overview** — `admin-partner-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Staff sign-in, grants, a partner token, and client keys. Every line waits. Nothing here is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**SHLD** — `admin-partner-shld.drawio` *(not yet drawn: this file is not in the repo)*

Who may sign in, what this domain grants them, and how a staff sign-in and a partner token work.

**HLD** — `admin-partner-hld.drawio`

One page: callers, the two engines, and why there is no command in and no fact out.

**LLD** — `admin-partner-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | Admin login |
| 2 | Refresh and revoke |
| 3 | Partner token |
| 4 | Grant change |
| 5 | Register, rotate, or suspend a partner client |
