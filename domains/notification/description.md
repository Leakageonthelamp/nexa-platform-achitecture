# Notification

Notification delivers the message. One Go engine owns the templates, the message log, the in-app inbox, device tokens, and whether a channel can reach that customer. Six channels leave from here: push, SMS, email, LINE, WebSocket, and the inbox.

It does not own the person. Identity owns the phone, the email, the LINE user id, and PDPA consent. Notification reads them over gRPC at send time, so no personal data rides the bus. A domain that already publishes a fact (Order, Payment) is not also asked to send a command. Notification turns those facts into messages. Loyalty, Wallet, and Voucher send `notification.requested` until they have a fact topic of their own.

Aggregator orders are skipped. Grab, LINE MAN, and Shopee Food already notify their own customer.

| | |
| --- | --- |
| **Owns** | Templates, the message log, the inbox, device tokens, channel reachability, and brand channel config. |
| **Does not own** | The contact, the consent, or the OTP code. Identity generates the OTP and calls `SendOtp` because the shopper is waiting on that screen. |
| **How it is called** | `customer-bff` registers devices, reads the inbox, and holds the WebSocket. `admin-bff` writes templates and channel config, and CSC reads the log and resends. Provider receipts (SES, SMS, LINE) arrive at `webhook-adapter` and become a command. |
| **Kafka** | Publishes nothing. Consumes `order.events`, `payment.events` (refunded only), `delivery.events` (shopper status), and `notification.requested` (send, broadcast, receipt). |

## Diagrams

**Overview** — `notification-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Order status, a refund, the one-time code, and the inbox. A solid line is another domain asking. A dashed line is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**SHLD** — `notification-shld.drawio` *(not yet drawn: this file is not in the repo)*

One page: who asks for a message, delivery status told by Delivery rather than a second send, and the channels that reach the customer.

**HLD** — `notification-hld.drawio`

One page: the consumes, including `delivery.events`, the path from event to message log to channel, and the call to Identity for contacts.

**LLD** — `notification-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | `order.events` consumer |
| 2 | SendOtp |
| 3 | Broadcast |
| 4 | Provider receipt |
| 5 | RegisterDevice |
| 6 | `payment.events` refunded |
| 7 | Send command |
| 8 | Inbox |
| 9 | Preferences |
| 10 | Templates |
| 11 | Brand channel config |
| 12 | CSC log and resend |
| 13 | Campaign stats |
| 14 | WebSocket fanout |
| 15 | Channel sender |
| 16 | UnregisterDevice |
| 17 | `delivery.events` consumer |
