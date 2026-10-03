# ADR-0002: The primary test is a Cochran-Mantel-Haenszel test stratified by channel

* **Status:** accepted
* **Date:** 2026-07-03
* **Deciders:** analytics team, reviewed with the Head of Product

## Context
The decision depends on whether mobile users pay less after checkout *than comparable desktop users*.
Mobile and desktop traffic come from different channel mixes, so the crude comparison mixes device and
channel effects. The test must be reproducible in pandas/statsmodels, SQL and base R.

## Options considered
1. **Crude two-proportion z test** — simple; confounded by channel mix.
2. **Logistic regression with device + channel terms** — flexible; harder to reproduce exactly in SQL,
   and its odds ratio assumes no interaction just like CMH, with more modelling choices to argue about.
3. **CMH test with channel strata** — a closed-form, textbook adjustment for one categorical
   confounder; Mantel-Haenszel common OR with the Robins-Breslow-Greenland interval.

## Decision
Option 3 for the payment step (purchase given checkout), α = 0.05, no continuity correction, strata
with both devices present. The crude z test and OR are reported next to it, as context.

## Consequences
One pre-registered primary test (no forking paths). The formulas are short enough to write in
`contract/questions.md` §4 and implement in SQL. It adjusts for channel only; other confounders remain
and the memo says so. If the per-channel odds ratios disagree strongly (heterogeneity), the common OR
is a poor summary: the per-channel table is always shown.

## AI assistance
An assistant claimed statsmodels' `StratifiedTable.test_null_odds()` applies a continuity correction by
default; checked the docs: `correction=False` is the default. Pinned by `stats-cases.json`.
