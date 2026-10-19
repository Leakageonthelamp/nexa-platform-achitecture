# Kafka topics

Twelve business topics. Each high-level diagram must use this list and no other topic name.

The rules come from two Confluent notes and from how food-delivery checkouts actually run:

- [Should you put several event types in the same Kafka topic?](https://www.confluent.io/blog/put-several-event-types-kafka-topic/) — events that must stay in order share one topic and one key. Split only when the owner or the throughput differs.
- [Multiple event types in the same topic, revisited](https://www.confluent.io/blog/multiple-event-types-in-the-same-kafka-topic/) — one Protobuf `oneof` per topic, so the subject stays bounded.
- [DoorDash checkout](https://careersatdoordash.com/blog/building-a-more-reliable-checkout-service-with-kotlin/) — the order service keeps the state machine and calls other services over gRPC. Kafka only decouples a step when nobody is waiting on the response.

## Rules

1. Sync when someone is waiting. Admin writes, checkout, pricing, and reads are gRPC. Kafka is for work nobody is waiting on.
2. A topic crosses a service boundary. A service does not publish a topic that only it consumes. Internal work queues are an outbox table plus a worker in the same app.
3. One inbound command topic per domain, named `<domain>.requested`, carrying one `oneof` and keyed by the aggregate id. One fact topic per aggregate. A second fact topic only when the rate is different, which is why sold-out is not on the menu topic.
4. Two fact shapes. Compacted state (`.changed`, `.published`) carries the latest value or a version pointer, so a new consumer does not need a snapshot topic. Lifecycle (`.events`) keeps 7 days.
5. Headers on every record: `event_id`, `event_type`, `brand_id`, `occurred_at`, `version`, `traceparent`. The Kafka key is `brand_id:<aggregate id>`.
6. The app writes a transactional outbox in the same Postgres transaction as the state change. No Debezium. No Kafka Connect cluster.
7. A consumer applies the record only when `version` is newer, then Ack. It retries three times with backoff inside the app, then writes one `<service>.dlq`. There is no per-topic retry topic.
8. The order service is the saga. Its state machine is rows in Postgres. Food is authorized first and captured after the POS accepts the ticket. No Temporal or Cadence in v1.
9. Protobuf, Schema Registry, BACKWARD compatibility. Six partitions, except `order.*` and `payment.*`, which have 12.

`<service>.dlq` is an operational topic, one per consuming service. It is not a business event and it is not drawn as a domain topic.

## Registry

| Topic | Owner | Kind | Key | Retention | Partitions | Producers | Consumers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `brand.changed` | Brand & Store | compacted state | `brand_id` | compact | 6 | Brand & Store | Catalog |
| `store.changed` | Brand & Store | compacted state | `brand_id:store_id` | compact | 6 | Brand & Store | Catalog, Delivery |
| `catalog.requested` | Catalog | command `oneof` | `brand_id:store_id:sku_id` | 7 days | 6 | partner-adapter (POS sold-out webhook) | Catalog |
| `catalog.menu.published` | Catalog | compacted, thin version | `brand_id:menu_id:channel` | compact | 6 | Catalog | partner-adapter, Catalog cache |
| `catalog.availability.changed` | Catalog | compacted state | `brand_id:store_id:sku_id` | compact | 6 | Catalog | partner-adapter, Catalog cache |
| `order.requested` | Order | command `oneof` | `brand_id:order_id` | 7 days | 12 | partner-adapter (aggregator create, replace, cancel, and POS status) | Order |
| `order.events` | Order | lifecycle | `brand_id:order_id` | 7 days | 12 | Order | Delivery, Notification, Loyalty, Voucher, partner-adapter |
| `payment.requested` | Payment | command `oneof` | `brand_id:transaction_id` | 7 days | 12 | Order (capture, void), webhook-adapter, Delivery (payout) | Payment |
| `payment.events` | Payment | lifecycle | `brand_id:transaction_id` | 7 days | 12 | Payment | Order, Wallet, Notification, Delivery |
| `delivery.requested` | Delivery | command `oneof` | `brand_id:delivery_id`, rider variants `mfg:rider_ref` | 7 days | 12 | partner-adapter | Delivery |
| `delivery.events` | Delivery | lifecycle | `brand_id:delivery_id` | 7 days | 12 | Delivery | Order, Notification, partner-adapter, Payment |
| `notification.requested` | Notification | command `oneof` | `brand_id:notification_id` | 7 days | 6 | Voucher & Campaign (broadcast), Loyalty, Wallet, Voucher (send), webhook-adapter (receipt) | Notification |

`store.changed` carries hours, status, zone, and `group_id` on the same key. Open-now is not a topic. A reader derives it from hours, status, and the current time. Consumers react to it by changing their own rows; they do not keep a copy of the store. Order does not consume it: it checks the store live with `ResolveStore` at checkout. Delivery does not copy it either: it syncs the store out to the fleet provider as a merchant.

`catalog.menu.published` is thin: version and `effective_at` only. The consumer calls `GetMenu(version)`. A menu can pass Kafka's 1 MB default, so the body stays off the topic.

`order.requested` is one `oneof`: create, replace, cancel, POS status. The same order id stays in one partition, so a cancel cannot pass the create.

`payment.requested` is one `oneof`: capture, void, webhook, payout. Charge and refund are not on it. Charge is the checkout gRPC, because the shopper is waiting for `authorize_url`. Refund is an admin gRPC. The webhook variant is published by webhook-adapter after it has checked the gateway signature. `payout` is published by Delivery in the same commit as `delivered`, one payout per delivery. Delivery chooses the id and Payment uses it as the transaction id, so the key stays `brand_id:transaction_id`. A rider payout uses `brand_id = mfg` (P-23).

`payment.events` is one `oneof`: authorized, captured, failed, voided, refunded, paid_out, payout_failed. Wallet acts on `captured` with `purpose=top_up` only. Delivery acts on `paid_out` and `payout_failed` only. Every other variant is an Ack with no work for that consumer. It does not have its own topic.

A wallet spend is not on this bus. Payment calls Wallet over gRPC (`Hold`, `Capture`, `Release`, `Refund`) and the caller is waiting, so a command cannot return the hold (D-09).

`order.events` is one `oneof`: placed, accepted, rejected, ready, completed, cancelled. Delivery acts on `accepted` (start dispatch) and `cancelled` (cancel the provider job). Every other variant is an Ack with no work.

Notification reads `payment.events` for `refunded` only. Every other variant is an Ack with no work.

`delivery.requested` is one `oneof`: provider_update, rider_sync, roster_sync. partner-adapter publishes it after it has checked the provider signature and mapped the payload. `provider_update` is keyed `brand_id:delivery_id`, so two status updates for one delivery stay in order. `rider_sync` and `roster_sync` are keyed `mfg:rider_ref`. They are thin: the record carries the provider ref, and Delivery reads the profile or the shift from the provider. The record never carries a phone number, a name, or an address. A provider_update and a rider_sync are different aggregates, so they do not need to be ordered against each other.

`delivery.events` is one `oneof`: dispatched, rider_assigned, picked_up, delivered, failed, cancelled. `delivered` carries the timeline, the distance, and the fees. It does not carry the rider's phone or the customer's address. Order moves the order on `delivered`, `failed`, and `cancelled`. Notification messages the shopper from the same facts. partner-adapter pushes a FAAS brand callback. Payment Statement invoices a FAAS brand from `delivered`. Everyone else Acks with no work.

`notification.requested` is one `oneof`: send, broadcast, receipt. `send` carries a template key, a `customer_id`, and template variables. It never carries a phone number, an email, or a LINE user id, because Notification reads those from Identity at send time. `broadcast` is thin: Campaign writes the audience file to S3 and the command carries only the S3 key. `receipt` is published by the webhook-adapter after it has checked the SES, SMS, or LINE signature. A domain that already publishes a fact never also sends `send`. Notification consumes that fact instead, which is why Order and Payment are not producers. OTP is not on this topic. Identity calls `SendOtp` over gRPC because the shopper is waiting.

## What is not a topic

These were on the previous diagrams. They do not come back.

| Removed | Why it is gone |
| --- | --- |
| `store.upserted`, `store.group.upserted`, `store.hours.changed`, `store.status.changed`, `store.zone.updated`, `store.snapshot` | One compacted `store.changed` already carries the latest store, including group, hours, status, and zone. |
| `store.availability.changed` | Open-now is derived. A cron publishing it is a second source of truth. |
| `store.import.requested`, `catalog.import.requested` | A worker in the owning engine reads the S3 or Excel file. Nobody is waiting, and nothing else consumes the file. |
| `brand.published` | Renamed `brand.changed` so every compacted fact uses the same suffix. |
| `catalog.availability.requested` | Renamed `catalog.requested`. |
| `catalog.item.upserted` | Voucher calls `ListSkus` when it needs the SKU list. The menu topic already says a version exists. |
| `order.create.requested`, `order.replace.requested` | Folded into `order.requested`. |
| `order.bsl.create.request`, `order.bsl.cancel.request`, `order.bsl.create.successful`, `order.bsl.cancel.failed`, `order.bsl.update` | The POS call is a worker in Order. It talks to the BSL proxy over gRPC. POS status comes back on `order.requested`. |
| `payment.create`, `payment.update`, `payment.gw.request`, `wallet.topped_up` | Charge is gRPC. Capture and void are `payment.requested`. Results are `payment.events`. The gateway call is a worker, not a topic. |
| `admin.authenticated`, `admin.authentication.failed`, `admin.principal.created`, `admin.grant.changed`, `admin.session.revoked`, `partner.token.issued`, `partner.client.changed`, `access.fraud.flagged` | An admin is waiting, so the write is gRPC. A token on the bus is a secret. The audit row stays in Postgres. |
| `admin.grant.requested`, `admin.session.revoke.requested`, `partner.client.rotate.requested`, `partner.client.revoke.requested` | Same reason: the caller is waiting. |
| `wallet.requested`, `wallet.events`, `wallet.balance.changed` | A spend is gRPC, because Payment is waiting for the hold (D-09). Nobody else reacts to a balance change, so there is no fact. Notification is told with `notification.requested`. |
| `mfg.fleet.exchange.api`, `zeek_webhook_rider`, `zeek_webhook_roster`, and a queue per fleet | Folded into `delivery.requested`. The provider webhook is an edge adapter, not a topic per provider. |
| `rider.created`, `rider.roster`, `roster.schedule` | The same command topic. A rider sync is a thin pointer, and Delivery reads the profile from the provider. |

## 2029 concept — no new topics yet

The [2029 concept](platform-concept.md) adds no topic by itself (P-35). Each feature fits an existing door:

| Concept feature | Where it lives | Why it is not a topic |
| --- | --- | --- |
| AI ordering, "complete your meal" | gRPC reads, then `UpdateCart` (P-34) | the shopper is waiting |
| Best deal stack, member price | the cart pricing call (O-21) | the shopper is waiting |
| Payment routing and failover across partners | a worker behind Payment's provider port (O-22) | internal to Payment; results are still `payment.events` |
| Pay Later | a tender behind Payment, like the wallet (O-23) | Payment is waiting for the answer |
| Minor Wallet in every brand, auto top-up | Wallet gRPC; a top-up is still `payment.events{captured, purpose=top_up}` (O-19) | a spend is gRPC (D-09) |
| Points and level across brands | Loyalty consumes `order.events`, as today (O-20) | the existing fact already carries the order |
| Personal home page, recommendations | the data-lake sink (P-11), plus any feature store decided under O-25 | the sink reads facts that already exist |
| Live tracking | `order.events`, `delivery.events`, the WebSocket on `customer-bff` | already exists |
| Minor ID consent | Identity gRPC (P-33) | personal data stays off the bus (D-05) |

If O-19 or O-20 moves a wallet or loyalty profile to a group tenant, its records are keyed `mfg:<aggregate id>`, the way rider variants already are. A new topic still needs a row in the registry above, with a named producer and consumer, before it appears on a diagram.

## Envelope

```
key:     brand_id:<aggregate id>
headers: event_id, event_type, brand_id, occurred_at, version, traceparent
value:   Protobuf oneof, BACKWARD compatible
```

`event_id` is the idempotency key. `version` is monotonic per key. A consumer that sees the same version again does nothing, then Ack.
