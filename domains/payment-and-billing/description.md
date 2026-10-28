# Payment & Billing

Payment & Billing moves the money and writes the paper. One Go engine owns the transaction. Checkout returns `authorize_url` on the gRPC. Capture, void, and the gateway webhook travel on the bus. A rider payout calls TrueMoney. Statement is a mode of this app, not a second service: after capture it writes the Thai tax invoice and receipt, and it never talks to a gateway.

Food payments are authorized first and captured later. The hold is placed at authorize. Money moves at capture, and only after Order has accepted the POS ticket. A rejection becomes a void. There is one transactions table, one Omise account per brand, and no automatic second gateway.

| | |
| --- | --- |
| **Owns** | The transaction, the attempt, gateway keys per brand, the invoice, and the receipt. |
| **Does not own** | The order status, the wallet balance, or the price. Order runs the saga. Wallet owns the stored-value ledger. |
| **How it is called** | Order calls `CreateTransaction` at checkout. A wallet tender calls Wallet `Hold` and returns no `authorize_url`. Capture and void call Wallet `Capture` or `Release`. `customer-bff` calls `CreateTransaction` only for a wallet top-up, captured at authorize. `admin-bff` calls refund, and a wallet tender calls Wallet `Refund`. Omise and TrueMoney are reached by this engine. They never call it. Webhooks land at `webhook-adapter`. |
| **Kafka** | Publishes `payment.events` (authorized, captured, failed, voided, refunded, paid_out, payout_failed). Consumes `payment.requested` (capture, void, webhook, payout) and `delivery.events` (`delivered` invoices a FAAS brand). Charge and refund stay gRPC, because someone is waiting. |

## v-next (2026-10-25): the table bill (proposal)

For postpaid table ordering ([`postpaid-table-ordering.md`](../../docs/design/postpaid-table-ordering.md), P-47, P-48), `CreateTransaction` gains `purpose = table_bill`: the final bill is charged and captured at once, like a wallet top-up, and only then does Order close the POS check. An optional `purpose = table_preauth` is a card hold at the first round, partly captured or released at close. A partial capture is new for this domain and depends on the gateway (to confirm). Statement mode writes the receipt and tax invoice from the paid bill. Rates, tips, service charge, and the guest tax invoice are to confirm with finance and legal (O-41). A split bill is several transactions, each with one tender (flagged against P-16, O-40). The HLD does not show this yet.

## Diagrams

**Overview** — `payment-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Charge, capture, refund, and rider payout. A solid line is another domain asking. A dashed line is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**SHLD** — `payment-billing-shld.drawio` *(not yet drawn: this file is not in the repo)*

One page: hold, then capture or release, a refund, and the Thai tax invoice. A wallet spend is a tender behind the payment, a top-up is taken at once, and a partner brand is invoiced when the order is delivered.

**HLD** — `payment-billing-hld.drawio`

One page: checkout, the wallet port, the command in, the transaction, statement mode (including the FAAS invoice), and who consumes `payment.events` (Order, Wallet, Delivery, Notification).

**LLD** — `payment-billing-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | CreateTransaction |
| 2 | Gateway webhook |
| 3 | Capture and void |
| 4 | Refund |
| 5 | Statement mode |
| 6 | Rider payout |
