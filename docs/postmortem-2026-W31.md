# Post-mortem FL-2026-08: mobile checkout events lost in 2026-W31

* **Status:** closed · **Severity:** data quality, medium (no wrong decision shipped)
* **Period affected:** Monday 2026-07-27 to Sunday 2026-08-02 (ISO week 2026-W31)
* **Detected:** 2026-08-04, during the refresh on the 2026-08 export · **Author:** analytics team
* **Format:** blameless: we describe systems and decisions, not people.

## Summary
Mobile app release 8.14 changed the checkout screen and stopped sending most `checkout` events. For one
week, about 70 % of mobile checkout events are missing from the export, while orders were still
recorded. The analysis pipeline did not fail: every `error` check passed and one `warn` check fired.
The new weekly monitoring showed the mobile checkout-given-cart rate at 10.7 % in W31 against a median
of 53.4 % (−80 %). We excluded the week from the analysis (contract 1.1.0, `exclude_weeks`) and
documented it here.

## Impact
- **Data:** 1,218 sessions in W31 (all devices) are excluded from v1.1 answers, with their events
  and orders. Orders with no checkout event rose from 53 (W31 excluded) to 113 (W31 included).
- **Decision:** none changed. With W31 included, the estimated mobile payment-step uplift is
  ₹14.1 lakh/month; with it excluded, ₹14.3 lakh/month (CMH odds ratio 0.725). Both are below the ₹25 lakh
  rebuild threshold: the recommendation stays `run_targeted_experiment`.
- **Risk avoided:** the weekly chart with W31 shows a false collapse of mobile checkout that a reader
  could take for a real drop, the opposite of what happened (orders continued).

## Timeline (IST)
| When | What | Source |
|---|---|---|
| 2026-07-27 10:00 | App 8.14 released to 100 % of Android and iOS users | app release notes |
| 2026-07-27 → 08-02 | Checkout screen sends `checkout` only on a retry path; most events lost | analytics SDK diff |
| 2026-08-03 11:30 | Hotfix 8.14.1 released; events back to normal | app release notes |
| 2026-08-04 09:40 | Refresh on 2026-08: v1.0 pipeline exits 3 on `sessions.channel.accepted` (referral, unrelated) | CI run |
| 2026-08-04 14:10 | v1.1 pipeline (referral accepted): passes, `orders.without_checkout.ratio` warns (3.3 %) | `answers.json` |
| 2026-08-04 15:00 | Weekly monitoring flags W31, `mobile_checkout_given_cart` −80 % | `answers.monitoring.anomalies` |
| 2026-08-04 16:30 | App team confirms the 8.14 regression | team chat |
| 2026-08-05 11:00 | Contract 1.1.0 with `exclude_weeks: ["2026-W31"]`; golden 2026-08; parity IDENTICAL | PR, CI run |

## Root cause
The checkout screen of 8.14 moved the analytics call into a callback that only fired after a payment
retry. No test in the app checked that funnel events are sent, and the release checklist had no
"analytics events" item. On the analytics side, the only safeguards were monthly row-level checks,
which compare rows, not behaviour over time.

## Detection
- **What worked:** the warning `orders.without_checkout.ratio` (orders exist, their checkout does not)
  and the weekly monitoring with a median baseline, which pinned the problem to one week and one metric.
- **What did not:** detection took 8 days, because the analysis only runs when an export is
  requested. A warning alone (3.3 % against a 2 % threshold) is easy to dismiss.

## What went well
- The contract stopped the v1.0 pipeline instead of producing numbers on a changed schema.
- Three tracks agreed on every number once the spec was clarified (see the parity note in Phase 7).
- The exclusion is explicit, versioned and reversible; its effect is measured above.

## What went badly
- Eight days between the release and detection.
- A spec ambiguity (when to count unknown channels relative to the exclusion) cost half a day.
- The median rule has known limits: with fewer than about 8 full weeks, or a real trend, it misfires.

## Action items
| # | Action | Owner | Due | Verified by |
|---|---|---|---|---|
| 1 | Run the pipeline weekly on the latest export (scheduled workflow) and alert on any anomaly | analytics | 2026-08-31 | a scheduled run on `main` |
| 2 | Add "analytics events fire for every funnel step" to the app release checklist | app team | 2026-08-15 | checklist in the app repo |
| 3 | App end-to-end test asserting `cart`, `checkout`, `payment` events on a test purchase | app team | 2026-09-15 | app CI |
| 4 | Worked examples in `contract/questions.md` for every counting rule | analytics | done | questions.md §2, `(v1.1)` notes |
| 5 | Revisit the median rule when the history exceeds 26 weeks (seasonality) | analytics | 2027-01 | ADR-0006 follow-up |
