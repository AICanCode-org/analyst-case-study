# ADR-0006: Versioned data contract, explicit week exclusion, and weekly monitoring

* **Status:** accepted
* **Date:** 2026-08-05
* **Deciders:** analytics team

## Context
The 2026-08 refresh brought three changes: a legitimate new channel (`referral`) that the 1.0.0
contract rejects, a new `payment_method` column, and one week of broken mobile tracking (2026-W31,
incident FL-2026-08) that no row-level check stops. Past answers files cite contract 1.0.0 and must
stay reproducible; readers of v1.0 answers (the v1.0 dashboard) must keep working.

## Options considered
1. **Edit the contract in place, fix W31 by imputing the missing checkout events.** Simple; old
   answers can no longer be reproduced, and imputation invents the very metric under study.
2. **Loosen the checks** (map unknown channels to `unknown`, raise the warn threshold). The run passes;
   the referral programme disappears into `unknown` and the next incident goes unnoticed too.
3. **Version the contract (1.1.0), keep 1.0.0 in `contract/history/`, exclude broken weeks explicitly
   with a post-mortem, and add monitoring that reports (never stops) weekly deviations from the median.**

## Decision
Option 3.
- `version: "1.1.0"`; `referral` accepted; `cleaning.exclude_weeks: ["2026-W31"]` with a comment naming
  the incident; a `monitoring` section (`max_relative_deviation: 0.30`, `max_days_behind: 2`).
- A 1.0 contract stays valid input: no `exclude_weeks` means none, no `monitoring` means the defaults.
- The answers schema 1.1 only **adds** fields (`monitoring`, `payment_methods`,
  `sessions_excluded_week`). On 2026-06 a v1.1 pipeline reproduces every v1.0 field of the golden file
  (`scripts/parity.py --backcompat`).
- Monitoring compares full ISO weeks with their median (robust to the outlier it is looking for),
  for sessions and the mobile checkout-given-cart rate, and reports anomalies in `answers.monitoring`.

## Consequences
Old results stay reproducible; new readers get more fields; a broken week is visible, documented and
measurable (the uplift moves from ₹14.1 to ₹14.3 lakh/month when W31 is excluded). Removing a week
requires a post-mortem, which is the review it deserves. The median rule is simple and explainable
but weak with short histories and trends; to be revisited past 26 weeks of history.

## AI assistance
An assistant suggested an isolation-forest anomaly detector. Rejected: the median rule found the
incident, can be implemented identically in Python, SQL and R, and can be explained to a product
manager in one sentence. The real gap was frequency (see the post-mortem's action item 1).
