# Delivery and Dispatch HLD — presenter script

Source: [`delivery-dispatch-hld.drawio`](delivery-dispatch-hld.drawio). About 15 minutes, then questions. Screen-share the diagram and leave it zoomed out until a section says to zoom.

The sentence on the title is the whole talk: **one port for every fleet, one ledger for the rider.**

This domain publishes `delivery.events` and `payment.requested{payout}`. It consumes `order.events`, `delivery.requested`, `store.changed`, and `payment.events`. The full list lives in [`kafka-topics.md`](../kafka-topics.md). The rules it follows are P-18 to P-29 in the [architecture baseline](../architecture.md).

---

## 0. Open (45 seconds)

Point at the title, then the grey subtitle.

> One Go app. Dispatch and the rider workforce share one schema. A ZEEK account is a config row, so the pool, our own riders, and ZEEKAGG are the same package. Grab Express is the second package. `brand_id` is on every hop. Riders use `brand_id = mfg`, because one pool serves every brand.

Walk the four pills once:

1. Orange — gRPC. Quote, GetQuote, CreateDelivery, the ops calls, and rider admin.
2. Blue — HTTP. ZEEK, Grab Express, and Google Maps, through the port. Not from the internet.
3. Purple — the command in, `delivery.requested`, and the command out, `payment.requested`.
4. Green — the fact out, `delivery.events`, and the facts we consume.

---

## 1. Callers (2 minutes)

Zoom to **1. Callers**. Each caller has a straight line into the door it calls.

> **customer-bff** calls `Quote` and reads the delivery. The shopper waits. A shopper never writes a status.
>
> **Order** calls `GetQuote` at `PlaceOrder`. The fee on the order is the fee we quoted. Dispatch does not start here.
>
> **partner-bff** is FAAS. Same `Quote`, then `CreateDelivery`. An external brand has no kitchen accept, so dispatch starts on this call.
>
> **admin-bff** assigns, cancels, redispatches, marks delivered, and approves a rider. The grant was checked before the call.

> partner-adapter is not in this lane. It does not call us. It checks a signature and publishes a command.

---

## 2. Kafka in (2 minutes)

Zoom to **2. Kafka in**. Four topics, four consume lines, four Acks.

> `order.events`. We act on `accepted` and `cancelled`. Everything else is an Ack with no work. Dispatch starts when the kitchen accepts, not when the order is placed.
>
> `delivery.requested`. One command, three variants: a provider status, a rider sync, and a roster sync. The rider variants carry a ref. They never carry a phone.
>
> `store.changed`. We sync the store out to the provider as a merchant. We do not keep a copy of the store.
>
> `payment.events`. We act on `paid_out` and `payout_failed`. Every other variant is an Ack.

> There is no second command topic. A service does not get two front doors.

---

## 3. The engine (5 minutes)

Zoom to **3. Delivery engine**. Top half is dispatch. Bottom half is the rider workforce. Read the top left to right.

> **Quote** does not call ZEEK. Straight-line distance, Google for the road distance above a threshold, then our fee scheme. The ETA is distance over a configured speed. It firms up when a rider is assigned.
>
> **quotes** holds that answer until it expires. The expiry is still an open question.
>
> **CreateDelivery** is the FAAS door. **Ops** is the admin door. Both write **deliveries**.
>
> **deliveries** has seven states, not the twenty-seven the old system had. An update applies only when its rank is higher. `delivered` and `cancelled` never move. That is the bug where a late status overwrote a delivered order, closed in the state machine instead of in a special case.
>
> **Dispatch worker** is the port. `Create`, `Cancel`, `Assign`, `GetRider`. The dashed box is ZEEK and Grab Express. Swapping the provider later is a new package and a new mapper. The rest of this page does not change.
>
> **Outbox relay** publishes after the commit. One relay, one lock.
>
> **Sweeper** is the no-rider wait. Cancel, try the next provider, or mark it failed. No timer service.

Point at the workforce label.

> Same app. `brand_id = mfg` on riders, shifts, and earnings. A delivery stays on the order's brand.
>
> **order.events** starts dispatch or cancels. **delivery.requested** writes the new status on deliveries. The rider and roster variants upsert their own rows. **store.changed** syncs the merchant.
>
> Follow the delivered status. In the same commit, deliveries writes one trip row on the **earnings ledger**, and the outbox carries `payment.requested`. The payout status lives on that row: sending, then paid or failed when **payment.events** comes back. There is no second payouts table.
>
> **Workforce crons** compare rows still sending with `payment.events`. They do not send money. They also read the shift file and write the HR file to S3. We do not call Humanica.

---

## 4. Facts out (1 minute)

> `delivery.events`: dispatched, rider assigned, picked up, delivered, failed, cancelled. `delivered` carries the timeline, the distance, and the fees. It does not carry a phone or an address.
>
> `payment.requested`, variant `payout`. It leaves with the delivered commit, one per trip. We choose the id. Payment uses it as the transaction id. The brand on a rider payout is `mfg`.

---

## 5. Consumers (1 minute)

> **Order** completes or fails the order. **Notification** messages the shopper from the fact, so we do not also send a notification command. **partner-adapter** posts the FAAS brand callback. **Payment Statement** invoices that brand. **Payment** calls TrueMoney. That box is dashed because it is not our call.

Each of those ends in an Ack. The TrueMoney line does not. It is HTTP, and Payment is the one waiting on it.

---

## 6. Data, decisions, not this domain (2 minutes)

> Aurora holds deliveries, quotes, riders, shifts, earnings, and the outbox. One schema, one role. Amounts are integer satang.
>
> Valkey is not a delivery. S3 holds documents, the shift file, and exports. Vault holds the provider secrets.

Read the bold words in **Decisions**. Stop on three:

> P-18, one port. The cost is that two small places know a provider: a Go package and a Bun mapper.
>
> P-20, seven states. The cost is that the fine steps live on the status log, as timestamps.
>
> P-23, riders are `mfg`. That is an exception to one brand per row, and it is written down because the pool is shared.

Point at the ponytail under the data lane.

> We do not allocate the rider. ZEEK does. The ceiling is that dispatch quality is whatever the provider gives us. The upgrade is our own rider app, added as one more package behind the same port.

**Not this domain**: Order owns the order and the moment it is accepted. Brand and Store owns the zone. Identity owns the address. Payment owns TrueMoney and the FAAS invoice. Notification owns the message. partner-adapter owns the signature.

---

## 7. Close (30 seconds)

> Quote stays local. Dispatch starts when the kitchen accepts. The provider sits behind one port. The rider is a ledger, and Payment moves the money.

Stop talking. Take questions.

---

## If they ask

**Why not call ZEEK for the quote?**
The shopper is waiting. A quote that depends on ZEEK fails when ZEEK is slow. Distance and the fee scheme are ours. The ETA gets precise when a rider is assigned (P-29).

**Why seven states?**
The old fleet service had about twenty-seven, and two of the mappings disagreed with each other. Rank plus a terminal state is what stopped a late pickup from overwriting a delivery. The extra steps are timestamps, so the delivery-time report still has them.

**What if every provider fails?**
The delivery is `failed` and Order hears it. Whether the order is then cancelled and refunded, or handed to CSC, is open (O-14).

**Why is the rider not on the brand?**
One rider pool delivers every brand. Putting a brand on the rider would fork the pool. The delivery row keeps the order's brand, so a report can still split by brand (P-23).

**Where did the Zendesk tickets go?**
They are not a webhook anymore. CSC records the ticket id on an earnings adjust (P-28).

**Can we leave ZEEK?**
Yes, without redrawing this page. A new provider is a Go package that implements the port, a mapper in partner-adapter, and a row in provider config. The ZEEK mark on the diagram is a placeholder until the official asset is dropped in. Grab, Google Maps, and TrueMoney are the real marks.

---

## Appendix — where the legacy system went

Ten repos. Four of them were the same job reached through a queue.

| Legacy | What it actually did | Where it goes |
| --- | --- | --- |
| `mfg-fm-api`, `mfg-fm-webhook-receiver`, `mfg-fm-queue-receiver` | Pick a provider, create the job, track status. Webhooks crossed three processes and were sometimes lost. | This domain. One consumer. The signature check moves to partner-adapter. |
| `mfg-faas-api` | Quote, fee, external create, brand callback, store sync to ZEEK. | Quote, CreateDelivery, store sync. The callback is partner-adapter. The invoice is Payment Statement. |
| `mfg-dm-api`, `mfg-dm-queue`, `mfg-dm-queue-webhook` | Rider HR, roster, payroll, manual assign. Status arrived from fleet and was mapped a second time. | Riders, roster, earnings, the ops calls. The second mapping is deleted. |
| `mfg-dm-fe` | The ops console: stuck orders, assign by phone, payroll. Not a live map. | admin-bff against the ops and rider-admin doors. The live map stays out until a provider gives us positions. |
| `mfg-dm-report-app-api`, `mfg-dm-report-app-job` | Excel reports by reading the driver and fleet databases directly. | The data-lake sink, plus an export file to S3 (P-27). Nothing reads this database to build a report. |

Kept, because a report or an ops screen already depends on it: the status timeline, the distance, the three fees (customer, rider, platform), the rider, the store, and the cancel reason.

Cut, with the cost written on the diagram: the external fleet-priority service, the time-of-day schedule, the twenty-seven states, the Zendesk webhook, the Humanica API, and an allocation engine of our own.
