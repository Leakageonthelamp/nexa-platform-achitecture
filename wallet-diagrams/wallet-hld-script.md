# Wallet HLD — presenter script

Source: [`wallet-hld.drawio`](wallet-hld.drawio). About 10 minutes, then questions. Screen-share the diagram and leave it zoomed out until a section says to zoom.

The sentence on the title is the whole talk: **stored value, its own ledger, paid through Payment.**

This domain publishes no topic of its own. It consumes `payment.events` and sends `notification.requested`. The full list lives in [`kafka-topics.md`](../kafka-topics.md). The rules it follows are D-09, D-10, and D-11 in the [architecture baseline](../architecture.md).

---

## 0. Open (45 seconds)

Point at the title, then the grey subtitle.

> One Go engine. One wallet per brand per customer. Payment calls Hold, Capture, Release, and Refund, so a spend looks like any other tender. Top-up money stays in Payment. `brand_id` is on every hop.

Walk the four pills once:

1. Orange — gRPC. Hold, Capture, Release, Refund, Adjust, and the reads.
2. Blue — HTTP. None. The edge stops at the BFFs. Omise never calls Wallet.
3. Purple — the command we send, `notification.requested`.
4. Green — the fact we consume, `payment.events`.

---

## 1. Callers (2 minutes)

Zoom to **1. Callers**. Each caller has one line into the engine box it calls.

> **Payment** is the provider port. It calls `Hold` when it authorizes, then `Capture` or `Release`, and `Refund` when an admin refunds a wallet tender. Same shape as its call to Omise.
>
> **admin-bff** calls `Adjust`: a CSC top-up, or a debit to correct a mistake. The admin needs the `wallet.adjust` grant, a reason code, and must stay inside the grant's limit.
>
> **customer-bff** reads `GetWallet` and `ListEntries`. A shopper sees only their own wallet, and never writes.

> Order, Voucher, and MemberCard never call Wallet. They pay through Payment (D-09). The whole pay-with-wallet checkout is LLD 8.

---

## 2. Kafka in (1 minute)

Zoom to **2. Kafka in**.

> `payment.events`, and only the `captured` variant whose purpose is `top_up`. Follow the `consume` line into **Top-up credit**. The Ack sits under it, after the commit.
>
> Every other variant is an Ack with no work. A second delivery of the same transaction id does nothing. There is no `wallet.requested`.

---

## 3. The engine (3 minutes)

Zoom to **3. Wallet engine**. Read it left to right: doors, then state, then background work.

> The left column is the four doors: **Payment port**, **Admin adjust**, **Reads**, and **Top-up credit**.
>
> The middle column is the state. **Holds** reserve balance and change `held` only. **Wallet + ledger** is one row per brand per customer, plus `wallet_entries`, which is append-only. Only an entry moves the balance. Available is `balance - held`; it is not a column.

Follow the lines into **Wallet + ledger**: capture and refund from Payment, credit and debit from Adjust, read from Reads, credit from Top-up.

> There is no hold timer (P-14). Order's sweeper already voids an unpaid checkout, and that void releases the hold.

Point at the right column.

> **Outbox relay** publishes the send, written in the same commit. **Reconciliation** runs once a day at 03:00: entries against the balance, and any hold still open after 24 hours. A mismatch is logged and raised as a metric. Nothing is auto-fixed. The same job purges outbox rows older than 7 days.

> Real money never lands here (D-10). The Omise charge stays in Payment.

---

## 4. Facts out (1 minute)

> There is no wallet fact. Nobody reacts to a balance change, and Payment already has the answer on the gRPC reply.
>
> What leaves is `notification.requested`, variant `send`, with a template key: `wallet.topped_up`, `wallet.adjusted`, or `wallet.refunded`. Those are template keys, not topics. The record carries `customer_id`. It never carries a phone number or an email.

---

## 5. Consumers (30 seconds)

> **Notification** is the only consumer. It delivers the send, then Ack.

---

## 6. Data, decisions, not this domain (2 minutes)

> Aurora holds wallets, holds, wallet_entries, the outbox, and the audit log. One schema, one role. Follow the `commit · read` line down from the engine.
>
> No Valkey. A balance is never cached. No S3. Amounts are integer amounts.

Read the bold words in **Decisions**, then the cost on each line. Stop on two:

> P-14, no hold timer. The cost is that a hold Payment never closes waits for CSC.
>
> `ponytail:` one entries table and one row lock. The ceiling is no double-entry ledger. The upgrade is double-entry, when finance asks.

**Not this domain**: Payment owns Omise, the top-up charge, a refund back to a card, and the tax invoice. Order owns the checkout timeout. Loyalty owns points and the loyalty profile. Identity owns the customer. Notification owns delivery.

---

## 7. Close (30 seconds)

> Payment is the only door for a spend. The ledger here counts stored value and nothing else. The only fact we consume is a captured top-up, and the only thing we publish is a send.

Stop talking. Take questions.

---

## If they ask

**What happens when the shopper pays with the wallet?**
The same checkout as a card (LLD 8). Order calls `CreateTransaction` with `method = wallet`. Payment calls `Hold` and gets `authorized` back at once, so there is no 3DS and no `authorize_url`. Order places the order and sends the POS ticket. When the POS accepts, Payment calls `Capture`, which writes the spend entry. When it rejects, or the sweeper fires, Payment calls `Release`, and the balance never moved.

**Why is a wallet spend not a command?**
Payment is waiting for the hold. A command cannot return it (D-09).

**Can the shopper split wallet and card?**
Not in v1 (P-16). A short balance is `FAILED_PRECONDITION`, and the app offers a card for the whole order.

**Who tops the wallet up?**
The shopper, through Payment and Omise. Or CSC, through `Adjust`, with a grant, a reason, and a limit (P-15). The limit amount is still open (O-12).

**Why no hold timer?**
Order's sweeper already closes an unpaid checkout and voids it. A second timer here would be a second source of truth, and a hold could expire just before Payment captures it. Reconciliation catches the rare hold nobody closed.

**Why no freeze?**
Nobody asked for one in v1. CSC can debit with `Adjust`. A freeze comes back when fraud needs it (P-15).

**Why one entries table, not transactions plus entries?**
Single-entry: every operation writes exactly one entry. A second table would only repeat it.

**Where is the tax invoice?**
Payment's Statement mode. Whether it is issued at top-up or at spend is open (O-11).

**What about a balance cap, expiry, and e-money rules?**
Open (O-10). Nothing is checked yet.
