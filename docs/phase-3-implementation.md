---
phase: 3
slug: phase-3-implementation
title: Implementation in five milestones
duration: 12 h
start_tag: phase-2-end
end_tag: phase-3-end
---
# Phase 3 · Implementation in five milestones: load, clean, explore, test, decide

## 1. Why it matters
This is where the old guide's "Load and Clean", "Explore" and "Test the Hypothesis" happen, but
**test-first**: for every rule and every formula a test already says what the right answer is, on a
fixture small enough to check by hand. You switch the tests on one milestone at a time, watch them
fail, and make them pass. By the end, your track turns the raw export into an `answers.json` that the
decision rule reads, and your report (notebook, SQL report or R Markdown) tells the story from it.
Nothing is copied from an assistant without a test agreeing with it.

## 2. Objectives
By the end of this phase you can:
- Load raw CSVs as text and implement the cleaning rules of `contract/questions.md` §2 in order, counting every row each rule changes.
- Implement the data-contract checks and stop the pipeline on a failing `error` check.
- Build the session funnel by device, channel and week, and find the Simpson's paradox in the cart step.
- Implement the two-proportion z test, the Cochran-Mantel-Haenszel test with the Robins-Breslow-Greenland interval and Welch's t test, and match hand-computed cases to 1e-9.
- Size the opportunity, apply the decision rule and write a report that runs top to bottom.

## 3. Step-by-step instructions

### Step 3.1 · The red → green loop
Work on a branch per milestone (`feat/m1-clean`). For each milestone:
1. Delete its lines from the pending list (`tests/conftest.py`, or `PENDING` in
   `tests/testthat/helper-funnellens.R`).
2. Run `make test`: the group fails with `TODO(Mx)` errors. Each stub has a hint naming the rule,
   the trap and the test file.
3. Implement until `make test` is green, run `make lint`, commit, open a PR.

<!-- track:python -->
Python: the stubs are in `funnellens/{load,clean,checks,metrics,stats,answers}.py`. Run one file
with `.venv/bin/pytest tests/unit/test_clean.py -x -q`; `-x` stops at the first failure.
<!-- /track -->

<!-- track:sql -->
SQL: the stubs are the views and tables in `sql/02_clean.sql` … `sql/05_answers.sql` (`SELECT NULL
AS todo`) and the check templates in `sql/checks/`. `01_load.sql` is complete: it loads every CSV as
text. The Python runner is complete too: it sets the variables (`getvariable('period_start')`),
loads the contract lists into `cfg_*` tables, renders the checks and turns your result views into
`answers.json`. Run `.venv/bin/pytest tests/unit/test_clean.py -x -q`, and explore any view with
`.venv/bin/python -m funnellens_sql report --data ../../contract/fixtures/tiny --out /tmp/tiny`.
<!-- /track -->

<!-- track:r -->
R: the stubs are in `R/{load,clean,checks,metrics,stats,answers}.R`. Load the package with
`pkgload::load_all()` and run one file with
`testthat::test_file("tests/testthat/test-unit-clean.R")`, or everything with `make test`.
<!-- /track -->

### Step 3.2 · M1 · Load and clean
Un-pend **"Phase 3 M1 - load the raw export as text"** and **"Phase 3 M1 - cleaning rules and the
issue counts"**. Implement in the order of §2: users, sessions (steps 1-8), events, orders. Rules
that are easy to get subtly wrong, and which the tests pin:
- **Timestamps:** exactly two formats; `05/01/2026 14:03` is 5 January. An impossible date is a bad
  timestamp, not a guess.
- **Amounts:** whole **paise** as integers (`₹1,299.00` → 129900). Floats for money drift; integer
  paise sum exactly in every language.
- **Duplicates:** exact duplicates after normalisation keep one row; a conflicting id loses all rows.
- **The join trap:** joining orders to sessions on a key that is not unique multiplies revenue.
  Check uniqueness before every join and compare row counts before and after.

<!-- track:python -->
```python
# pandas raises instead of silently multiplying rows:
orders.merge(sessions[["session_id", "device"]], on="session_id", how="inner", validate="many_to_one")
```
<!-- /track -->

<!-- track:sql -->
```sql
-- the cleaning steps are views, so you can count every step:
SELECT (SELECT count(*) FROM s2_parsed) - (SELECT count(*) FROM s3_deduplicated) AS exact_duplicates;
```
<!-- /track -->

<!-- track:r -->
```r
# dplyr warns about many-to-many joins; make the expectation explicit:
dplyr::inner_join(orders, sessions[, c("session_id", "device")], by = "session_id",
                  relationship = "many-to-one")
```
<!-- /track -->

### Step 3.3 · M2 · Contract checks
Un-pend **"Phase 3 M2 - data-contract checks"**. Each check type is a small function (or SQL
template) that returns the failing-row count and, for ratio checks, the observed ratio. Checks run in
contract order on the clean tables; `raise_on_errors` stops with a contract error when an `error`
check fails, and the command line turns that into exit code 3. Run your pipeline on the real export
now (`make run`): it should stop at the first unimplemented step, not with a wrong number.

### Step 3.4 · M3 · Explore: the funnel by device, channel and week
Un-pend **"Phase 3 M3 - funnel by device, channel and week"**. This is the old "Explore" step,
made precise: a session reaches a step only if it reached the previous one; a purchase is a session
with an order. Before moving on, look at your own numbers on the real export:
1. Where does mobile diverge from desktop: everywhere, or at one step?
2. Split by channel. Does mobile carry more `paid_social` traffic? Is mobile's cart rate lower
   *within* each channel, or only overall?
3. Plot sessions and conversion per week. A break or a backfill would invalidate any comparison
   across the period.

Write two or three candidate explanations, ranked by how well this evidence supports them, in your
report. You should find that the overall cart gap is mostly **channel mix**, while the payment step
is worse on mobile within every channel.

### Step 3.5 · M4 · Test the hypothesis
Un-pend **"Phase 3 M4 - two-proportion z, CMH and Welch tests"**. Implement the formulas of §4.
`contract/fixtures/stats-cases.json` has hand-computed cases (including a stratum with a zero cell
and unequal variances) that every track must match to 1e-9.

<!-- track:python -->
Use the libraries, then prove them against the cases: `statsmodels.stats.proportion.proportions_ztest`,
`statsmodels.stats.contingency_tables.StratifiedTable` (`oddsratio_pooled`, `test_null_odds(correction=False)`)
and `scipy.stats.ttest_ind(equal_var=False)`. Check which defaults differ from the contract (the CI of
the z test is unpooled; the RBG variance is computed explicitly).
<!-- /track -->

<!-- track:sql -->
Write the formulas in SQL: `04_stats.sql` aggregates the 2×2 tables per stratum and computes E, V,
R, S, P, Q with plain arithmetic. DuckDB has no normal or t distribution, so the runner registers
three scalar functions you can call from SQL: `erfc(x)`, `t_two_sided_p(t, df)` and `t_quantile(p, df)`
(`funnellens_sql/mathfn.py`, standard library only).
<!-- /track -->

<!-- track:r -->
Base R has what you need, with two traps: `stats::prop.test` applies a continuity correction unless
you pass `correct = FALSE` (its χ² is then z², and it gives no unpooled Wald interval: compute that
yourself); `stats::mantelhaen.test(correct = FALSE)` gives the CMH statistic and the MH odds ratio,
but its interval uses `qnorm(0.975)`: recompute the Robins-Breslow-Greenland interval with the
contract's `z_975` so every track agrees to 1e-9. `stats::t.test(var.equal = FALSE)` is Welch's test.
<!-- /track -->

### Step 3.6 · M5 · Opportunity, decision and answers.json
Un-pend **"Phase 3 M5 - answers.json and the decision"** and **"Phase 3 M5 - command line and exit
codes"**. Size the opportunity per §5 (remember the sample rate), apply the decision rule mechanically
and assemble `answers.json` exactly as the schema says. Then:
```bash
make run                                                  # out/answers.json
python3 ../../scripts/parity.py ../../contract/golden/answers-2026-06.json out/answers.json
```
Parity will probably report differences first. Each one is a precise pointer
(`$.by_channel.cmh.purchase_given_checkout.ci95[0]`): fix the rule, never the golden file. The data
tests that pin the full export stay pending until Phase 4.

### Step 3.7 · The report: the old "Present" step
Fill in the skeleton report. Each question gets the evidence (a table or a chart computed from
`answers.json` or your package), one paragraph of interpretation with the interval, and the caveat.
End with the recommendation and a chart that would work on a slide with no verbal explanation (for
example the payment-step rate by channel and device).

<!-- track:python -->
`notebooks/analysis.ipynb`: `make report` executes it top to bottom into `out/` and fails on any
error. Never rely on cells run out of order: restart the kernel and run all before you commit.
<!-- /track -->

<!-- track:sql -->
`make report` writes `out/report.md` with every result view as a table. Add your interpretation to
the README of your fork or a `report/` page that quotes those tables.
<!-- /track -->

<!-- track:r -->
`report/analysis.Rmd`: `make report` knits it to HTML from a fresh R session. Inline numbers with
`` `r pct(x)` `` so the text cannot drift from the computation.
<!-- /track -->

## 4. AI-assist prompts

### Prompt 1: Implement one rule, test-first
```text
I am implementing this cleaning rule in <pandas | DuckDB SQL | R with dplyr>: <paste the rule from
contract/questions.md §2>. Here is the failing test and its fixture rows: <paste the test and the
relevant tiny/*.csv lines>. Write the smallest implementation that makes the test pass, and explain
which part of the rule each line implements. Do not change the test.
```
**Verify the output by:** running the test (it must pass for the right reason: check the issue count
too, not just the rows), then running the whole unit suite, because a rule changed early changes
every count after it. Reject code that "simplifies" the rule order.

### Prompt 2: Check my statistics against the formula
```text
Here is the contract's formula for the Cochran-Mantel-Haenszel test with the Robins-Breslow-Greenland
interval: <paste §4>. Here is my implementation: <paste>. Here are three hand-computed cases with
expected values: <paste two cases of stats-cases.json>. Walk through case 1 step by step, compare with
what my code computes, and point at any line that disagrees with the formula.
```
**Verify the output by:** running the stats unit tests (they compare to 1e-9); if the assistant's
step-by-step numbers disagree with `stats-cases.json`, the file wins: it was computed independently.

### Prompt 3: Explain a parity difference
```text
My answers.json differs from the golden answers here: <paste the parity.py output>. The rule for these
fields is: <paste the relevant questions.md section>. My code for it is: <paste>. List the possible
causes in order of likelihood (rule order, null handling, integer vs float, a join), and for each one
the quickest check.
```
**Verify the output by:** running each check it proposes and fixing only the confirmed cause; then
re-run parity and the unit tests. Never edit the golden file to make parity pass.

## 5. Deliverables
- [ ] All unit test groups un-pended and green in your track (`make test`); `make lint` clean.
- [ ] `make run` writes `out/answers.json`, and `scripts/parity.py` against the golden answers says `IDENTICAL`.
- [ ] The report runs top to bottom (`make report`) and answers Q1-Q8 with intervals and caveats.
- [ ] One slide-ready chart and two or three ranked candidate explanations in the report.
- [ ] One PR per milestone, each with a green CI run, and `AI_LOG.md` entries for the prompts you used.

## 6. Self-check quiz

### Q1. Why are amounts stored as whole paise (integers) instead of rupees (floats)?
- [ ] Integers use less memory
- [x] Integer sums are exact in every language, so revenue totals agree across tracks; floats accumulate rounding error
- [ ] The contract forbids decimals
- [ ] Paise are easier to read
> **Answer:** Money in floating point drifts (0.1 + 0.2 ≠ 0.3). Integer paise make `revenue_paise` identical in pandas, DuckDB and R, and conversion to rupees happens only when a mean is computed.

### Q2. After joining orders to sessions, revenue is 7 % higher than the sum of orders. What is the most likely cause?
- [ ] Refunds were removed
- [x] The session key was not unique on the session side, so some orders were duplicated by the join
- [ ] The sample rate was applied twice
- [ ] Orders without checkout were kept
> **Answer:** A many-to-many join silently multiplies rows. Check uniqueness first, and use `validate="many_to_one"` (pandas) or `relationship = "many-to-one"` (dplyr) so the join fails instead.

### Q3. Mobile's cart rate is lower overall but not within channels; its payment rate is lower within every channel. What does the evidence support?
- [ ] The whole mobile funnel is broken
- [ ] Nothing: the results contradict each other
- [x] The cart gap is mostly channel mix, while the payment step is a genuine mobile gap among comparable users
- [ ] Desktop users are lying
> **Answer:** Stratifying separates the two effects. That is exactly why `decision.reasons` can contain both `adjusted_payment_gap_significant` and `aggregate_cart_gap_is_channel_mix`.

### Q4. Your z-test p-value differs from the golden file in the 4th digit. What is the first thing to check?
- [ ] Whether the golden file is outdated
- [x] Whether your library applies a default the contract does not (for example a continuity correction, or a pooled variance where the contract uses unpooled)
- [ ] Whether your computer is 32-bit
- [ ] Whether the sample is too small
> **Answer:** Library defaults are the most common cause of "almost equal" statistics. The contract writes the formula; `stats-cases.json` shows the exact expected values.

### Q5. The CMH p-value is far below 0.05 and the uplift is ₹16 lakh a month. What does the decision rule say?
- [ ] Rebuild the checkout: the gap is highly significant
- [x] Run a targeted experiment: the gap is real but worth less than the ₹25 lakh rebuild threshold
- [ ] Do not rebuild: the gap is not significant
- [ ] Collect more data
> **Answer:** Significance says the gap is unlikely to be noise; the threshold says whether closing it pays for a rebuild. An experiment on the payment step tests fixes at a fraction of the cost.

### Q6. Why must the report run top to bottom from a clean state?
- [ ] Jupyter and R Markdown require it
- [x] Cells run out of order (or objects left in a session) can produce results the code no longer reproduces; a clean run is the only proof
- [ ] It makes the report shorter
- [ ] CI cannot read notebooks otherwise
> **Answer:** Hidden state is the classic notebook bug. `make report` restarts from nothing; Phase 5 makes CI do the same on every push.

## 7. What you learned
- Test-first analysis: every rule and formula pinned on a hand-checkable fixture before it touches real data.
- Defensive cleaning: text-first loading, counted rules, integer money, uniqueness before joins.
- Exploration with a purpose: funnel by device, channel and week, and how stratification exposes a Simpson's paradox.
- Three hypothesis tests implemented exactly, including the library defaults that silently change results.
- A mechanical decision rule, a parity check against golden answers, and a report that runs from scratch.

## 8. Catch-up git commands
```bash
git fetch upstream --tags
git switch -c my-phase-4 phase-3-end
# Compare one milestone of your track with the reference:
git diff phase-3-end -- tracks/python/funnellens/clean.py
git diff phase-3-end -- tracks/sql/sql/04_stats.sql
git diff phase-3-end -- tracks/r/R/stats.R
```
