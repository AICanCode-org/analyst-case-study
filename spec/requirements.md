# FunnelLens requirements

> Reference version (tag `phase-1-end`). Yours can differ in wording; it should not differ in the
> decision rule, which the contract fixes for this course.

## 1. The decision
The Head of Product will decide in the next planning cycle whether to spend a quarter of the mobile
squad (≈ ₹75 lakh fully loaded) on rebuilding the mobile checkout. Rebuilding when the checkout is
not the problem wastes the quarter and leaves the real cause (traffic mix, pricing, payment options)
untouched. Not rebuilding when it is broken leaves money on the table every month. The analysis must
say which of three outcomes the evidence supports: **rebuild**, **run a targeted experiment first**,
or **do not rebuild**.

## 2. Stakeholders
| Stakeholder | Needs from the analysis | Would like the answer to be |
|---|---|---|
| Head of Product (decides) | A recommendation with the evidence and its limits, on one page | "Rebuild" |
| Mobile engineering lead | Which step is worse, and by how much, to scope any work | "It is not the code" |
| Finance partner | The monthly value of closing the gap vs the rebuild cost | A conservative number |
| Marketing / CRM lead | Whether channel mix explains the gap | "Not my channels" |
| Data / analytics lead | A reproducible, reviewed analysis the next analyst can re-run | — |

## 3. Questions
| # | As asked | Metric (contract/questions.md) |
|---|---|---|
| Q1 | "Can we even trust this export?" | rows removed per rule, contract checks (§2, data-contract.yaml) |
| Q2 | "Where does mobile lose people?" | step rates view→cart→checkout→purchase by device (§3) |
| Q3 | "Is the mobile checkout worse?" | purchase given checkout, mobile vs desktop, difference with 95 % CI, two-proportion z (§4) |
| Q4 | "Is it the checkout, or who comes on mobile?" | Mantel-Haenszel odds ratio within acquisition channel, CMH test; Simpson check on cart given view (§4) |
| Q5 | "Do mobile buyers just spend less?" | mean order value by device, Welch's t (§4) |
| Q6 | "Did anything break during the period?" | weekly sessions and conversion by device (§3) |
| Q7 | "What is it worth?" | extra orders per month if mobile paid like desktop within channel × mobile AOV, scaled to the full traffic (§5) |
| Q8 | "So what do we do?" | the decision rule below, with machine-readable reasons (§5) |

## 4. Decision rule (agreed before the analysis)
Primary test: the payment step (purchase given checkout) of mobile vs desktop, **adjusted for
acquisition channel** (Cochran-Mantel-Haenszel), α = 0.05, two-sided.
1. Not significant → `no_checkout_gap_found` (do not rebuild).
2. Significant and monthly uplift ≥ ₹25,00,000 → `rebuild_checkout`.
3. Significant and uplift < ₹25,00,000 → `run_targeted_experiment` (an A/B test of payment-step fixes).

α = 0.05 is the team's convention for a single pre-registered test. ₹25 lakh a month = the rebuild
cost recovered in three months. Both values live in `contract/data-contract.yaml` (`analysis:`).
Other tests (Q3 unadjusted, Q5, cart step) are descriptive context and cannot overturn the rule.

## 5. Data and its limits
- One export, 2026-01-01 to 2026-06-30, a random **1-in-20 sample of sessions** (rates are unbiased;
  totals are scaled by 20).
- **Observational:** users chose their device and channel. Adjustment for channel removes one known
  confounder, not all of them (age, income, intent). The analysis can show *where* and *how much*,
  not *why*.
- Purchases are orders linked to a session; there is no purchase event, no page-load or app-version data.
- Known defects: duplicate and conflicting sessions, two date formats, amounts as text, city
  spellings, missing signup channels, out-of-order and orphan events, orders without a checkout.

## 6. Acceptance criteria
1. `make run` and `make report` work from a clean checkout in every track, with no manual step.
2. Every cleaning rule of questions.md §2 reports how many rows it removed or changed (`data_quality.issues`).
3. A failing `error` check stops the pipeline with exit code 3 before any answer is written; `warn` checks are reported.
4. `answers.json` validates against `contract/answers.schema.json`.
5. The three tracks produce identical answers (1e-9 relative, integers exactly) and match the golden file.
6. Every effect is reported with a 95 % interval and the test it comes from; p-values are never the only number.
7. The recommendation follows mechanically from the decision rule and lists its reasons.
8. The memo and the dashboard state the observational caveat and never use causal language.
9. Unit tests cover every rule on the tiny fixture; data tests check invariants on the real export; coverage ≥ 85 %.
10. No row-level data leaves the pipeline: answers.json, the dashboard and any AI prompt contain aggregates only.

## 7. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Confounding by channel (mobile gets more low-intent traffic) | Primary test stratified by channel (CMH) |
| Simpson's paradox: an aggregate gap that reverses or vanishes within channels | Report within-channel gaps next to the aggregate; `simpson` section |
| A join on a non-unique key multiplies orders or revenue | Uniqueness checks before joins; invariants (devices add up to all, rows removed + kept = read) |
| Forking paths: trying cuts until one is significant | One pre-registered primary test; everything else is labelled descriptive |
| A tracking break or backfill in one week | Weekly series (Q6); from v1.1 automatic monitoring |
| Wrong formula or library default (continuity correction, pooled vs unpooled) | Formulas written in questions.md; hand-computed `stats-cases.json`; three independent tracks |
| An AI-written summary invents or rounds a number wrongly | The narrator sees numbered facts only; guardrails check every number; template fallback |

## 8. Out of scope (v1)
Causal attribution of the gap to specific checkout screens (needs an experiment or session
recordings), payment-method analysis (not in the 2026-06 export), city-level analysis, forecasting,
customer lifetime value.
