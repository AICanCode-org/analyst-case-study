---
phase: 2
slug: phase-2-design
title: "Design: data contract, analysis plan and ADRs"
duration: 3 h
start_tag: phase-1-end
end_tag: phase-2-end
---
# Phase 2 · Design: data contract, analysis plan and ADRs

## 1. Why it matters
In software, design is the architecture. In analysis, design is **deciding how the question will be
answered before the data can influence you**: which rows count, which test, which confounder, what
the output looks like and when the pipeline must refuse to produce a number. FunnelLens writes this
down in two places: a *data contract* (the rules a machine checks) and an *analysis plan* (the
reasoning a human reviews), plus one Analysis Decision Record per significant choice. Three tracks
in three languages can only agree to the ninth decimal because every rule is written down; your
future self, re-running the analysis on next month's export, depends on the same thing.

## 2. Objectives
By the end of this phase you can:
- Read a data contract critically: raw columns, cleaning rules and their order, checks and their severities.
- Write an analysis plan with hypotheses, competing explanations, metrics, tests and their assumptions, and what would change the decision.
- Explain why the primary test is a Cochran-Mantel-Haenszel test stratified by channel, and what a Simpson's paradox would look like in this funnel.
- Draw the pipeline from raw CSVs to `answers.json`, the report and the dashboard, including where it stops on a failed check.
- Record decisions as ADRs with options, consequences and the numbers they could move.

## 3. Step-by-step instructions

### Step 2.1 · Read the contract like a reviewer
Open `contract/data-contract.yaml` and `contract/questions.md` §2 side by side. For each defect you
noted in Phase 0, find the rule that handles it and the issue counter that reports it. Then answer
three questions in your notes:
1. Why are exact duplicates removed **after** normalising labels and parsing timestamps (step 3)?
   *(Hint: `DESKTOP` and `desktop` are the same session.)*
2. Why does a conflicting `session_id` lose **all** of its rows instead of keeping the first?
3. Which checks are `error` and which `warn`, and what is the difference for the business? An
   `error` means a number would be wrong (duplicate ids, an unknown device); a `warn` means a number
   is less certain (more unknown channels than usual).

### Step 2.2 · Check two rules by hand on the tiny fixture
`contract/fixtures/tiny/` has 14 sessions. Open `sessions.csv` and apply rules 1-5 of §2 with a pen
(or a spreadsheet). Compare your counts with `issues` in `contract/fixtures/tiny-expected.json`. If
you disagree, re-read the rule: the fixture is the contract's executable example, and the unit tests
in Phase 3 hold every track to it.

### Step 2.3 · Hypotheses and competing explanations
Copy `spec/analysis-plan.md` (the template is already there) and write:
- **H1 (Head of Product):** the mobile checkout loses buyers: purchase given checkout is lower on mobile.
- **H2 (traffic mix):** mobile gets more traffic from channels that convert less; within a channel,
  mobile is no worse. This would make the overall gap a mix effect (a Simpson's paradox).
- **H3 (basket size):** mobile buyers buy as often but spend less per order.

For each, write the metric and the result that would support or refute it. Notice that H1 and H2 can
both be partly true; the plan must be able to tell "partly" apart.

### Step 2.4 · Choose the tests and say why
| Question | Test | Why this one | Report |
|---|---|---|---|
| Q3 | two-proportion z test (pooled) | two independent proportions, large counts | difference + unpooled 95 % CI, z, p |
| Q4 | Cochran-Mantel-Haenszel, strata = channel | one common odds ratio across 2×2 tables, adjusting for channel | MH odds ratio + Robins-Breslow-Greenland 95 % CI, p; the crude OR next to it |
| Q5 | Welch's t test | means of skewed order values, unequal variances | difference + 95 % CI, df, p |

Write the assumptions of each (independence of sessions, enough events per stratum, no continuity
correction) and the formula reference in `contract/questions.md` §4. The CMH test is the **one**
primary test of the decision rule; the others are context. Writing that down now is your protection
against reporting whichever test "worked".

### Step 2.5 · Draw the pipeline
Add a Mermaid diagram to the plan: raw CSVs (text) → cleaning rules (with issue counts) → contract
checks (`error` → exit 3, no output) → funnel tables → tests → opportunity → decision →
`answers.json` → report / dashboard / AI narrator. GitHub renders Mermaid in Markdown, so the diagram
lives next to the text and is reviewed in the same pull request.

### Step 2.6 · Write the ADRs
Use `spec/adr/0000-template.md`. Five decisions deserve a record:
1. **Read everything as text**; the cleaning rules decide every type (no type guessing by the CSV reader).
2. **Adjust for channel with CMH** as the single primary test.
3. **One output contract for three tracks** (`answers.json` + schema), golden answers and parity to 1e-9.
4. **Contract checks with severities**: `error` stops the run (exit 3), `warn` is reported.
5. **The AI narrator sees facts, not data**: numbered aggregates in, guardrails out, a deterministic
   template when the model is absent, slow or wrong.

Each ADR names at least two real alternatives (pandas' type inference; a logistic regression with a
channel term; one track only; warnings only; letting the model read `answers.json` directly) and
the consequence you accept.

## 4. AI-assist prompts

### Prompt 1: Review my data contract
```text
Here is a data contract for an e-commerce funnel export: <paste contract/data-contract.yaml> and the
cleaning rules: <paste contract/questions.md §2>. Review it like a senior analytics engineer: which
rule order changes the result, which defect is not covered, which check has the wrong severity, and
what would silently corrupt revenue. Quote the rule for every point.
```
**Verify the output by:** testing each claimed gap against the tiny fixture or the rules text (an
assistant may claim a defect is "not handled" when §2 handles it), and turning any real gap into an
issue rather than an edit to the contract in this phase.

### Prompt 2: Explain CMH and Simpson's paradox with my numbers' shape
```text
I compare a conversion step between mobile and desktop users, stratified by acquisition channel
(email, organic, paid_social, unknown). Explain, with a small made-up example of 2x2 tables, how the
Mantel-Haenszel odds ratio can differ from the crude odds ratio, and how an overall gap can vanish or
reverse within every channel (Simpson's paradox). Then list the assumptions of the CMH test.
```
**Verify the output by:** recomputing the assistant's made-up example by hand (the MH odds ratio is
Σ(a·d/n) / Σ(b·c/n)); assistants often get the arithmetic of their own examples wrong. Check the
assumptions against `contract/questions.md` §4 and a statistics reference.

### Prompt 3: Draft an ADR, then argue against it
```text
Draft an Analysis Decision Record using this template: <paste spec/adr/0000-template.md>. Decision:
<"read every raw CSV as text and parse types in the cleaning rules">. Context: <three tracks must
agree to 1e-9; exports have amounts like "₹1,299.00" and two date formats>. Give two real
alternatives. Then write the strongest argument against the decision.
```
**Verify the output by:** checking the alternatives are real options with real costs (not straw
men), and that the consequences mention a number that could move. Keep the counter-argument in the
ADR's consequences if it is valid.

## 5. Deliverables
- [ ] Notes answering the three contract questions of Step 2.1, and your hand count on the tiny fixture.
- [ ] `spec/analysis-plan.md`: hypotheses H1-H3, metrics, tests with assumptions, the pipeline diagram, what would change the decision, threats to validity.
- [ ] At least five ADRs in `spec/adr/` (0001-0005).
- [ ] A merged PR with a green CI run and an `AI_LOG.md` entry.

## 6. Self-check quiz

### Q1. Why are exact duplicate sessions removed after normalising labels and parsing dates?
- [ ] It is faster
- [x] `DESKTOP` vs `desktop` or `2026-01-05 14:03:00` vs `05/01/2026 14:03` are the same session written differently; comparing raw text would keep both
- [ ] Because the contract checks need it
- [ ] Duplicates cannot be found in raw text
> **Answer:** Order matters. Normalise first, then compare; otherwise "duplicates" depend on formatting accidents and the counts differ between tracks.

### Q2. Two rows share a `session_id` but have different devices. What does the contract do, and why?
- [ ] Keep the first row
- [ ] Keep the row with the latest timestamp
- [x] Drop all rows of that id and count it: there is no way to know which row is true, and guessing would bias the device comparison
- [ ] Stop the pipeline
> **Answer:** A conflicting id is ambiguous evidence. Dropping it (and counting it in `sessions_conflicting_ids`) is honest and reproducible; the count is small enough not to matter, and the check proves it.

### Q3. What makes the CMH test the right primary test here?
- [ ] It is the most famous test
- [x] It compares mobile vs desktop within each channel and combines the strata into one odds ratio, removing confounding by channel mix
- [ ] It works without any data cleaning
- [ ] It always gives smaller p-values
> **Answer:** The question is "is mobile worse for comparable users?". Stratifying by the known confounder and pooling with Mantel-Haenszel answers exactly that; the crude odds ratio is reported alongside to show how much the mix mattered.

### Q4. Mobile carts less often overall, but within every channel mobile carts as often as desktop. What is this?
- [ ] A bug in the funnel
- [x] A Simpson's paradox: the aggregate gap comes from the channel mix, not from the device
- [ ] Proof the checkout is broken
- [ ] Regression to the mean
> **Answer:** When groups have different mixes of a variable that affects the outcome, the aggregate can disagree with every subgroup. The `simpson` section of answers.json reports both so a reader sees it.

### Q5. An `error` check fails. What happens?
- [ ] A warning is printed and the analysis continues
- [x] The pipeline stops with exit code 3 before writing answers.json: a wrong number is worse than no number
- [ ] The failing rows are deleted automatically
- [ ] The check is retried
> **Answer:** `error` checks guard invariants that, if broken, make results wrong (duplicate ids, unknown devices). `warn` checks report degraded certainty and let the run finish.

### Q6. Why does the AI narrator get numbered facts instead of answers.json or the raw data?
- [ ] Models cannot read JSON
- [ ] It is cheaper
- [x] Facts are aggregates only (privacy), and numbering them lets guardrails check every citation and every number the model writes
- [ ] Because the template needs them
> **Answer:** The smaller and more structured the model's input, the easier it is to verify its output. ADR-0005 records this, and Phase 6 implements the guardrails.

## 7. What you learned
- A data contract makes cleaning rules, checks and severities machine-checkable; the order of rules changes numbers.
- An analysis plan fixes hypotheses, metrics, tests and the decision before the data can influence them.
- Stratification (CMH) addresses a known confounder, and Simpson's paradox is what it protects against.
- ADRs make analysis decisions reviewable: alternatives, consequences, the numbers they move.
- A tiny hand-checkable fixture is the executable example of the contract.

## 8. Catch-up git commands
```bash
git fetch upstream --tags
git switch -c my-phase-3 phase-2-end
git diff phase-1-end phase-2-end --stat        # the plan and the ADRs of the reference
git show phase-2-end:spec/analysis-plan.md | less
```
