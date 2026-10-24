#!/usr/bin/env python3
"""NEXA scale calculator. Every number below is an ASSUMPTION, not a measurement.

Edit the PARAMETERS block, run `python3 scale-calc.py`, and paste the tables into
docs/design/scale-assumptions.md. Nothing here is a fact about production load.
"""
import math

# ---- PARAMETERS (all assumptions; the owner rewrites these) -----------------
TIERS = {                       # peak orders per minute, all brands together
    "S": 200,
    "M": 1000,
    "L": 5000,
}
HOT_BRAND_SHARE = 0.40          # share of total peak that the busiest brand takes
BURST_FACTOR = 1.5              # peak second vs the average second of the peak minute
EDGE_REQ_PER_ORDER = 40         # BFF requests per order (menu, cart reads, PlaceOrder, status polls)
PG_WRITE_TX_PER_ORDER = 25      # Postgres write transactions per order, all domains (outbox rows included)
RECORDS_PER_ORDER = {           # Kafka records per order, per topic (own-app order, delivery share applied)
    "order.events": 5,
    "payment.events": 3,
    "payment.requested": 2,
    "order.requested": 4,       # POS status updates, duplicates included
    "delivery.events": 2,       # about half the orders are delivery, about 4 events each
    "notification.requested": 1,
}
PARTITIONS_REGISTERED = {"order.events": 12, "payment.events": 12, "payment.requested": 12,
                         "order.requested": 12, "delivery.events": 12, "notification.requested": 6}
CONSUMER_RECORDS_PER_PARTITION_PER_SEC = 100   # one Postgres transaction and Ack per record
PARTITION_HEADROOM = 3          # spare capacity so a backlog can drain
PAYLOAD_LOG_DOCS_PER_ORDER = 12 # Mongo documents per order
PAYLOAD_LOG_AVG_KB = 4          # average document size after masking
ORDERS_PER_MONTH_AT_PEAK_SHARE = {"S": 60_000, "M": 400_000, "L": 2_000_000}  # monthly orders per tier
RETENTION_DAYS = 90             # payload log TTL
# -----------------------------------------------------------------------------

def row(*c):
    return "| " + " | ".join(str(x) for x in c) + " |"

print("### Load shape per tier (assumptions)\n")
print(row("Tier", "Peak orders/min (total)", "Busiest brand, orders/min", "Peak orders/s (with burst)",
          "Edge requests/s", "Kafka records/s (all topics)", "Postgres write tx/s (all domains)"))
print(row(*["---"] * 7))
osec = {}
for t, opm in TIERS.items():
    o = opm / 60 * BURST_FACTOR
    osec[t] = o
    rec = o * sum(RECORDS_PER_ORDER.values())
    print(row(t, f"{opm:,}", f"{opm * HOT_BRAND_SHARE:,.0f}", f"{o:,.0f}",
              f"{o * EDGE_REQ_PER_ORDER:,.0f}", f"{rec:,.0f}", f"{o * PG_WRITE_TX_PER_ORDER:,.0f}"))

print("\n### Partitions needed per topic: ceil(records/s / per-partition rate x headroom)\n")
print(row("Topic", "Registered partitions", *[f"Needed at {t}" for t in TIERS]))
print(row(*["---"] * (2 + len(TIERS))))
for topic, n in RECORDS_PER_ORDER.items():
    need = []
    for t in TIERS:
        r = osec[t] * n
        need.append(max(6, math.ceil(r / CONSUMER_RECORDS_PER_PARTITION_PER_SEC * PARTITION_HEADROOM)))
    print(row(f"`{topic}`", PARTITIONS_REGISTERED[topic], *need))

print("\n### Payload log (MongoDB) volume\n")
print(row("Tier", "Orders/month", "Docs/month", "GB/month", f"GB held at {RETENTION_DAYS}-day TTL"))
print(row(*["---"] * 5))
for t, m in ORDERS_PER_MONTH_AT_PEAK_SHARE.items():
    docs = m * PAYLOAD_LOG_DOCS_PER_ORDER
    gb = docs * PAYLOAD_LOG_AVG_KB / 1024 / 1024
    print(row(t, f"{m:,}", f"{docs:,}", f"{gb:,.1f}", f"{gb * RETENTION_DAYS / 30:,.1f}"))

print("\n### Error budget per 30-day month\n")
print(row("Availability target", "Allowed downtime per 30 days"))
print(row("---", "---"))
for a in (99.5, 99.9, 99.95, 99.99):
    print(row(f"{a}%", f"{30 * 24 * 60 * (1 - a / 100):,.1f} min"))
