---
phase: 7
slug: phase-7-observability
title: "Data refresh, monitoring and a post-mortem"
duration: 3 h
start_tag: phase-6-end
end_tag: phase-7-end
release: v1.1.0
---
# Phase 7 · Data refresh, monitoring and a post-mortem

## 1. Why it matters
The memo went out; the Head of Product approved the experiment and asked for the numbers again on
the **August export (2026-08)**. You run the same pipeline on the new folder and it stops:
`data contract violated: sessions.channel.accepted (878 rows)`. That is the contract doing its job.
Behind it are three real-world changes: marketing launched a **referral** programme, orders now carry
a **payment method**, and app release **8.14** silently lost about 70% of mobile checkout events
for one week. In analytics, the dangerous failures are the silent ones. This phase adds a versioned
contract, data-quality **monitoring** over time, an incident **post-mortem**, and release **v1.1.0**,
without breaking anyone who reads v1.0 answers.

## 2. Objectives
By the end of this phase you can:
- Diagnose a failing pipeline from its exit code and the failing check, and decide whether the data or the contract is wrong.
- Evolve the data contract with a version (1.0.0 → 1.1.0), keep the old version, and keep the answers schema backward compatible.
- Add monitoring: freshness, weekly metrics against their median, anomalies; report them without stopping the run.
- Exclude a week of broken tracking explicitly, with a post-mortem, and quantify what it changes.
- Prove backward compatibility: v1.1 reproduces the v1.0 golden file on 2026-06, and the v1.0 dashboard reads v1.1 answers.

## 3. Step-by-step instructions

### Step 7.1 · Run v1.0 on the new export
```bash
git switch -c my-phase-7 phase-6-end
ls data/raw/2026-08 && cat data/README.md | head -40      # the new data dictionary
cd tracks/<yours> && make run DATA=../../data/raw/2026-08; echo "exit $?"
```
Exit code 3 (contract violated) and the check id `sessions.channel.accepted` with 878 rows. Query the
rows (`SELECT channel, count(*) …`): they are all `referral`, a new, legitimate channel. The data is
right; the contract is out of date. Write that down before touching anything.

### Step 7.2 · Version the contract (1.1.0)
1. Copy `contract/data-contract.yaml` to `contract/history/data-contract-1.0.0.yaml` (never edited again).
2. In the live contract: `version: "1.1.0"`, add `referral` to the accepted channels, and add a
   `monitoring` section (`max_relative_deviation: 0.30`, `max_days_behind: 2`).
3. Read `contract/questions.md` §6 and the `(v1.1)` notes in the cleaning steps; read
   `spec/adr/0006-versioned-contract-and-monitoring.md`.
4. A pipeline must still accept a 1.0 contract: missing `monitoring` means the defaults, missing
   `exclude_weeks` means no exclusion. Add a unit test for that.

<!-- track:python -->
`funnellens/monitoring.py`: `full_weeks()`, `monitoring()` and `payment_methods()`; `clean.py` drops
excluded weeks after the other session rules and counts `sessions_excluded_week`.
<!-- /track -->
<!-- track:sql -->
`sql/06_monitoring.sql` and `sql/07_payment_methods.sql`; the runner passes `exclude_weeks` and the
monitoring thresholds as parameters (`cfg_exclude_weeks`), so the SQL stays declarative.
<!-- /track -->
<!-- track:r -->
`R/monitoring.R` (`monday_of()`, `full_weeks()`, `monitoring()`, `payment_methods()`); `clean.R`
records the exclusion in `ISSUE_ORDER` so the issue counts stay in contract order.
<!-- /track -->

### Step 7.3 · Monitoring finds what the checks missed
Run v1.1 on 2026-08 **without** excluding any week first (`exclude_weeks: []`). Every check passes
except one warning: `orders.without_checkout.ratio` (113 orders, 3.3%). Then look at
`answers.monitoring.anomalies`:

| week | metric | value | median | deviation |
|---|---|---|---|---|
| 2026-W31 | mobile_checkout_given_cart | 0.107 | 0.534 | −80% |

Mobile users did not stop paying (orders exist without a checkout event: that is the warning).
The **tracking** broke. The release notes confirm it: app 8.14 shipped on Monday of W31 and the
hotfix 8.14.1 the next Monday. Weekly monitoring turned a vague warning into a dated cause.

### Step 7.4 · Exclude the week, and write the post-mortem
Add `exclude_weeks: ["2026-W31"]` with a comment that names the incident. Re-run: 1,218 sessions
excluded, no warning, no anomaly. Then write `docs/postmortem-2026-W31.md` in the blameless format
(summary, impact, timeline, root cause, detection, what went well, what went badly, action items
with owners). Quantify the impact on the decision: with W31 left in, the payment-step uplift moves by
about ₹0.2 lakh/month and the recommendation does not change, but the weekly chart shows a false
collapse that a reader could take for a real drop. With W31 excluded, the CMH odds ratio is 0.725
and the uplift ₹14.3 lakh/month: still `run_targeted_experiment`.

### Step 7.5 · Payment methods
The new `payment_method` column answers a question the experiment design needs: which methods mobile
users choose (UPI 1,252, card 413, COD 267, net banking 140 orders). The experiment should test the
redesigned payment step on UPI first. `payment_methods` is `null` on exports without the column.

### Step 7.6 · Golden file, backward compatibility, parity
```bash
make coverage                     # unit + data tests, incl. the golden subset on 2026-08 (repo: tracks/<yours>)
make run DATA=../../data/raw/2026-08
python3 ../../scripts/parity.py ../../contract/golden/answers-2026-08.json out/answers.json      # IDENTICAL
make run DATA=../../data/raw/2026-06 OUT=/tmp/fl-2026-06
python3 ../../scripts/parity.py --backcompat ../../contract/golden/answers-2026-06.json /tmp/fl-2026-06/answers.json
```
The v1.0 dashboard must still render v1.1 answers (the schema only adds fields): try it with the
`phase-6-end` image. The v1.1 dashboard adds a **Monitoring** tab and two facts for the narrator.

> **A parity story worth telling.** When the three tracks were first compared on 2026-08, the SQL track
> counted `sessions_unknown_channel` after excluding the week and Python before it. Both followed the
> spec, because the spec did not say. The fix was a sentence in `questions.md` (count after step 9),
> not code in one track. Ambiguity in a spec shows up as a parity failure: that is what parity is for.

### Step 7.7 · Release v1.1.0
Update the runbook (a "data refresh" section: run, read the exit code, read the monitoring tab,
decide: data issue, contract change or incident), the CHANGELOG (`## [1.1.0]`: Added, Changed,
Fixed), the default export (`EXPORT=2026-08` in `.env.example` and the Makefiles), then tag `v1.1.0`.

## 4. AI-assist prompts

### Prompt 1: Diagnose the failing refresh
```text
My analysis pipeline stopped with "data contract violated: sessions.channel.accepted (878 rows)" on a
new monthly export. Here is the contract section and a sample of the failing rows: <paste>. List the
possible explanations (data error, upstream change, contract out of date), what query would tell them
apart, and what I should change in each case. Do not propose relaxing the check without evidence.
```
**Verify the output by:** running the query it suggests yourself and checking the answer against the
data dictionary of the new export. Reject any fix that makes the check pass by deleting it or by
mapping `referral` to `unknown`.

### Prompt 2: Design the monitoring rule
```text
I want to flag weeks whose data looks broken: weekly sessions and the mobile checkout-given-cart rate
compared with their median over the full weeks of the month, flagged above a 30% relative deviation.
Here are the weekly values: <paste>. What are the weaknesses of this rule (partial weeks, small
counts, seasonality, a real change versus broken tracking), and what would a stronger rule look like?
```
**Verify the output by:** computing the deviations by hand for two weeks and comparing with
`answers.monitoring`, and checking that partial weeks are excluded as the spec says. Record one
weakness in the post-mortem's "what went badly" or action items.

### Prompt 3: Review my post-mortem
```text
Review this post-mortem for a data incident: <paste docs/postmortem-2026-W31.md>. Check that it is
blameless, that the timeline has times and sources, that the impact on the decision is quantified,
and that each action item is specific, owned and verifiable. List what is missing; do not rewrite it.
```
**Verify the output by:** checking each of its claims against the incident data (dates, counts,
deviations) and the CHANGELOG; add only the items you agree with, and note in `AI_LOG.md` which ones
you rejected and why.

## 5. Deliverables
- [ ] `contract/history/data-contract-1.0.0.yaml` and the live contract 1.1.0 (referral, exclude_weeks, monitoring).
- [ ] Monitoring and payment methods implemented and tested in your track; a 1.0 contract still accepted.
- [ ] `golden/answers-2026-08.json`, backward compatibility on 2026-06, parity `IDENTICAL`.
- [ ] `docs/postmortem-2026-W31.md`, ADR-0006, the runbook update.
- [ ] `CHANGELOG.md` 1.1.0 and the tag `v1.1.0`.

## 6. Self-check quiz

### Q1. The v1.0 pipeline exits 3 on the August export. What is the right first move?
- [ ] Remove the failing check
- [ ] Map unknown channels to `unknown`
- [x] Look at the failing rows and find out whether the data or the contract is wrong
- [ ] Re-run until it passes
> **Answer:** The contract stopped the run on purpose. Here the rows are a legitimate new channel, so the contract changes, with a new version and a note.

### Q2. Why is the old contract kept in `contract/history/`?
- [ ] Git cannot show old versions
- [x] Old answers files cite `contract_version 1.0.0`; keeping it lets anyone reproduce them and lets the pipelines test that a 1.0 contract still works
- [ ] The dashboard reads it
- [ ] It is required by YAML
> **Answer:** A versioned contract is part of the reproducibility of every past result.

### Q3. All checks pass except a 3.3% warning. Why was W31 still a problem?
- [ ] It was not: warnings can be ignored
- [x] Row-level checks look at the month as a whole; only the weekly view showed that mobile checkout-given-cart collapsed by 80% in one week
- [ ] W31 had too many sessions
- [ ] The warning threshold was wrong
> **Answer:** Checks validate rows; monitoring validates behaviour over time. You need both.

### Q4. Why exclude W31 instead of "fixing" its missing checkout events?
- [ ] Excluding is faster
- [x] The lost events cannot be recovered; imputing them would invent data, while excluding a documented week is transparent and its effect can be measured
- [ ] The contract forbids changes to events
- [ ] W31 is a holiday
> **Answer:** Exclusion with a post-mortem and a quantified impact is honest; imputation of a broken funnel step would bias the very metric under study.

### Q5. What does "backward compatible" mean for answers schema 1.1?
- [ ] v1.1 answers are identical to v1.0 answers
- [x] It only adds fields: a v1.0 reader still works, and on the old export every v1.0 field keeps its value
- [ ] It removes unused fields
- [ ] It can only be read by the v1.1 dashboard
> **Answer:** `--backcompat` compares every v1.0 field on 2026-06, and the v1.0 dashboard renders v1.1 answers.

### Q6. Parity failed on a count during the refresh. What did that reveal?
- [ ] A bug in DuckDB
- [ ] That one track should be deleted
- [x] An ambiguity in the spec: two correct readings gave two numbers, so the spec was clarified
- [ ] That parity checks are too strict
> **Answer:** Independent implementations are an excellent spec review. The fix was one sentence in `questions.md`.

## 7. What you learned
- A failing contract check is information: diagnose before you change anything.
- Versioned contracts and additive schemas keep old results reproducible and old readers working.
- Weekly monitoring against a median finds silent tracking failures that row checks miss.
- Blameless post-mortems with a quantified impact on the decision.
- Independent implementations (parity) expose ambiguities in a spec.

## 8. Catch-up git commands
```bash
git fetch upstream --tags
git switch -c my-phase-8 phase-7-end      # = v1.1.0
git diff phase-6-end phase-7-end --stat
```
