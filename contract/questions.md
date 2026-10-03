# FunnelLens: business questions, cleaning rules and formulas

This page is the **single source of truth** for every number FunnelLens reports. The Python, SQL and R
tracks implement it independently and must agree (to 1e-9 relative, integers exactly) on
`contract/golden/answers-2026-06.json`. If a rule here is ambiguous, fix this page first, then the code.

## 1. The decision and the questions

> Mobile is ~69 % of sessions but only ~61 % of revenue. The Head of Product wants to rebuild the
> mobile checkout (a quarter of a squad's time). **Should we?**

| # | Question | Answer field |
|---|---|---|
| Q1 | Can we trust the export? What did cleaning remove, and do the contract checks pass? | `data_quality` |
| Q2 | How does the funnel (view → cart → checkout → purchase) differ by device? | `funnel` |
| Q3 | Is the mobile payment step (purchase given checkout) worse, and by how much? | `payment_step_test` |
| Q4 | Does the gap survive once we compare like with like (within acquisition channel)? Is any aggregate gap a mix effect (Simpson)? | `by_channel` |
| Q5 | Do mobile buyers spend less per order? | `order_value` |
| Q6 | Is the weekly trend stable (no breaks or backfills that would invalidate a comparison)? | `weekly` |
| Q7 | If mobile paid like desktop within each channel, what would it be worth per month? | `opportunity` |
| Q8 | Recommendation, with machine-readable reasons | `decision` |

## 2. Cleaning rules (apply in this order; count everything you remove)

All raw files are read **as text**; empty cells stay empty strings. *Normalise a label* = trim
surrounding whitespace, then lower-case.

**users**: `user_id` → integer. `signup_channel` "" → null (count: `users_missing_signup_channel`).
`city` → normalised label, then mapped through `cleaning.city_aliases` (`bangalore` → `bengaluru`).
`users_city_variants_merged` = distinct raw `city` strings − distinct clean cities.

**sessions** (in this order):
1. Normalise `device` and `channel`; a channel in `cleaning.unknown_channel_values` ("", "(not set)",
   "unknown") becomes `unknown`.
2. Parse `started_at` after trimming. Exactly two formats exist: `YYYY-MM-DD HH:MM:SS` and
   `DD/MM/YYYY HH:MM` (day first). Any other text, or an impossible date (30 February), is a bad
   timestamp: drop the row (`sessions_bad_timestamp`).
3. Drop rows that are exact duplicates **after** steps 1-2 (same id, user, device, channel and
   instant): keep one, count the removed rows (`sessions_exact_duplicates`).
4. A `session_id` that still appears more than once has conflicting rows: drop **all** of its rows
   and count the distinct ids (`sessions_conflicting_ids`).
5. Drop sessions whose date is outside `[period_start, period_end]` of `export.json`
   (`sessions_out_of_period`).
6. Drop sessions whose `user_id` is not a clean user (`sessions_orphan_user`).
7. Count clean sessions with channel `unknown` (`sessions_unknown_channel`; they are kept).
   *(v1.1)* Count them **after** step 9, so the count and its ratio check describe the analysed sessions.
8. Derive `week` = ISO 8601 week of the start date as `YYYY-Www` (e.g. 1 Jan 2026 → `2026-W01`) and
   `month` = `YYYY-MM`.
9. *(v1.1)* Drop sessions whose `week` is in `cleaning.exclude_weeks` (`sessions_excluded_week`).
   Their events and orders then fail the orphan rules below and are counted there. This count is the
   **last** key of `issues` (after `orders_without_checkout`).

**events**: normalise `event_name`; drop names not in `cleaning.steps` (`events_unknown_name`);
then drop events whose session is not a clean session (`events_orphan_session`). Keep one row per
(session, step) with the earliest timestamp; the removed rows are `events_repeated_steps`.
`sessions_out_of_order` = sessions where, for two consecutive steps that both exist (view→cart,
cart→checkout), the later step's first timestamp is earlier than the earlier step's.

**orders** (in this order): drop rows identical in every raw column, keep one
(`orders_exact_duplicates`). Parse `amount` to integer **paise**: trim; delete every `₹`, `Rs.`,
`,` and space; the rest must match `^-?\d+(\.\d{1,2})?$` (else `orders_unparseable_amount`, dropped);
`"1,299.5"` → 129950. Amounts ≤ 0 are refunds or test rows (`orders_non_positive_amount`, dropped).
Orders whose session is not clean are dropped (`orders_orphan_session`). Count clean orders whose
session has no checkout event (`orders_without_checkout`; kept for revenue).

## 3. Metrics

**Session funnel.** For each clean session: `view` = has a view event; `cart` = view and a cart event;
`checkout` = cart and a checkout event; `purchase` = checkout and at least one clean order. Every
count below is a number of sessions.

- `funnel.by_device.<all|desktop|mobile>`: `sessions, view, cart, checkout, purchase`,
  `revenue_paise` = sum of **all** clean orders of those sessions (also orders without checkout),
  `conversion` = purchase / sessions, `step_rates` = view/sessions, cart/view, checkout/cart,
  purchase/checkout (null if the denominator is 0).
- `mobile_share_of_sessions`, `mobile_share_of_revenue` = mobile / all.
- `by_channel.channels`: for each channel (sorted by name), the five counts per device.
- `weekly`: for each ISO week that has a clean session (sorted), sessions and purchases per device and
  `conversion` = purchases / sessions (null when a device has no session that week).

## 4. Statistics (group 1 = mobile, group 2 = desktop; z₉₇.₅ = `analysis.z_975`)

**Two proportions** (Q3; x successes of n): p₁ = x₁/n₁, p₂ = x₂/n₂, difference = p₁ − p₂.
z = (p₁ − p₂) / √(p̄(1 − p̄)(1/n₁ + 1/n₂)) with pooled p̄ = (x₁ + x₂)/(n₁ + n₂); two-sided
p = erfc(|z|/√2). 95 % interval (unpooled Wald): difference ± z₉₇.₅·√(p₁(1−p₁)/n₁ + p₂(1−p₂)/n₂).
Q3 uses successes = purchase, n = checkout.

**Cochran-Mantel-Haenszel** (Q4), no continuity correction. One 2×2 table per channel where both
devices have n > 0 at the base step: a = mobile successes, b = mobile failures, c = desktop
successes, d = desktop failures, n = a+b+c+d. Steps: `cart_given_view` (successes cart, base view)
and `purchase_given_checkout` (purchase, checkout).
- E = (a+b)(a+c)/n, V = (a+b)(c+d)(a+c)(b+d) / (n²(n−1)); statistic = (Σa − ΣE)² / ΣV; p = erfc(√(statistic/2)).
- Mantel-Haenszel odds ratio OR = Σ(ad/n) / Σ(bc/n).
- 95 % interval: exp(ln OR ± z₉₇.₅·√v) with the Robins-Breslow-Greenland variance, R = ad/n,
  S = bc/n, P = (a+d)/n, Q = (b+c)/n:
  v = ΣPR / (2(ΣR)²) + Σ(PS + QR) / (2·ΣR·ΣS) + ΣQS / (2(ΣS)²).
- `crude_odds_ratio` = (Σa·Σd)/(Σb·Σc); `strata` = number of tables.
- `simpson` (cart step): `aggregate_gap` = mobile − desktop cart/view over all sessions;
  `within_channel_gaps` = the same per stratum; `reversal` = the aggregate gap is negative and every
  within gap positive, or the other way round.

**Welch t test** (Q5) on order values in rupees (paise/100) of all clean orders, mobile vs desktop:
mean, sample sd (n − 1); se = √(s₁²/n₁ + s₂²/n₂); t = (m₁ − m₂)/se;
df = se⁴ / ((s₁²/n₁)²/(n₁−1) + (s₂²/n₂)²/(n₂−1)); two-sided p from Student's t with df (not an
integer); 95 % interval (m₁ − m₂) ± t₀.₉₇₅,df · se.

## 5. Opportunity and decision

**Opportunity** (Q7): per CMH stratum of `purchase_given_checkout`, gap = max(0, c/(c+d) − a/(a+b));
extra orders = (a+b)·gap. `extra_orders_in_sample` = Σ; `months` = calendar months of the period;
the export is a sample (`sample_rate`, 0.05 = 1 in 20 sessions), so
`extra_orders_per_month` = Σ / months / sample_rate;
`mobile_aov_inr` = mean mobile order value; `monthly_revenue_uplift_inr` = extra_orders_per_month ·
mobile_aov_inr; `mobile_monthly_revenue_inr` = mobile revenue_paise / 100 / months / sample_rate;
`uplift_share_of_mobile_revenue` = uplift / mobile monthly revenue.

**Decision** (Q8), thresholds from `analysis`:
1. CMH `purchase_given_checkout` p ≥ alpha → `no_checkout_gap_found`, reasons `[adjusted_payment_gap_not_significant]`.
2. else uplift ≥ `rebuild_min_monthly_uplift_inr` → `rebuild_checkout`, `[adjusted_payment_gap_significant, uplift_above_rebuild_threshold]`.
3. else → `run_targeted_experiment`, `[adjusted_payment_gap_significant, uplift_below_rebuild_threshold]`.
4. Then append `aggregate_cart_gap_is_channel_mix` if the aggregate cart gap is negative and the
   cart-step CMH is not significant **or** its OR ≥ 1 (mobile carts at least as well within channels).

## 6. v1.1: monitoring and payment methods

**`monitoring`** (data quality over time; it reports, it never stops the run):
- `freshness`: `period_end`; `last_session_date` = date of the latest clean session;
  `days_behind` = period_end − last_session_date (days); `stale` = days_behind > `monitoring.max_days_behind`.
- `excluded_weeks` = `cleaning.exclude_weeks` (as listed in the contract).
- `weeks`: every **full** ISO week of the period (its Monday ≥ period_start and its Sunday ≤ period_end)
  that has a clean session, in week order, with `sessions` (all devices) and
  `mobile_checkout_given_cart` = mobile sessions with funnel checkout / mobile sessions with funnel cart
  (null if no mobile cart).
- `medians`: the median of each metric over `weeks` (nulls ignored; an even count takes the mean of the
  two middle values).
- `anomalies`: for each week (in order) and each metric (`sessions` first), deviation =
  (value − median) / median; an anomaly when |deviation| > `monitoring.max_relative_deviation`:
  `{week, metric, value, median, deviation}`.

**`payment_methods`**: `null` when the raw orders have no `payment_method` column (exports before
2026-08). Otherwise `{"by_device": {"desktop": {method: orders}, "mobile": {...}}}` over clean orders,
method = normalised label (`""` → `unknown`), keys in name order.

**Compatibility.** Schema 1.1 only adds fields. On the 2026-06 export a v1.1 pipeline reproduces every
v1.0 field of `golden/answers-2026-06.json` (except `schema_version`, `generator` and
`dataset.contract_version`), and a v1.0 dashboard reads v1.1 answers (the schema allows extra fields).

## 7. Numbers and JSON

Counts are integers. Rates, statistics and money are unrounded doubles; round only when you display
them. A rate with a zero denominator is `null`. Key order in `answers.json` does not matter; list
order does (contract order for `checks`, name order for channels, week order for `weekly`).
