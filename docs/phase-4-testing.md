---
phase: 4
slug: phase-4-testing
title: "Testing the analysis: golden answers, invariants, parity, coverage"
duration: 3.5 h
start_tag: phase-3-end
end_tag: phase-4-end
---
# Phase 4 · Testing the analysis: golden answers, invariants, parity, coverage

## 1. Why it matters
Unit tests on a 14-session fixture prove each rule. They do not prove that the analysis of the real
export is right, that nothing is double-counted, or that a broken export is refused. Analysts rarely
test their work this way, which is why "the numbers changed and nobody knows why" is so common. In
this phase you switch on three kinds of **data tests**: golden answers (the whole `answers.json` on
the real export), invariants (properties that must hold for *any* export, such as "devices add up to
all"), and contract violations (a corrupted export must stop the run). You add a coverage gate, break
the analysis on purpose to see the tests catch it, and compare your track with another one.

## 2. Objectives
By the end of this phase you can:
- Explain the difference between unit tests, golden tests, invariants and contract-violation tests, and what each one cannot catch.
- Un-pend and pass the data tests of your track on the real export.
- Read a parity report and trace a difference to a rule.
- Break the analysis on purpose (a join, a rule order, a default) and show which test fails.
- Enforce an 85 % line-coverage gate and explain what coverage does not tell you.

## 3. Step-by-step instructions

### Step 4.1 · Know the layers you already have
| Layer | Where | Catches | Misses |
|---|---|---|---|
| Unit | `tests/unit`, tiny fixture | a wrong rule or formula | interactions on real data, scale |
| Golden | `tests/data/test_golden*` | any change of any number on the real export | *why* it changed |
| Invariants | `tests/data/test_invariants*` | double counting, lost rows, impossible statistics | a consistently wrong formula |
| Contract violations | `tests/data/test_contract_violations*` | a broken export analysed silently | a new defect type the contract does not know |
| Parity | `scripts/parity.py` | a track-specific bug or an ambiguous rule | an error all tracks share |

### Step 4.2 · Un-pend the data tests
Delete the three Phase 4 entries ("golden answers", "invariants", "contract violations") from your
pending list and run:

<!-- track:python -->
```bash
cd tracks/python
make coverage        # unit + data tests on data/raw/2026-06, coverage gate 85 %
```
<!-- /track -->

<!-- track:sql -->
```bash
cd tracks/sql
make coverage        # unit + data tests on data/raw/2026-06, coverage gate 85 % (the runner and SQL views)
```
<!-- /track -->

<!-- track:r -->
```bash
cd tracks/r
make coverage        # testthat on unit + data tests with covr, gate 85 %
```
<!-- /track -->

If the golden test fails, the message lists the JSON paths that differ. Fix the cause in your rules,
never the golden file: it is the value all three tracks agreed on.

### Step 4.3 · Read the invariants
Open the invariants file of your track and explain each test in one sentence in your notes. The most
useful one is *rows removed + rows kept = rows read*: for every table, the issue counts plus the clean
row count must add up to the raw row count. It turns the cleaning log into an equation, so a rule
that drops rows without counting them fails immediately.

### Step 4.4 · Break it on purpose
Make each change on a scratch branch, run `make coverage`, write down which test failed, then revert:
1. Join orders to sessions **before** removing conflicting session ids (revenue multiplies).
2. Remove exact duplicates **before** normalising labels (the duplicate count drops).
3. Use the library default with a continuity correction for the z test (the p-value moves).
4. Count a purchase for an order without a checkout (the funnel grows at the last step).

If a change breaks no test, you found a gap: write an invariant or a unit test that catches it.

### Step 4.5 · Parity with another track
Run another track's pipeline on the same export (the Python track is the easiest to install) and compare:
```bash
cd tracks/python && make install run && cd ../..
python3 scripts/parity.py contract/golden/answers-2026-06.json tracks/python/out/answers.json tracks/<yours>/out/answers.json
```
`IDENTICAL` means equal to 1e-9 relative (integers exactly). Three independent implementations that
agree are strong evidence that the rules are unambiguous and the formulas right; it is the
analysis equivalent of a second pair of eyes.

### Step 4.6 · Add one test of your own
Add one data test that protects a finding a stakeholder will quote, for example "the payment-step
odds ratio within channels is below 1 and its CI excludes 1", or "the mobile share of sessions is
between 65 % and 72 %". A finding-level test fails loudly if a future export or a refactoring changes
the story, not just a digit.

## 4. AI-assist prompts

### Prompt 1: What do my tests not prove?
```text
Here are the test names of my analysis (unit, golden, invariants, contract violations): <paste the
output of pytest --collect-only -q or the test_that names>. The analysis cleans four CSVs, builds a
funnel and runs three hypothesis tests (see <paste contract/questions.md §1>). List the five most
likely ways the analysis could be wrong while every test passes, and a test for each.
```
**Verify the output by:** implementing at most two of its suggestions and checking each new test
fails when you break the behaviour on purpose (a test that cannot fail proves nothing).

### Prompt 2: Write an invariant
```text
In my answers.json, data_quality has raw_rows, clean_rows and issues (counts of rows each cleaning
rule removed): <paste those three objects>. The rules are: <paste questions.md §2>. Write an invariant
test in <pytest | testthat> that checks removed + kept = read for each table, and explain which issue
counts must NOT be subtracted (they count kept rows).
```
**Verify the output by:** checking the assistant's list of "kept" counters against §2 (unknown
channel, out-of-order sessions and orders without checkout are kept, not removed), and running the
test against the real export.

### Prompt 3: Explain a statistical difference between two tracks
```text
Two implementations of a Welch t test give df = 2017.9 and df = 2018.0 on the same data, and p-values
that differ in the 6th digit. The contract says: <paste the Welch paragraph of §4>. What are the
possible causes (sample vs population sd, rounding, integer division, the t distribution
implementation), and how do I find which implementation follows the contract?
```
**Verify the output by:** recomputing df by hand from the four summary numbers (means, sds, ns) in
`answers.json` and checking which implementation matches; the contract's formula decides, not the
more popular library.

## 5. Deliverables
- [ ] All tests un-pended in your track; `make coverage` green with ≥ 85 % line coverage.
- [ ] Notes: one sentence per invariant, and the four "break it" experiments with the test that caught each.
- [ ] Parity `IDENTICAL` between your track, the golden answers and at least one other track.
- [ ] One finding-level data test of your own.
- [ ] A merged PR with a green CI run and an `AI_LOG.md` entry.

## 6. Self-check quiz

### Q1. The golden test passes. What does that prove?
- [ ] That the analysis is correct
- [x] That your answers.json equals the agreed reference on this export; the reference could share an error with you, which is why invariants and independent tracks exist
- [ ] That the code has no bugs
- [ ] That the next export will be analysed correctly
> **Answer:** A golden test pins behaviour; it does not prove truth. Parity across three independent implementations and invariants make a shared mistake much less likely.

### Q2. Which invariant catches a join that multiplies revenue?
- [ ] The funnel never grows
- [x] Rows removed plus rows kept equals rows read: duplicated orders make the clean count larger than the raw count minus the removed rows
- [ ] No error check fails
- [ ] Statistics are well formed
> **Answer:** A many-to-many join creates rows that no rule removed and no raw file contained, so the cleaning equation stops balancing (and the golden revenue changes too).

### Q3. You append a session with channel `referral` to a copy of the export. What must happen?
- [ ] It is counted as `unknown`
- [ ] It is silently dropped
- [x] The `sessions.channel.accepted` error check fails and the run stops with exit code 3
- [ ] The dashboard shows a warning
> **Answer:** An unknown value is a contract change, not a cleaning problem. Stopping forces a human to decide, and Phase 7 shows what happens when a real refresh does exactly this.

### Q4. Coverage is 99 %. What does that not tell you?
- [ ] Which lines ran during the tests
- [x] Whether the assertions check the right values: a line can run in a test that asserts nothing useful
- [ ] Whether the gate passes
- [ ] Which files are untested
> **Answer:** Coverage measures execution, not verification. The "break it on purpose" exercise is the real test of your tests.

### Q5. Parity reports one difference: `$.data_quality.issues.sessions_exact_duplicates: 351 != 349`. Most likely cause?
- [ ] A floating-point error
- [x] A different rule order or normalisation before deduplication (for example comparing raw labels)
- [ ] The golden file is corrupted
- [ ] The sample rate
> **Answer:** Integer differences in issue counts point at rule logic, never at floating point. Re-read §2 step 3: duplicates are compared after normalising labels and parsing timestamps.

### Q6. Why add a finding-level test ("the adjusted payment OR is below 1 with a CI excluding 1")?
- [ ] To increase coverage
- [x] So a change of the story (not just a digit) fails loudly, with a message a stakeholder would understand
- [ ] Because the golden test is not enough to run CI
- [ ] Because statsmodels requires it
> **Answer:** Golden tests fail on any change, including harmless ones after a contract update. A finding-level test says which conclusion is at risk.

## 7. What you learned
- Four layers of tests for an analysis, and what each layer cannot catch.
- Invariants that turn the cleaning log into equations.
- Mutation-style testing: break the analysis on purpose and make sure a test notices.
- Parity across independent implementations as a review tool.
- Coverage as a floor, not a proof.

## 8. Catch-up git commands
```bash
git fetch upstream --tags
git switch -c my-phase-5 phase-4-end
git diff phase-3-end phase-4-end --stat     # what the reference un-pended and added
```
