# Food aggregator order data design (first launch)

Source LLD: `food-aggregator/food-aggregator-v1.drawio`.  
Diagram: `food-aggregator-erd.drawio` (9 pages). DDL: `schema.sql`. Seed: `seed_status.sql`.

Backups (box only): `food-aggregator-erd-v1-tracks/` (multi-track), `food-aggregator-erd-v2-simple/` (first single-status cut).

## 1. Purpose

order-domain is the source of truth for first launch (Grab / LINE MAN → POS):

- one order row per channel order, idempotent on `ref_id`
- one POS ticket (`order_subs`) per brand/store/POS
- **one** `status` column on order and sub, values from `order_statuses`, filled via `status_mappings`
- raw message log in Mongo `order_raw` (never used for decisions)

## 2. Single status model

| Piece | Where | Meaning |
|---|---|---|
| `status` | `orders`, `order_subs` | Same `order_statuses.code` values |
| mapper | `status_mappings` | `(source, raw_status) → status_code` |
| history | `order_status_history` | Append-only + `UNIQUE(source,event_id)` dedup |

**Why `order_statuses` lookup (not a PG enum):** mapper FK, reserved inactive rows, rank in DB.

### Apply rules

1. Map raw → candidate via `status_mappings`. Unknown → history `applied=false`.
2. Rank only moves forward (and `occurred_at` not stale). Else `applied=false`.
3. POS event updates matching sub, then rollup `orders.status`.
4. Delivery event applies only if current ≥ READY.
5. Grab cancel is final → CANCELLED (+ `status_reason` if food already left).
6. One PG TX: update + history + outbox. Reconcile every 5 min.

Vendor codes: only Grab public values are real. LINE MAN / BSL / SDM = TBD placeholders.

## 3. Status lifecycle

| Status | Rank | Meaning | Entered by (source → raw) | Next | Terminal | Active |
|---|---|---|---|---|---|---|
| RECEIVED | 10 | Accepted into OMS | SYSTEM create | CONFIRMED, CANCELLED, FAILED, PENDING_PAYMENT* | No | Yes |
| PENDING_PAYMENT | 15 | Waiting authorize | PAYMENT → TBD_successful* | CONFIRMED, CANCELLED, FAILED | No | Reserved |
| CONFIRMED | 30 | POS ticket confirmed | BSL TBD_ACCEPTED / SDM UpdateOrder:OK | PREPARING, CANCELLED, REJECTED | No | Yes |
| PREPARING | 40 | Kitchen cooking | BSL TBD_COOKING (TBD) | READY, CANCELLED | No | Yes |
| READY | 50 | Ready for rider/pickup | BSL TBD_READY (TBD) | OUT_FOR_DELIVERY, COMPLETED, CANCELLED | No | Yes |
| OUT_FOR_DELIVERY | 60 | Rider en route | **GRAB COLLECTED** | DELIVERED, CANCELLED*, FAILED | No | Yes |
| DELIVERED | 70 | Handed to customer | **GRAB DELIVERED** | COMPLETED, AWAITING_PAYMENT* | No | Yes |
| AWAITING_PAYMENT | 75 | Postpaid bill unpaid | OWN channel* | COMPLETED, CANCELLED | No | Reserved |
| COMPLETED | 100 | Done | SYSTEM close / pickup | — | Yes | Yes |
| CANCELLED | 100 | Cancelled | **GRAB CANCELLED** / BSL TBD_VOID | — | Yes | Yes |
| REJECTED | 100 | POS/channel rejected | BSL reject (TBD) | — | Yes | Yes |
| FAILED | 100 | Hard failure | **GRAB FAILED** / submit exhausted | — | Yes | Yes |

\* reserved / rare.

### Example paths

1. **Grab delivery happy:** RECEIVED → CONFIRMED → PREPARING → READY → OUT_FOR_DELIVERY → DELIVERED → COMPLETED  
   (`grab_4y25f-tcc-siam_A-7XKQ`, The Coffee Club Siam)
2. **POS reject:** RECEIVED → CONFIRMED → REJECTED
3. **Grab cancel:** … → READY → CANCELLED (`GRAB CANCELLED` final; if picked up, keep CANCELLED + `status_reason`)

## 4. What we removed

| Removed | Why | Add back later |
|---|---|---|
| Separate payment/delivery/pos columns | One status enough for prepaid launch | Side tables when own channel/fleet needs parallel progress |
| `order_deliveries`, `order_payments`, `order_sessions` | Overhead | New tables; reserved statuses already seeded |
| `order_sub_items` | `items` jsonb | Normalize when reporting needs it |
| `inbox` / `parked_events` | History UNIQUE + reconcile | Only if early events become common |

## 5. Data dictionary

### 5.1 `order_statuses` (PostgreSQL)

| Column | Type | Null / Key | Why it exists | Example |
|---|---|---|---|---|
| code | text | PK | Canonical status id used by orders.status and order_subs.status | READY |
| rank | smallint | NOT NULL | Progress order; ignore backward moves | 50 |
| is_terminal | boolean | NOT NULL | No further transitions when true | false |
| is_active | boolean | NOT NULL | false = reserved for later features | true |
| description | text | NULL | Human-readable meaning | Ready for pickup / rider |

### 5.2 `status_mappings` (PostgreSQL)

| Column | Type | Null / Key | Why it exists | Example |
|---|---|---|---|---|
| id | bigint | PK identity | Surrogate key | 12 |
| source | text | UK NOT NULL | Vendor/system that emitted the raw status | GRAB |
| raw_status | text | UK NOT NULL | Exact vendor value before normalize | COLLECTED |
| status_code | text | FK → order_statuses | Normalized status | OUT_FOR_DELIVERY |
| is_active | boolean | NOT NULL | Soft-disable without deleting | true |
| note | text | NULL | Doc / TBD reminder | Grab docs — picked up |
| created_at | timestamptz | NOT NULL | When mapping was inserted | 2026-11-09 10:00:00+07 |

### 5.3 `orders` (PostgreSQL)

| Column | Type | Null / Key | Why it exists | Example |
|---|---|---|---|---|
| id | uuid | PK | Internal UUID v7 | 01936c8a-7f3e-7000-8000-a1b2c3d4e5f6 |
| ref_id | text | UK NOT NULL | External idempotency key (not cross-domain FK) | grab_4y25f-tcc-siam_A-7XKQ |
| channel | text | UK1 NOT NULL | Sales channel | GRAB |
| channel_order_id | text | UK1 NOT NULL | Order id inside the channel | A-7XKQ |
| channel_short_code | text | NULL | Short code for staff/rider | 7XKQ |
| channel_merchant_id | text | UK1 NULL | Merchant id at channel | 4y25f-tcc-siam |
| brand_id | text | NULL | Primary brand | TCC |
| store_id | text | NULL | Primary store | TCC-BKK-SIAM |
| fulfillment_type | text | NOT NULL | DELIVERY / PICKUP / DINE_IN | DELIVERY |
| payment_mode | text | NOT NULL | PREPAID today for aggregators | PREPAID |
| delivery_provider | text | NOT NULL | Who delivers; NONE for pickup | GRAB |
| scheduled_for | timestamptz | NULL | When to fire POS if scheduled | null |
| customer | jsonb | NULL | Masked customer snapshot | {"name":"Somchai","phone":"+66******89"} |
| delivery_address | jsonb | NULL | Masked drop-off | {"area":"Pathum Wan","note":"Lobby"} |
| items | jsonb | NULL | Full line snapshot | [{"sku":"TCC-LATTE","qty":2,"price":12000}] |
| currency | char(3) | NOT NULL | ISO currency | THB |
| subtotal | bigint | NOT NULL | Food subtotal (satang) | 24000 |
| discount_total | bigint | NOT NULL | Discount (satang) | 0 |
| delivery_fee | bigint | NOT NULL | Delivery fee (satang) | 2500 |
| service_charge | bigint | NOT NULL | Service charge (satang) | 0 |
| tax_total | bigint | NOT NULL | Tax (satang) | 1680 |
| grand_total | bigint | NOT NULL | Customer total (satang) = ฿281.80 | 28180 |
| status | text | FK NOT NULL | Current normalized status | OUT_FOR_DELIVERY |
| status_reason | text | NULL | Cancel/fail/ops note | null |
| status_changed_at | timestamptz | NOT NULL | Last status change | 2026-11-09 10:28:11+07 |
| first_raw_id | text | NULL | Mongo _id of create | 01936c8a-0001-7000-8000-000000000001 |
| placed_at | timestamptz | NOT NULL | Customer placed-at | 2026-11-09 10:15:00+07 |
| completed_at | timestamptz | NULL | When COMPLETED | null |
| cancelled_at | timestamptz | NULL | When CANCELLED | null |
| created_at | timestamptz | NOT NULL | OMS insert time | 2026-11-09 10:15:02+07 |
| updated_at | timestamptz | NOT NULL | Last update | 2026-11-09 10:28:11+07 |
| version | integer | NOT NULL | Optimistic lock | 4 |

### 5.4 `order_subs` (PostgreSQL)

| Column | Type | Null / Key | Why it exists | Example |
|---|---|---|---|---|
| id | uuid | PK | Sub (POS ticket) UUID v7 | 01936c8a-7f3e-7000-8000-b2c3d4e5f607 |
| order_id | uuid | FK UK1 NOT NULL | Parent order | 01936c8a-7f3e-7000-8000-a1b2c3d4e5f6 |
| seq | smallint | UK1 NOT NULL | 1-based sequence | 1 |
| ref_id | text | UK NOT NULL | Sent to POS as external ref | grab_4y25f-tcc-siam_A-7XKQ#1 |
| brand_id | text | NOT NULL | Brand for this ticket | TCC |
| store_id | text | NOT NULL | Store for this ticket | TCC-BKK-SIAM |
| pos_type | text | UK2 NOT NULL | POS adapter | BSL |
| pos_store_ref | text | NOT NULL | Store id in POS | e5a2accc22ec42808a6a3e4cfede055b |
| pos_order_id | text | UK2 NULL | POS ack id; fallback lookup | POS-982341 |
| items | jsonb | NULL | Lines for this POS ticket | [{"sku":"TCC-LATTE","qty":2,"plu":"10021"}] |
| currency | char(3) | NOT NULL | Currency | THB |
| subtotal | bigint | NOT NULL | Subtotal (satang) | 24000 |
| discount_total | bigint | NOT NULL | Discount (satang) | 0 |
| tax_total | bigint | NOT NULL | Tax (satang) | 1680 |
| grand_total | bigint | NOT NULL | Sub total (satang) | 25680 |
| status | text | FK NOT NULL | Same order_statuses codes | READY |
| status_reason | text | NULL | Fail/cancel reason | null |
| status_changed_at | timestamptz | NOT NULL | Last change | 2026-11-09 10:22:00+07 |
| attempt_count | smallint | NOT NULL | Submit retry count | 1 |
| next_attempt_at | timestamptz | NULL | When to retry submit | null |
| last_error | text | NULL | Last submit error | null |
| submitted_at | timestamptz | NULL | First successful submit | 2026-11-09 10:16:05+07 |
| created_at | timestamptz | NOT NULL | Insert time | 2026-11-09 10:15:02+07 |
| updated_at | timestamptz | NOT NULL | Last update | 2026-11-09 10:22:00+07 |
| version | integer | NOT NULL | Optimistic lock | 3 |

### 5.5 `order_status_history` (PostgreSQL)

| Column | Type | Null / Key | Why it exists | Example |
|---|---|---|---|---|
| id | bigint | PK identity | History row id | 1042 |
| order_id | uuid | FK NOT NULL | Order that changed | 01936c8a-7f3e-7000-8000-a1b2c3d4e5f6 |
| sub_id | uuid | FK NULL | Sub if POS-side; null for delivery | 01936c8a-7f3e-7000-8000-b2c3d4e5f607 |
| source | text | UK1 NOT NULL | Who emitted the event | GRAB |
| raw_status | text | NULL | Vendor value before map | COLLECTED |
| from_status | text | NULL | Before | READY |
| to_status | text | NOT NULL | After (or attempted) | OUT_FOR_DELIVERY |
| applied | boolean | NOT NULL | false = ignored (rank/stale) | true |
| event_id | text | UK1 NOT NULL | Dedup with source | evt_grab_A-7XKQ_collected |
| reason | text | NULL | Optional reason | null |
| raw_id | text | NULL | Mongo order_raw._id | 01936c8a-00aa-7000-8000-0000000000aa |
| occurred_at | timestamptz | NOT NULL | Time at source | 2026-11-09 10:28:10+07 |
| recorded_at | timestamptz | NOT NULL | Time OMS wrote history | 2026-11-09 10:28:11+07 |

### 5.6 `outbox` (PostgreSQL)

| Column | Type | Null / Key | Why it exists | Example |
|---|---|---|---|---|
| id | uuid | PK | Event id | 01936c8a-7f3e-7000-8000-c3d4e5f60718 |
| aggregate_type | text | NOT NULL | ORDER or SUB | ORDER |
| aggregate_id | uuid | NOT NULL | Aggregate that changed | 01936c8a-7f3e-7000-8000-a1b2c3d4e5f6 |
| partition_key | text | NOT NULL | Kafka key = orders.ref_id | grab_4y25f-tcc-siam_A-7XKQ |
| topic | text | NOT NULL | Kafka topic | order.events.v1 |
| event_type | text | NOT NULL | Domain event name | OrderStatusChanged |
| payload | jsonb | NOT NULL | Event body | {"status":"OUT_FOR_DELIVERY"} |
| headers | jsonb | NULL | Optional Kafka headers | {"correlation_id":"evt_..."} |
| created_at | timestamptz | NOT NULL | Enqueued in same TX | 2026-11-09 10:28:11+07 |
| published_at | timestamptz | NULL | null = pending publish | 2026-11-09 10:28:12+07 |
| attempts | integer | NOT NULL | Publish retry count | 1 |

### 5.7 `order_raw` (MongoDB)

| Column | Type | Null / Key | Why it exists | Example |
|---|---|---|---|---|
| _id | UUID v7 | PK | Document id | 01936c8a-0001-7000-8000-000000000001 |
| order_ref_id | string | indexed NOT NULL | Joins to orders.ref_id | grab_4y25f-tcc-siam_A-7XKQ |
| order_id | UUID \| null | indexed | Back-filled after PG | 01936c8a-7f3e-7000-8000-a1b2c3d4e5f6 |
| sub_ref_id | string \| null | indexed | Sub ref when POS-scoped | grab_4y25f-tcc-siam_A-7XKQ#1 |
| sub_order_id | UUID \| null | | Back-filled sub UUID | 01936c8a-7f3e-7000-8000-b2c3d4e5f607 |
| direction | string | NOT NULL | INBOUND / OUTBOUND | INBOUND |
| source | string | unique w/ event | Who produced the message | GRAB |
| kind | string | NOT NULL | Message category | PARTNER_STATUS |
| stage | string | unique w/ event | RAW / MINOR_STANDARD / POS_PAYLOAD | RAW |
| event_id | string | unique w/ source+stage | Idempotent insert key | evt_grab_A-7XKQ_collected |
| channel | string | | Channel denorm | GRAB |
| brand_id | string | | Brand denorm | TCC |
| store_id | string | indexed | Store denorm for ops | TCC-BKK-SIAM |
| kafka | object | NULL | Kafka coordinates | {"topic":"agg.order.status.raw.v1","offset":9182} |
| http | object | NULL | HTTP meta if webhook | {"method":"POST","path":"/order-state"} |
| payload | object | NOT NULL | Body with PII masked | {"state":"COLLECTED","orderID":"A-7XKQ"} |
| payload_sha256 | string | | Integrity aid | a3f1c9... |
| error | object \| null | | Parse/downstream error | null |
| occurred_at | date | NOT NULL | Event time at source | 2026-11-09T10:28:10+07:00 |
| received_at | date | NOT NULL | OMS ingest time | 2026-11-09T10:28:11+07:00 |
| expire_at | date | TTL index | received_at + 180d | 2027-05-08T10:28:11+07:00 |

## 6. Open questions

1. Can one pilot order split across brands / POS?
2. Partial accept across subs?
3. Exact LINE MAN / BSL / SDM status codes (echo our `ref_id`)?
4. Grab DRIVER_ALLOCATED / DRIVER_ARRIVED — log-only or rider jsonb later?
5. Multi-sub diverge product rule?
6. Who owns refund after Grab CANCELLED?
7. PII masking + 180d TTL OK?
8. Scheduled-order hold before POS fire?

## 7. Diagram pages

1. ERD Postgres  
2. Mongo order_raw  
3. Status state machine  
4. Status lifecycle  
5. Dict · catalog  
6. Dict · orders  
7. Dict · order_subs  
8. Dict · history & outbox  
9. Dict · Mongo order_raw  
