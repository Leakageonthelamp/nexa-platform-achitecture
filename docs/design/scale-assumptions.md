# Scale and uptime — recommended shape

**Status: RECOMMENDED SHAPE, first draft. Every number in this file is an ASSUMPTION, not a fact and not a measurement.** The business has not answered O-01 to O-03. The numbers exist so the design has a shape to size against. The owner will rewrite them.

How to read it:

- **Assumption** — a working guess the owner replaces.
- **Derived** — computed from assumptions by [`tools/scale-calc.py`](../tools/scale-calc.py). Change the parameters in that script, run it, and paste the new tables here.
- **To confirm** — something DevOps or the business must answer.

Nothing here changes a rule in [`architecture.md`](../architecture.md). O-01, O-02 and O-03 stay **open** until the business answers.

---

## 1. Parameters

These are the inputs. All are assumptions.

| Parameter | Starting value | Meaning |
| --- | --- | --- |
| Peak orders per minute, per brand (`P_b`) | set per brand. The tiers below use totals | The busiest minute of the lunch or dinner peak, for one brand |
| Peak orders per minute, total (`P_t`) | the sum of `P_b`. Tiers: 200, 1,000, 5,000 | Brands peak at the same hours, so no discount for them peaking at different times (conservative) |
| Busiest brand's share | 40% | One brand is much larger than the others |
| Burst factor | 1.5 | The busiest second against the average second of the peak minute |
| Edge requests per order | 40 | Menu, cart reads, `PlaceOrder`, status reads |
| Postgres write transactions per order | 25 | All domains, outbox rows included |
| Kafka records per order | 17 | `order.events` 5, `payment.events` 3, `payment.requested` 2, `order.requested` 4, `delivery.events` 2, `notification.requested` 1 |
| Consumer rate per partition | 100 records per second | One Postgres transaction and one Ack per record |
| Partition headroom | 3 | Spare capacity so a backlog can drain |

---

## 2. Sizing tiers

A tier is a size of the whole platform, not a brand. The platform moves up a tier when the peak total passes the tier's number. Tier names are labels for this file only.

| Tier | Peak orders per minute (total) | Reads as |
| --- | --- | --- |
| S | 200 | a pilot, with one or two brands live |
| M | 1,000 | several brands live |
| L | 5,000 | most brands live, at lunch peak |

### Derived load per tier

| Tier | Peak orders/min (total) | Busiest brand, orders/min | Peak orders/s (with burst) | Edge requests/s | Kafka records/s (all topics) | Postgres write tx/s (all domains) |
| --- | --- | --- | --- | --- | --- | --- |
| S | 200 | 80 | 5 | 200 | 85 | 125 |
| M | 1,000 | 400 | 25 | 1,000 | 425 | 625 |
| L | 5,000 | 2,000 | 125 | 5,000 | 2,125 | 3,125 |

Read the table: at Tier L the assumed peak is 125 orders per second, about 5,000 edge requests per second and about 3,125 Postgres write transactions per second across all domains. These look modest for the chosen stack, but that is **To verify** with DevOps and a load test. The likely risk is not raw volume. It is the hot brand and the lunch peak, per-key ordering, and the sync call chain on `PlaceOrder`.

---

## 3. Latency targets (p99)

All **Assumptions**. They are sized so the `PlaceOrder` chain fits inside one deadline.

| Operation | p99 target | Notes |
| --- | --- | --- |
| `ResolveStore` | 100 ms | a Valkey hit on Brand & Store |
| `GetMenu` | 300 ms | cache hit by menu version |
| `GetCart` and `UpdateCart` | 500 ms | priced live: Catalog `PriceLines` then Voucher `EvaluateBasket` |
| `PlaceOrder` up to `authorize_url` | 2,500 ms | includes the payment gateway call |
| POS ticket accepted | 30 s at p95 | nobody waits. Used to size the sweeper window (O-04) |

### Deadline budget for `PlaceOrder`

A single deadline of **3,000 ms** is set at the BFF and passed down every hop, never reset (P-02). Sequential steps, one example split:

| Step | Budget |
| --- | --- |
| `ResolveStore` | 150 ms |
| `PriceLines` | 300 ms |
| `GetQuote` (delivery only) | 300 ms |
| `EvaluateBasket` | 300 ms |
| `ReserveRedemptions` | 200 ms |
| `CreateTransaction` (gateway) | 1,200 ms |
| commit and response | 150 ms |
| **Sum** | **2,600 ms** |

The 400 ms left is slack. This supports O-02, but the answer is the business's.

| Window | Starting value | Open item |
| --- | --- | --- |
| Payment window (abandoned 3DS or QR) | 15 minutes | O-04 |
| POS answer window | 3 minutes | O-04 |

---

## 4. Availability, RPO and RTO

### Availability targets

**Assumptions**, measured at the BFF for the shopper path (`GetMenu`, `GetCart`, `PlaceOrder`).

| Tier | Shopper path | Admin console | Payload log |
| --- | --- | --- | --- |
| S | 99.5% | 99.5% | best effort, no target |
| M | 99.9% | 99.5% | best effort, no target |
| L | 99.95% | 99.5% | best effort, no target |

| Availability target | Allowed downtime per 30 days |
| --- | --- |
| 99.5% | 216.0 min |
| 99.9% | 43.2 min |
| 99.95% | 21.6 min |
| 99.99% | 4.3 min |

Define "available" before using the numbers. **Assumption:** a request counts as a failure when the BFF returns a 5xx that is not caused by a third party (gateway, POS). The business has not set this definition.

### RPO and RTO

**Assumptions.** What DevOps can deliver with the fixed infrastructure is **To confirm**.

| Tier | RPO (data lost) | RTO (time to recover) | Shape |
| --- | --- | --- | --- |
| S | 5 minutes | 60 minutes | multi-AZ only |
| M | 1 minute | 30 minutes | multi-AZ, tested restore |
| L | 1 minute | 15 minutes | multi-AZ plus a second region. **To confirm** feasibility and cost |

The payload log has no RPO or RTO target. It is best effort ([`order-payload-log.md`](order-payload-log.md)).

---

## 5. Payload log volume

Assumptions: 12 documents per order, 4 KB average after masking, a 90-day TTL, and monthly order counts of 60,000 (S), 400,000 (M) and 2,000,000 (L). The monthly counts are guesses, not forecasts.

| Tier | Orders/month | Docs/month | GB/month | GB held at 90-day TTL |
| --- | --- | --- | --- | --- |
| S | 60,000 | 720,000 | 2.7 | 8.2 |
| M | 400,000 | 4,800,000 | 18.3 | 54.9 |
| L | 2,000,000 | 24,000,000 | 91.6 | 274.7 |

Cluster tier is not chosen here. DevOps and Atlas sizing decide it (O-29).

---

## 6. Kafka partitions: how they follow from the numbers

Rule used: `partitions = max(6, ceil(peak records per second / consumer rate per partition x headroom))`. Partitions can be raised later but not lowered, and raising them changes which partition a key goes to, so ordering for a key breaks across the change. So size for the expected tier, not for today.

| Topic | Registered partitions | Needed at S | Needed at M | Needed at L |
| --- | --- | --- | --- | --- |
| `order.events` | 12 | 6 | 6 | 19 |
| `payment.events` | 12 | 6 | 6 | 12 |
| `payment.requested` | 12 | 6 | 6 | 8 |
| `order.requested` | 12 | 6 | 6 | 15 |
| `delivery.events` | 12 | 6 | 6 | 8 |
| `notification.requested` | 6 | 6 | 6 | 6 |

Reading the table, under these assumptions:

- The registered counts (6, and 12 for `order.*` and `payment.*`) cover Tiers S and M.
- At Tier L, `order.events` (19) and `order.requested` (15) need more than 12. The others fit.
- The compacted topics (`brand.changed`, `store.changed`, `catalog.*`) have low volume and stay at 6.
- The number of consumer pods per topic can never usefully exceed its partition count.

Recommendation for v3: **keep the registered counts** and set a review point when the platform moves from M to L. At that review, raise the 7-day topics while consumers have drained. Compacted topics are not re-partitioned. The counts in [`kafka-topics.md`](../kafka-topics.md) are unchanged in this pass.

---

## 7. What follows for infrastructure

DevOps owns the infrastructure. These are the asks that follow from the shape, as triggers, not as sizes.

| Area | Trigger or rule | Notes |
| --- | --- | --- |
| Aurora | One cluster per environment (P-08). Move Order and Payment to their own cluster when peak write transactions or commit latency pass a threshold. **Assumption:** at Tier L, or when the writer's CPU stays above 60% at peak, whichever comes first | The threshold is a guess. Instance sizes are for DevOps |
| EKS | Replica counts: enough `api` pods that one pod loss at peak stays inside the latency target. At least 3 per critical app, one per AZ (**Assumption**) | Each mode is its own workload |
| Valkey | Sized for the four allowed uses, never for truth (D-04) | Unchanged |
| Kafka | Partition counts as in section 6. Throughput is far below Confluent limits at these numbers (**To verify** against the chosen cluster type) | Cluster type and cost are for DevOps |
| MongoDB | Volume as in section 5 | O-29 |
| Kong rate limits | Set per brand and per route class, with a separate bucket for webhooks and for AI traffic | See [`tech-stack.md`](tech-stack.md#ai-ready-edge) |

---

## 8. How to replace these numbers

1. Get real figures from the business: peak orders per minute per brand (O-01), targets (O-02), recovery goals (O-03).
2. Edit the parameters at the top of [`tools/scale-calc.py`](../tools/scale-calc.py).
3. Run `python3 docs/tools/scale-calc.py` and paste the tables into this file.
4. Replace "Assumption" with the source of the number, and update O-01 to O-03 in [`architecture.md` §13](../architecture.md#open--needs-a-business-answer).
5. Re-check the partition counts and the Aurora trigger.

---

## 9. Open items

| Id | Question | What this file gives |
| --- | --- | --- |
| O-01 | Peak orders per minute, per brand and total | a parameter table and three example tiers |
| O-02 | Availability and p99 for `PlaceOrder` and `GetMenu` | example targets and a deadline budget |
| O-03 | RPO and RTO, multi-AZ only or a second region | example targets per tier |
