# Notification HLD — presenter script

Source: [`notification-hld.drawio`](notification-hld.drawio). About 14 minutes, then questions. Screen-share the diagram and leave it zoomed out until a section says to zoom.

The sentence on the title is the whole talk: **facts and commands in, one message log, every channel out.**

This domain consumes three topics and publishes none. It owns one of them, `notification.requested`. The full list lives in [`kafka-topics.md`](../kafka-topics.md).

---

## 0. Open (1 minute)

Point at the title, then the grey subtitle under it.

> One Go engine. It owns the templates, the message log, the inbox, device tokens, and channel reachability.
>
> It does not own the person. Identity owns the phone, the email, the LINE user id, and PDPA consent. We read them over gRPC at send time, so no personal data rides the bus.
>
> Six channels: push, SMS, email, LINE, WebSocket, and the in-app inbox. One stack, `brand_id` on every hop.

Walk the four pills once, left to right:

1. Orange — gRPC. `SendOtp`, the inbox, `RegisterDevice`, templates, and our own call to Identity, `BatchGetContacts`.
2. Blue — HTTP. FCM, SES, SMS, and LINE going out. Provider receipts coming in at the edge.
3. Purple — one command, `notification.requested`.
4. Green — no fact out. We only consume.

> If a line is not one of those, it is not a path we support.

---

## 1. Callers (2 minutes)

Zoom to **1. Callers**.

> Cloudflare and Kong sit in front, as on every page. Kong is the only PEP. It also lets the WebSocket upgrade through, for the customer token issuer only.
>
> **customer-bff** registers devices, reads the inbox, saves preferences, and holds the WebSocket. Bun handles sockets natively, so there is no socket service.
>
> **admin-bff** is the only write door. It needs the manage-notification grant to write templates and brand channel config. CSC uses the same door to read the message log and resend.
>
> **Identity** calls `SendOtp`. The shopper is staring at the OTP screen, so this is sync.

Point at the note.

> Providers never call us directly. Receipts come in through webhook-adapter and become a command.

---

## 2. Kafka in (2 minutes)

Zoom to **2. Kafka in**.

> Three consumes.
>
> `order.events` is Order's lifecycle: placed, accepted, rejected, ready, completed, cancelled. Each one can become a push, an inbox row, and a WebSocket frame.
>
> `payment.events` — we keep `refunded` and Ack everything else. Order already turns payment failures into `order.events`, so we don't message twice.
>
> `notification.requested` is ours. One `oneof`: send, broadcast, receipt.

Point at the webhook-adapter.

> SES bounces arrive through SNS, and SMS delivery receipts and LINE follow and unfollow events come in too. The adapter checks the signature, then publishes the receipt variant. A bad signature dies at the edge.

> Loyalty, Wallet, and Voucher use `send` for now, because they have no fact topic yet. A domain that already publishes a fact never also sends `send`. That is why Order and Payment are not producers.

---

## 3. The engine (4 minutes)

Zoom to the yellow lane, **3. Notification engine**. Walk the main path first. It runs bottom-left to top-right.

> **Intake** has one handler per topic. It only acts on a new `event_id`, commits, then Acks.
>
> **Rules** maps an event type to a template and a set of channels, per brand. Aggregator orders are skipped, because Grab or LINE MAN already notifies its own customer.
>
> **Recipient resolve** calls `BatchGetContacts` on Identity in pages of 500. It checks consent, locale, and reachability.
>
> **Message log** gets one row per recipient and channel, unique on event id, template, and channel. That unique key is why a replay can't double-send.
>
> **Send workers.** They claim rows in status `queued`. OTP, transactional, and marketing each have their own workers, so a two-million-customer broadcast never delays an order push. After the provider answers, the worker writes `sent` or `failed` back on that row.
>
> **Rate limiter** is a Valkey token bucket per brand and provider. **Channel senders** make the HTTP call: three retries with backoff, then the row is failed.

Point at the left column.

> `SendOtp` is the exception. It sends inline with a 3-second timeout, and the code is never logged. Templates and the inbox are plain gRPC.

Point at **Broadcast worker** and **Quiet hours**.

> A broadcast command carries only an S3 key. The worker reads the audience file in pages and writes the rows. Quiet hours (21:00 to 08:00) and the frequency cap apply to marketing only. An order update never waits.

Point at the ponytail note.

> The message log is the send queue. Ceiling: row churn on a multi-million broadcast. Upgrade: SQS per priority lane, same workers.

---

## 4. Facts out (1 minute)

Zoom to **4. Facts out**.

> No fact topic. Nobody downstream acts on a delivery status. Campaign reads stats over gRPC, and CSC reads the message log.
>
> Realtime is not a topic either. Senders publish to Valkey pub/sub on `ws:brand_id:customer_id`. It is at-most-once. The app re-reads on reconnect.

---

## 5. Channel providers (1 minute)

Zoom to **5. Consumers**.

> One trunk, five branches. FCM covers Android and iOS through APNs. SES has one identity per brand domain. End User Messaging carries SMS with a sender ID per brand. LINE has one OA per brand.
>
> These are outbound HTTP calls, not consumes, so there is no Ack. SES and SMS use an IAM role, so there is no static key.
>
> The last box is our own customer-bff. It subscribes to Valkey and fans out to the sockets on that pod.

---

## 6. Data, decisions, not this domain (2 minutes)

Point at **6. Data**.

> Aurora is the truth: templates, the message log partitioned by day, inbox, devices, preferences, and audit. Valkey holds token buckets and pub/sub. S3 holds broadcast audiences. Vault holds the FCM service account, the APNs key, and LINE tokens.
>
> The message log keeps `customer_id`, not the phone or the email.

Point at **Decisions**, read the bold words only, then point at **Not this domain**.

> Identity owns the person and the OTP code. Order and Payment are only read from their facts. Campaign owns the segment. Delivery joins when its topic exists. Aggregators and the kitchen are not ours.

---

## 7. Close (30 seconds)

> Three topics in. One message log. Every channel out through one door per provider. OTP is the only thing anyone waits on.
>
> No personal data on the bus. Brands are rows.

Stop talking. Take questions.

---

## If they ask

Answer from the diagram. If it is not on the page, say it is not decided here.

**Why not consume a `loyalty.events` topic instead of `send`?**
It does not exist. With Notification as the only consumer, a Loyalty fact would be a queue. When a second consumer appears, Loyalty publishes a fact and stops sending `send`.

**Why is OTP gRPC and not the command topic?**
The shopper is waiting. A command cannot return "sent" or "failed" to the login screen.

**What happens if the SMS provider is down during OTP?**
The call fails fast after 3 seconds and the login shows an error. There is no second SMS provider. That is a written cost.

**Can a customer get the same push twice?**
A Kafka replay cannot cause it, because the message row is unique. A crash after the provider returned 200 but before our commit can send one duplicate. That is the at-least-once cost.

**Why not keep a copy of contacts and consent?**
That would put personal data on the bus and give PDPA two copies to keep in sync. Live reads cost a delay when Identity is down, and the retry covers it.

**How does a broadcast avoid starving order updates?**
Separate worker pools per priority, a token bucket per provider, and quiet hours for marketing.

**What if the WebSocket drops?**
Frames are lost. The app re-reads `GetOrder` on reconnect, and the push and inbox row carry the same update.

**Who decides which customers get a campaign?**
Campaign. It writes the audience file to S3. We only deliver.

**Where are LINE and FCM secrets?**
Vault, per brand. Never on the bus or in a log.
