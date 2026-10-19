# MFG ePlatform — 2029 platform concept

**Target picture, not a rulebook.** This file describes what the customer should feel once the 3-year platform upgrade is finished (2029), and which shared building blocks make it possible. It is written for planners and for AI agents that need the big picture before they design or build anything.

- **Source:** [`Bonchon_App_2029_Concept_Demo.html`](Bonchon_App_2029_Concept_Demo.html), a clickable 11-step demo for internal discussion. Open it in a browser to see each screen.
- **Binding rules live elsewhere.** [`architecture.md`](architecture.md) is the rulebook. Where this concept and the rulebook disagree, the rulebook wins until a decision in [`architecture.md` §13](architecture.md#13-decision-register) changes it. [§7](#7-gaps-against-the-current-baseline) below lists every known disagreement.
- **All numbers are samples.** Menu, prices, people, payment partners, fees, and success rates in the demo are illustrative. Wallet, Pay Later credit, and cross-brand data sharing still need partner, legal (including PDPA), and franchisor agreement.

---

## 1. The idea in one paragraph

Today every Minor Food brand runs its own account, points, wallet, menu set-up, and payment deal. In 2029 the customer has **one Minor ID** that works in every brand app, carries **one wallet and one points balance**, and sees **the same member price and deals in every channel**. Customers can order by tapping or by asking an **AI** in plain words; both go into one cart priced by one rules engine. Card and QR payments go to whichever payment partner is cheapest and working at that moment. Every brand app is built from the same **8 shared building blocks**, so launching or upgrading a brand is mostly configuration, not a new build. The tagline is **"One Minor Food."**

---

## 2. The big picture

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ Brand apps and channels                                                              │
│ Bonchon · The Pizza Company · Swensen's · Sizzler · Dairy Queen · Burger King ·      │
│ The Coffee Club · GAGA        +  Web · Kiosk · LINE · Delivery partners              │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │ one Minor ID, one cart, one price
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 8 shared building blocks                                                             │
│                                                                                      │
│  [1] Customer ID & profile   [2] Membership & CRM    [3] Orders & menu               │
│  [4] Campaign & coupon       [5] Payment & wallet    [6] Data platform               │
│  [7] AI operating brain      [8] Back office                                         │
└───────────────────┬──────────────────────────────────────────────┬───────────────────┘
                    │                                              │
                    ▼                                              ▼
┌──────────────────────────────────────────┐   ┌──────────────────────────────────────┐
│ Any POS till and kitchen system          │   │ Partners: payment, lending, delivery │
│ (through adapters)                       │   │ (several of each, swappable)         │
└──────────────────────────────────────────┘   └──────────────────────────────────────┘
```

**Build once, use in every brand.** A new brand app is a set of rows and settings on the shared blocks, which matches the baseline rule that brands are rows, not deployments ([`architecture.md` principle 6](architecture.md#2-principles)).

---

## 3. Who it is for — the demo persona

The demo follows one customer from first sign-in to her second brand.

| Field | Value in the demo |
| --- | --- |
| Customer | Ploy Srisuk, Minor ID **Gold**, member no. 8812 4567 |
| Home address | Sukhumvit 39 (nearest store has live stock checked) |
| Habit | "Friday usual": Soy Garlic Wings 6 pcs ×2 and Japchae, ฿527 |
| Start state | 1,240 points (Platinum at 2,000), wallet ฿1,250, Pay Later ฿5,000 pre-approved |
| Moment | Friday evening, raining, ordering dinner for 4 (one person does not eat spicy), budget under ฿1,000 |

---

## 4. The 8 shared building blocks

Each block is used by every brand and every channel. The "Shows up in steps" column points to the journey in [§5](#5-the-customer-journey--11-steps).

| # | Block | What it gives the customer and the business | Shows up in steps |
| --: | --- | --- | --- |
| 1 | **Customer ID & profile** | One Minor ID across all brands; phone + OTP sign-in, Apple / Google / LINE login; address, saved card, and PDPA consent that travel with the customer | 1, 8, 9, 11 |
| 2 | **Membership & CRM** | One member level and one points balance in every brand; member price shown on the menu; clear tier progress; a welcome gift the first time a customer tries a new brand | 1, 2, 3, 6, 8, 9, 11 |
| 3 | **Orders & menu** | One menu model for app, web, kiosk, store, and delivery partners; same options everywhere; kitchen notes reach the kitchen screen; live store, kitchen, and rider status | 3, 4, 5, 6, 10, 11 |
| 4 | **Campaign & coupon** | One rules engine for deals (member price, BOGO, coupons); automatically picks the best stack and explains it; margin limits set centrally per campaign | 3, 4, 5, 6, 11 |
| 5 | **Payment & wallet** | Minor Wallet usable in every brand (no partner fee, 2× points); Pay Later through a licensed lending partner; smart routing of card and QR payments across several partners, with automatic retry on the next one | 7, 8, 11 |
| 6 | **Data platform** | With consent, one customer view across brands; inputs for personalization (time of day, weather, habits) | 1, 2, 7, 10, 11 |
| 7 | **AI operating brain** | Personal home page and recommendations with a reason; conversational ordering that respects group size, diet, budget, live stock, and the customer's deals; "save as favourite" nudges | 2, 4, 5, 10, 11 |
| 8 | **Back office** | Central control of menus, prices, campaigns, and margin; POS tills read Minor ID through adapters | 9, 11 |

---

## 5. The customer journey — 11 steps

Each step lists what the customer sees, what changes compared to today, the blocks it relies on, and why it matters to the business.

### Step 1 — Sign in, then choose Minor ID

```
Phone number ──▶ OTP auto-filled from SMS ──▶ Signed in
                                                 │
                                                 ▼
                        Offer: "Upgrade to Minor ID" (one account, 8 brands)
                        PDPA consent toggle, in plain words
                           │                          │
                     Upgrade (1 tap)            "Not now" (always available)
                           ▼                          ▼
                Minor ID active, 8 brands       Keep Bonchon-only account,
                linked                          upgrade later from "Me"
```

- **Customer sees:** phone number and an OTP that fills itself in, no forms; Apple, Google, or LINE as alternatives. Right after sign-in, one clear offer to upgrade to Minor ID. Consent can be changed at any time.
- **Today → 2029:** each brand has its own account, points, and login → one Minor ID for all brands. We cannot see that a Bonchon fan also buys at Swensen's → with consent, one customer view across brands.
- **Rules:** the customer decides; "Not now" is always there. Franchised brands join only when each franchisor agrees.
- **Blocks:** Customer ID & profile, Membership & CRM, Data platform.
- **Why:** every new member becomes a customer of all brands, not just one.

### Step 2 — A home screen that knows the customer

- **Customer sees:** a greeting and first content that change with weather and time of day ("It's raining in Sukhumvit. Your Friday usual can be at your door in about 25 min — order it again?"); member level, points, wallet, and credit in one line; "Your Friday usual" reorder in one tap; AI picks that give a reason ("New · you love Soy Garlic", "Most ordered on rainy days"); 8 simple categories; an "Ask AI" entry.
- **Today → 2029:** the same home page for everyone → each customer sees their own page. Reordering means finding each item again → one tap.
- **Blocks:** Data platform, AI operating brain, Membership & CRM.
- **Why:** faster choice means more orders and bigger baskets.

### Step 3 — Browse a menu that is easy to choose from

- **Customer sees:** clear categories and one-tap filters (not spicy, under ฿200, for sharing, top rated); the Gold member price on the menu itself, with no surprise at checkout; deal labels (BOGO, New) from one campaign engine.
- **Today → 2029:** menu and prices set up again for each channel → one menu service feeds app, web, kiosk, and delivery partners. Member price seen only at the till → the same member price and rules everywhere.
- **Blocks:** Orders & menu, Campaign & coupon, Membership & CRM.
- **Why:** a new item can go live in every channel on the same day, with fewer mistakes.

### Step 4 — Manual order: choose and add

- **Customer sees:** a dish page with photo, rating, member price, and today's deal; required choices (size, glaze) are marked, optional extras and a kitchen note, and the price updates as she chooses; after adding, "Complete your meal" suggests sides and drinks, with her usual Japchae first.
- **Today → 2029:** options differ by channel → one menu model, same options in app, web, kiosk, and store. Upsell is the same list for everyone → based on this order and her habits. Kitchen notes get lost → the note goes straight to the kitchen screen.
- **Key rule:** manual and AI ordering share **one cart and one set of deal rules**.
- **Blocks:** Orders & menu, Campaign & coupon, AI operating brain.

### Step 5 — AI order: say what you need

```
"Dinner for 4. One of us doesn't eat spicy. Under ฿1,000."
        │
        ▼
AI checks: menu · deals for this customer · live stock at the nearest store · past orders
        │
        ▼
Keeps the 3 items already in the cart, adds 8 more
→ 12 wings + 2 non-spicy bowls · ฿968 after deals · ฿32 under budget · saves ฿391
        │
        ▼
Customer: "Add 8 items" — or refine: "Make it ฿800" · "Add a dessert" · "No soda"
```

- **Customer sees:** types or says a need, not a dish name. The AI completes the meal for the group, the diet rule, and the budget, and shows the ready time (about 25 min).
- **Today → 2029:** the customer scrolls and guesses → AI suggests a full meal in seconds. One way to order → tap or ask, and mix them freely.
- **Rule:** the AI must ground every answer in live data (menu, stock, deals) before it answers. It edits the same cart as manual ordering.
- **Blocks:** AI operating brain, Orders & menu, Campaign & coupon.
- **Why:** group orders are the biggest baskets.

### Step 6 — Cart: deals that stack the right way

Worked example from the demo (11 items):

| Line | Amount |
| --- | --: |
| Subtotal | ฿1,359 |
| Buy 1 get 1 · Soy Garlic Wings | −฿199 |
| Gold member price · 10% off food | −฿92 |
| Friday Family coupon · ฿100 off orders over ฿1,000 | −฿100 |
| Free Kimchi Coleslaw coupon (฿59) | not used: ฿100 off is better, kept for next time |
| **Total** | **฿968** (saved ฿391) |

- **Customer sees:** member price, BOGO, and a coupon combined for her; the app picks the best mix, says why, and keeps the unused coupon. Savings, points, and free delivery (Gold benefit, 3 left this month) shown before paying.
- **Today → 2029:** the customer must pick one coupon and rules differ by channel → one rules engine with the same result in app, web, and store. Stacked-deal cost is hard to control → margin limits set centrally per campaign.
- **Blocks:** Campaign & coupon, Membership & CRM, Orders & menu.

### Step 7 — Pay: faster and cheaper

```
Payment options (best for the customer first)
  1. Minor Wallet      balance ฿1,250 · no fee · 2× points        ◀ "Best for you"
  2. Minor Pay Later   ฿5,000 available · pay by 25 Nov · 0% if paid in full
  3. Saved card        •••• 4242, one tap
  4. PromptPay QR      inside the app, no app switching

Behind the screen — card and QR only (wallet has no partner fee)
  Partner A  fee 1.6%  success 98.1%
  Partner B  fee 1.2%  success 99.3%   ◀ chosen: lowest fee, highest success
  Partner C  fee 1.4%  success 97.6%
  Fails? ──▶ retry automatically on the next partner

Confirm with Face ID (~1 s) ──▶ Paid ฿968 · order B-2047 · wallet left ฿282 · +194 points
```

- **Today → 2029:** one payment partner per channel at a fixed fee → several partners, each card or QR payment routed to the cheapest one that works. A failed payment is a lost order → automatic retry on the next partner.
- **Blocks:** Payment & wallet, Data platform.
- **Why:** every 0.1% of fee saved on app sales goes straight to profit. Partner names, fees, and success rates are samples to verify.

### Step 8 — Minor Wallet and Pay Later

- **Customer sees:** one balance that works in all Minor Food brands; top-up tiers with a bonus (฿500 +฿20, ฿1,000 +฿50, ฿2,000 +฿150); auto top-up ("when below ฿200, add ฿500"); pre-approved Pay Later credit for loyal customers (for example ฿5,000 after 3 years, pay by the 25th of next month, 0% if paid in full) from a licensed lending partner; activity across brands (Bonchon spend, The Coffee Club spend, Swensen's cash back).
- **Today → 2029:** gift cards and vouchers differ by brand → one wallet for all brands. Every order pays a payment fee → wallet spend has no partner fee, and cash comes in earlier.
- **Constraint:** the wallet and credit need a licence or a licensed partner, subject to legal review.
- **Blocks:** Payment & wallet, Customer ID & profile, Membership & CRM.

### Step 9 — Member card and benefits

- **Customer sees:** a digital member card with a QR for the counter; progress to the next level in plain words ("566 points to Platinum — about 3 more orders like tonight's"); Gold benefits (10% off food, free delivery 4× a month, birthday wings, priority pick-up lane, 2× points with wallet). In a store, one scan applies the member price and points in about 2 seconds.
- **Today → 2029:** store and app benefits differ → same member, same benefits, every channel. The till needs manual codes → any POS reads Minor ID through an adapter.
- **Blocks:** Membership & CRM, Back office, Customer ID & profile.

### Step 10 — Live tracking, and a reason to come back

```
Confirmed 18:44 ──▶ Cooking 18:47 ──▶ Picked up 19:02 ──▶ Arriving 19:15
                                       (rider Somchai, 4.9)
After the order: points +194 → 1,434 · saved ฿391
AI: "Save this as 'Friday feast'? Next rainy Friday I'll have it ready in one tap."
```

- **Today → 2029:** status updates are late or missing → store, kitchen, and rider status in real time. Silence after the order → a smart next step that builds the habit.
- **Blocks:** Orders & menu, Data platform, AI operating brain.
- **Why:** fewer "where is my order?" calls, more repeat orders.

### Step 11 — One Minor ID, every brand

- **Customer sees:** Ploy opens The Pizza Company app and taps "Continue as Ploy with Minor ID", no new account. Address, wallet (฿1,332, same balance everywhere), saved card, and 1,434 points are already there, plus a welcome gift (free garlic bread on her first order).
- **Blocks:** all 8.
- **Why:** a new brand app becomes mostly set-up, not a new build, and every brand's customers become everyone's customers.

---

## 6. Concept rules an agent should keep

These are the product rules implied by the demo. Use them when proposing designs.

1. **One identity, opt-in.** Minor ID is offered, never forced. Cross-brand sharing needs explicit PDPA consent that can be withdrawn at any time. Franchised brands join only with franchisor agreement.
2. **One cart, two ways in.** Manual taps and AI requests edit the same cart and are priced by the same rules.
3. **One price everywhere.** Member price and deal results are identical in app, web, kiosk, store, and delivery partners, and are shown before checkout, never as a surprise.
4. **The engine picks the best deal stack** and explains it; unused coupons are kept. Margin limits are set centrally per campaign.
5. **AI is grounded.** It checks menu, live stock, and the customer's deals before answering, and it never invents an item or a price.
6. **Wallet first when it is best for the customer.** Card and QR payments are routed to the cheapest working partner, with automatic failover.
7. **Same member, same benefits, every channel**, including the physical till.
8. **Build once.** Anything built for one brand must work for every brand by configuration.

---

## 7. Gaps against the current baseline

The current baseline ([`architecture.md`](architecture.md)) covers the core ordering platform. These concept features are either missing from it or conflict with an accepted decision. **Do not build against the concept where it conflicts; raise a decision in [`architecture.md` §13](architecture.md#13-decision-register) first.**

### Conflicts with accepted decisions

| Concept says | Baseline says | What has to change |
| --- | --- | --- |
| One wallet balance works in every brand (steps 8, 11) | D-11: one wallet per `(brand_id, customer_id)`; a balance does not cross brands; no transfer between brands | **O-19:** a group-level wallet (likely the reserved `mfg` tenant, as P-23 does for riders), plus legal and BOT e-money review (O-10) |
| One points balance and one member level in every brand (steps 1, 9, 11) | D-11: Loyalty is one profile per `(brand_id, customer_id)` | **O-20:** group-level loyalty, and who funds points earned in one brand and spent in another |
| Card and QR routed across several payment partners with failover (step 7) | [§10 guardrail](architecture.md#10-simplicity-guardrails): one provider per brand, no automatic second PSP | **O-22** |
| Wallet and card in the same payment flow, ranked by "best for you" | P-16: one tender per order, no split | No conflict unless split tender is wanted; flag if the product asks for it |

Decisions already taken from this concept: **P-33** (Minor ID is the Identity account, with cross-brand sharing as a consent purpose), **P-34** (AI ordering owns no state and writes only through the cart), and **P-35** (no new Kafka topic yet; see [`kafka-topics.md`](kafka-topics.md#2029-concept--no-new-topics-yet)).

### Building blocks with no home in the baseline yet

| Block | Closest baseline piece | Missing |
| --- | --- | --- |
| Customer ID & profile | Identity & Profile | Minor ID across brands is drawn (P-33). Still open: Apple / Google / LINE login, how Kong sets `X-Brand-Id` for a multi-brand customer (O-06), franchisor data sharing (O-26) |
| Membership & CRM | Loyalty (not drawn); Voucher & Campaign (drawn) | Tier-based member price on the menu, tier progress, first-visit-to-brand welcome gift (O-20, O-21) |
| Campaign & coupon | Voucher & Campaign; Catalog `PriceLines` prices the cart (P-31) | v1 applies a fixed order on the cart. Still open: the best-stack optimizer and central margin limits (O-21) |
| Payment & wallet | Payment & Billing with one gateway (Omise); Wallet | Multi-partner routing and failover (O-22), PromptPay QR in app, Pay Later (O-23), auto top-up and top-up bonus (O-19) |
| Data platform | Data-lake sink only (P-11) | Real-time customer features (habits, time, weather) for personalization (O-25), and a consented cross-brand customer view (P-33) |
| AI operating brain | none | Conversational ordering, recommendations with reasons, saved favourites. The rule is set (P-34); the model, vendor, and host are open (O-24) |
| Back office | Admin & Partner, `admin-bff` | Campaign and margin console; POS read of Minor ID |
| Channels | `customer-bff`, `guest-bff`, `partner-adapter` | Kiosk and web as first-class channels on the same BFFs |

### Already aligned with the baseline

- **Brands are rows** on one shared stack (principle 6), which is the "build once" promise.
- **One menu feeds every channel**, including aggregators, through `catalog.menu.published` and `partner-adapter`.
- **Live store and stock** are checked at the owner, never copied (D-07), which is what the AI needs for "stock at Sukhumvit 39".
- **POS through adapters**: the BSL POS already enters through `partner-adapter`.
- **Live order and rider tracking**: `order.events` and `delivery.events` with the WebSocket on `customer-bff`.
- **Wallet spend has no gateway fee**: Payment calls Wallet the way it calls Omise (D-09).
- **No personal data on the bus** (D-05), which fits the PDPA-first consent model.

---

## 8. Prerequisites outside engineering

- **Legal:** wallet licence or licensed partner (O-10, O-19); Pay Later credit through a licensed lending partner (O-23); PDPA consent design for cross-brand sharing (P-33); tax-invoice timing for wallet top-ups (O-11).
- **Franchisors:** agreement before a franchised brand joins Minor ID, and what data they see (O-26).
- **Finance:** who funds cross-brand points and wallet balances (O-19, O-20); margin floors per campaign (O-21).
- **Partners:** contracts with more than one payment partner so routing has something to choose from (O-22).

---

## 9. Glossary

| Term | Meaning |
| --- | --- |
| Minor ID | One customer identity for all Minor Food brands, opt-in, with PDPA consent |
| Minor Wallet | Stored-value balance usable in every brand in the concept (see the D-11 conflict in [§7](#7-gaps-against-the-current-baseline)) |
| Minor Pay Later | Pre-approved credit for loyal customers, provided by a licensed lending partner |
| Smart payment routing | Sending each card or QR payment to the cheapest working payment partner, with automatic retry on the next one |
| AI operating brain | The shared AI block for personalization and conversational ordering |
| BOGO | Buy one, get one free |
| OTP | One-time password |
| PDPA | Thailand's Personal Data Protection Act |
| CRM | Customer relationship management |
| POS | Point of sale (store till) |
| QR | Quick Response code; PromptPay QR is Thailand's QR payment |
