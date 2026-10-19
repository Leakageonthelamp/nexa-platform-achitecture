# Wallet

Wallet is stored value. One Go engine holds one wallet per brand per customer, plus an append-only ledger. Available balance is `balance − held`. It is not a column. Only a ledger entry moves the balance.

A spend looks like any other tender. Payment calls Hold, Capture, Release, and Refund, the same way it calls Omise. Order, Voucher, and MemberCard never call Wallet. Top-up money stays in Payment: the shopper pays Omise, and Wallet credits the ledger when `payment.events` says that top-up was captured. Real money never lands here.

| | |
| --- | --- |
| **Owns** | The wallet per brand and customer, the stored-value ledger, and holds. |
| **Does not own** | The charge, the card, the order, or loyalty points. |
| **How it is called** | Payment is the only writer on the checkout path. `admin-bff` calls `Adjust` (CSC credit or a correcting debit) with the `wallet.adjust` grant, a reason, and a limit. `customer-bff` reads `GetWallet` and `ListEntries`. A shopper never writes. |
| **Kafka** | No wallet topic. Consumes `payment.events`, and only a captured top-up. Sends `notification.requested` so Notification can tell the customer. |

## Diagrams

**SHLD** — `wallet-shld.drawio`

Who uses the stored-value balance, what Wallet does, and how a wallet payment and a top-up run.

**Overview (tryout)** — `wallet-overview.drawio`. The rulebook for the next one is [`overview-guideline.md`](../overview-guideline.md).

A system overview: four doors into one ledger, then Payments, Notifications, and the nightly check. A solid line is another domain asking. A dashed line is Kafka. Each door is marked with the choice that serves it: gRPC where the caller waits, Kafka for the top-up and the customer message, Aurora PostgreSQL for the ledger, and a daily job for the nightly check. Not a replacement for the SHLD.

**HLD** — `wallet-hld.drawio`

One page: the four doors (Payment, admin adjust, reads, top-up credit), the ledger, and why nothing is published except a notification. This is the reference for the relation lines on every HLD.

**LLD** — `wallet-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | Hold |
| 2 | Capture and release |
| 3 | Top-up credit |
| 4 | Adjust |
| 5 | Refund to wallet |
| 6 | GetWallet and ListEntries |
| 7 | Reconciliation cron |
| 8 | Pay with wallet, end to end |
