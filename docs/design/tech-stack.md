# Tech stack

**Status: first draft, design phase.** Nothing here is final. It records what the owner has decided, what DevOps owns, and what is still open. Rules that bind the design stay in [`architecture.md`](../architecture.md); this file explains the stack choices behind them.

Labels used in this file:

- **Decided** — the owner said so on 2026-10-24.
- **Verified** — checked against the official source linked next to it, on 2026-10-24.
- **To verify** — not checked yet. Do not rely on it.
- **Assumption** — a working guess the owner can replace.

---

## 1. What is fixed and what is open

| Layer | Choice | Status | Who runs it |
| --- | --- | --- | --- |
| CDN, WAF, TLS | Cloudflare | Decided (core infra fixed by DevOps) | DevOps |
| API gateway, policy point | Kong | Decided (core infra fixed by DevOps) | DevOps |
| Compute | EKS (Kubernetes on AWS) | Decided (core infra fixed by DevOps) | DevOps |
| System of record | Aurora PostgreSQL | Decided (core infra fixed by DevOps) | DevOps |
| Cache and short-lived state | ElastiCache Valkey | Decided (core infra fixed by DevOps) | DevOps |
| Files | S3 | Decided (core infra fixed by DevOps) | DevOps |
| Secrets and signing keys | Vault | Decided (core infra fixed by DevOps) | DevOps |
| Event backbone | Confluent Cloud (Kafka and Schema Registry) | Decided; event-driven design is a requirement | DevOps |
| Logs, metrics, traces | CloudWatch and OpenTelemetry | Decided (core infra fixed by DevOps) | DevOps |
| Order payload log | MongoDB Atlas on AWS | Likely. **To confirm with DevOps** (see [`order-payload-log.md`](order-payload-log.md)) | DevOps, to confirm |
| Edge apps (BFFs, adapters) | Bun and Elysia v2, REST only | Decided | Our teams |
| Core apps (domains) | Go, hexagonal structure | Decided | Our teams |
| Edge and core boilerplates | owner's draft repos | Not shared yet. **Align with the boilerplate when shared** | Our teams |

Rules for new tools:

- Infrastructure stays on AWS as much as we can. DevOps owns it and builds it.
- A new tool may be non-AWS when it is clearly better. Confluent Cloud, Cloudflare and MongoDB Atlas are already vendor services that run on or in front of AWS, so "off AWS" is not a new idea here.
- A new tool needs a row in [`architecture.md` §13](../architecture.md#13-decision-register) with a reason and a cost, and a named owner on the DevOps side.

### What we ask DevOps for

| Request | Why | Status |
| --- | --- | --- |
| Kafka topics and Schema Registry subjects created from the registry in [`kafka-topics.md`](../kafka-topics.md) | the registry is the only topic list | **To confirm** how topics are created (IaC, or by request) |
| A MongoDB Atlas project on AWS with private connectivity | the order payload log | **To confirm** |
| An insert-only Mongo role for writers and a read role for Cart & Order | least privilege for the log | **To confirm** |
| Valkey, Aurora, and S3 as already drawn | unchanged | Fixed |

---

## 2. Edge: Bun and Elysia v2

### What was verified

Sources are official Elysia pages read on 2026-10-24.

| Fact | Source |
| --- | --- |
| Elysia 2 is a complete rewrite. The beta was published 30 Jul 2026 and the **release candidate (RC) on 19 Oct 2026**. | [Elysia 2 beta](https://elysiajs.com/blog/elysia-20), [Elysia 2 RC](https://next.elysiajs.com/blog/elysia-20-rc/) |
| The RC post says the team is "quite confident that Elysia 2 RC is stable and ready for production" and recommends new projects start on it. It is still an RC, not a final release. | [Elysia 2 RC](https://next.elysiajs.com/blog/elysia-20-rc/) |
| Install for the RC: `bun add elysia@rc`. Migration from 1.4: `bunx @elysia/codemod@latest`. | [Elysia 2 RC](https://next.elysiajs.com/blog/elysia-20-rc/) |
| Lifecycle hooks keep their original `on` names again (the beta had dropped them). The two-parameter `onError` form is a breaking change. | [Elysia 2 RC](https://next.elysiajs.com/blog/elysia-20-rc/) |
| Route signature is hook first, handler last: `.post('/', { body: ... }, handler)`. The codemod rewrites `get(path, handler, hook)` to `get(path, hook, handler)`. | [Elysia 2 beta](https://elysiajs.com/blog/elysia-20), [codemod README](https://cdn.jsdelivr.net/npm/@elysia/codemod@2.0.0-rc.0/README.md) |
| The Elysia 2 beta notes say errors use RFC 9457 problem details with `application/problem+json`. | [Elysia 2 beta](https://elysiajs.com/blog/elysia-20) |
| WebSocket is opt-in: `.use(websocket())` from `elysia/websocket`. | [Elysia 2 beta](https://elysiajs.com/blog/elysia-20) |
| Type inference now covers error responses, so the OpenAPI output lists the errors a route can return. | [Elysia 2 RC](https://next.elysiajs.com/blog/elysia-20-rc/) |
| The OpenAPI plugin is `@elysia/openapi` (docs show `bun add @elysia/openapi@next`). It serves a UI at `/openapi` and the raw spec at `/openapi/json`; both paths are configurable. | [OpenAPI plugin](https://next.elysiajs.com/plugins/openapi) |
| An ahead-of-time (AOT) build plugin is available for Bun.build, Vite, esbuild and others. Elysia runs on Node.js through an adapter (`@elysia/node`, built on `srvx` and `crossws`). | [Elysia 2 beta](https://elysiajs.com/blog/elysia-20) |
| Elysia 2 trims memory and startup time. The posts say not to expect much higher throughput. | [Elysia 2 beta](https://elysiajs.com/blog/elysia-20) |

### What this means for us

| Point | Note |
| --- | --- |
| Version | Elysia 2 is an RC today. Pin an exact version in the lockfile. **To verify:** when the final release ships, and whether the npm default tag has moved off 1.4.x (an npm page read the same day, possibly cached, still showed 1.4.30). Open item O-34. |
| Error body | [`architecture.md` §4](../architecture.md#grpc-contract) sets the HTTP error body to `{ "code", "message", "trace_id" }`. Elysia 2 may default to RFC 9457. We keep our own shape as the rule and map it in one error handler. **To verify** in the RC docs how to override the default, and whether the RC still defaults to problem details. |
| Plugins | The `@elysia` npm scope holds the official plugins for Elysia 1.4 and later (beta notes). Check every plugin we use against the RC before adopting it. **To verify** per plugin. |
| Anything not in the table above | Do not assume it. Mark it **To verify** in the design and check the docs first. |

### REST only, for now

- The edge API is REST over HTTPS with JSON. No GraphQL.
- Behind the edge nothing changes: BFF to domain is gRPC ([`architecture.md` §4](../architecture.md#4-interaction-rules)).
- One OpenAPI document per BFF is generated from the route schemas. It is a build artifact that CI diffs, so a breaking API change is visible in review. **To verify:** the exact CI diff tool (the team picks one).

### AI-ready edge

An AI assistant will be added later. [`architecture.md`](../architecture.md) already fixes the main rule in P-34: the AI owns no state and writes only through `UpdateCart`. The edge needs a few things so the AI can use the API safely. Keep this list short and build only what has a named user.

| Need | What it means | Status |
| --- | --- | --- |
| Stable contracts | One OpenAPI document per BFF, versioned, with a CI diff that fails on a breaking change. | Proposed |
| Tool-friendly operations | Small, single-purpose operations with clear names, typed errors, and an `idempotency_key` on every write (P-01). | Proposed |
| Scoped tokens | An AI call carries a token that names the customer and the allowed operations (for example read menu, read order history, `UpdateCart`). It cannot place an order or pay. | Proposed. Identity model: open item O-35 |
| Audit | Every AI write has an audit row that says it came from the assistant, with the prompt id. Same transaction as the change (audit rule in §8). | Proposed |
| No new state | The AI keeps no cart, menu or price of its own (P-34). Its context window is not a data store. | Decided (P-34) |
| Rate limits | A separate token bucket for assistant traffic at Kong, so it cannot starve the shopper path. | Proposed |

Which model, vendor and host the assistant uses is O-24. It is not decided here.

### Hexagonal shape for the edge (outline)

The edge is thin, so hexagonal here means one rule: routes never call a gRPC client or a vendor SDK directly.

```text
src/
  routes/        inbound adapter: Elysia routes, schemas, auth headers from Kong
  app/           use cases for this BFF or adapter
  ports/         interfaces: domain client, event publisher, payload logger
  clients/       outbound adapters: gRPC clients, Kafka producer
  mappers/       vendor payload <-> canonical command (partner-adapter, webhook-adapter)
```

**Align with the boilerplate when shared.** Names above are placeholders.

---

## 3. Core: Go with a hexagonal structure

Hexagonal means ports and adapters. The domain does not know about gRPC, Kafka, Postgres or a vendor. Adapters plug into ports. This is what lets us swap a POS vendor, run a legacy system behind the same port, and add the Mongo log without touching business rules.

### Layout (proposed)

```text
cmd/<domain>/main.go        composition root: picks a mode, wires only the adapters that mode needs
internal/<domain>/
  domain/                   entities, value objects, state machines, rules. No imports from the layers below
  app/                      use cases (commands and queries). Owns transaction boundaries
  ports/
    in/                     what callers can ask: use-case interfaces
    out/                    what the domain needs: repositories, outbox, clients of other domains,
                            POS, payment gateway, payload log, clock
  adapters/
    in/grpc/                api mode
    in/kafka/               consumer mode
    in/cron/                cron mode
    out/postgres/           repositories and the outbox table
    out/outbox/             the relay that publishes after commit (worker mode)
    out/grpcclient/         calls to other domains
    out/<vendor>/           one package per external vendor (for example pos/bsl, pos/promise, pos/vivi)
    out/legacy/<system>/    legacy bridge adapters (see legacy-bridge.md)
    out/mongo/              the payload log writer (Cart & Order only)
```

Dependency rule: `adapters` depend on `ports`, `ports` and `app` depend on `domain`, and nothing depends on an adapter. A test of `domain` and `app` needs no database and no broker.

### Mapping onto the existing modes

[`architecture.md` §9](../architecture.md#9-runtime-shape) defines four modes per domain app. They map onto the layout like this:

| Mode | Driving adapter (what starts work) | Uses | Kubernetes workload |
| --- | --- | --- | --- |
| `api` | `adapters/in/grpc` | use cases through `ports/in` | Deployment |
| `consumer` | `adapters/in/kafka` | use cases through `ports/in`, then Ack | Deployment |
| `worker` | the outbox relay in `adapters/out/outbox`, background loops (POS dispatch, gateway call, payload log writer) | `ports/out` | Deployment |
| `cron` | `adapters/in/cron` | use cases through `ports/in` | CronJob, `Forbid`, `Asia/Bangkok` |

One image holds all four. `main.go` starts only the adapters for the chosen mode. Behavior of each mode (health, deadlines, idempotency) stays as written in §5 and §9 of the rulebook.

**Align with the boilerplate when shared.** The owner's Go boilerplate may use other folder names or a different split of `app` and `ports`. When it arrives, the boilerplate wins on names and this file is updated to match. Names of domains, packages (`mfg.<domain>.v1`), topics and the tenant `mfg` do not change.

---

## 4. Other tools

| Tool | Use | Status |
| --- | --- | --- |
| Protobuf and `buf` | contracts for gRPC and Kafka values | Decided (P-04) |
| Confluent Schema Registry | Protobuf, BACKWARD compatible | Decided |
| OpenTelemetry | `traceparent` across gRPC and Kafka. The trace id is also the correlation id of the payload log | Decided |
| MongoDB Go driver | the payload log writer in Cart & Order. **To verify** the driver version against the Atlas cluster version | To verify |
| MongoDB access from Bun | the adapters write capture records. **To verify** the Bun driver choice | To verify |

---

## 5. Open questions for this file

| Id | Question |
| --- | --- |
| O-34 | Elysia 2 final release date, version pin, and the error body (RFC 9457 against our shape). |
| O-35 | AI assistant identity: does it act as the customer with a scoped token, or as a service principal? Which operations are allowed? |
| O-36 | How are Kafka topics, schemas and ACLs created: by DevOps from the registry, or by us? |

Full text is in [`architecture.md` §13](../architecture.md#open--needs-a-business-answer).
