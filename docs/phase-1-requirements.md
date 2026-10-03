---
phase: 1
slug: phase-1-requirements
title: "Requirements: questions, decisions and acceptance criteria"
duration: 2 h
start_tag: phase-0-end
end_tag: phase-1-end
---
# Phase 1 · Requirements: questions, decisions and acceptance criteria

## 1. Why it matters
Most analyses fail before the first line of code: they answer a question nobody asked, or they never
say what result would change the decision. "Rebuild the mobile checkout" is a stakeholder's
*solution*. Your first job is to turn it into questions the data can answer, a **decision rule agreed
before anyone looks at the numbers**, and acceptance criteria a reviewer can check. Writing the rule
first is what stops an analysis from being bent, consciously or not, towards the answer someone
wants (the "garden of forking paths"). The result is `spec/requirements.md`, one page a Head of
Product, an engineering lead and a finance partner can all sign.

## 2. Objectives
By the end of this phase you can:
- Map the stakeholders of a decision, what each needs and what each would like the answer to be.
- Turn a proposed solution into 5-8 measurable questions, each linked to a metric and a `contract/questions.md` section.
- Write a decision rule with a significance level and a minimum business effect (₹ per month) before seeing the data, and justify both numbers.
- State what an observational, sampled export can and cannot establish.
- Write testable acceptance criteria and a risk list for an analysis, and file the questions as GitHub issues.

## 3. Step-by-step instructions

### Step 1.1 · Map the stakeholders
Copy the headings of `spec/requirements.md` (they are already there with `TODO`s). For at least four
stakeholders (Head of Product, mobile engineering lead, finance, marketing), write one line each:
*what they need from you* and *what they hope you will find*. Notice the conflicts: the Head of
Product hopes the checkout is the problem; marketing would rather it was not the traffic it buys.
Naming these hopes up-front is how you stay independent of them.

### Step 1.2 · From "rebuild it" to questions
Ask *why* until you reach something measurable. "Mobile revenue is flat" → "is mobile's revenue
share lower than its session share?" → "at which funnel step does mobile lose people?" → "is that step
worse for mobile users who arrived the same way as desktop users?". For each question, write the
metric and its exact definition. The eight questions of `contract/questions.md` §1 are the agreed set
for this course; your job is to understand why each is there and what decision depends on it. Add
one question of your own to "Out of scope" if it cannot be answered with this export.

### Step 1.3 · The decision rule, before the data
Write down, *now*, which result leads to which recommendation:
1. If the payment-step gap is **not** significant after adjusting for acquisition channel
   (α = 0.05): **do not rebuild** (`no_checkout_gap_found`).
2. If it is significant and closing it would be worth **at least ₹25 lakh a month**: **rebuild**.
3. If it is significant but worth less: **run a targeted experiment** on the payment step first.

Justify the numbers in one line each: α = 0.05 is the team's convention for a one-off decision; a
rebuild costs about a quarter of a squad (≈ ₹75 lakh fully loaded) and must pay back within three
months, hence ₹25 lakh a month. Both are in `contract/data-contract.yaml` (`analysis:`) so code and
memo use the same numbers. Changing them after seeing the results needs a written reason.

### Step 1.4 · What the data can and cannot say
Write §5 of the requirements: six months, a 1-in-20 sample of sessions (so counts must be scaled by
20 for business figures), one country, and **observational**: users chose their device and channel,
nobody randomised them. That means an association, however significant, is not proof that the
checkout *causes* the gap. Say so now; the memo will repeat it.

### Step 1.5 · Acceptance criteria and risks
Write at least eight acceptance criteria a reviewer can check without trusting you, for example:
"`make report` runs top to bottom from a clean checkout", "every cleaning rule reports how many rows
it changed", "a failing `error` check stops the run with exit code 3 before any number is written",
"the three tracks produce identical `answers.json` (1e-9)", "every effect is reported with a 95 %
interval", "the memo states the recommendation and the observational caveat". Then at least five
risks with the mitigation: confounding by channel, Simpson's paradox, a join that multiplies
revenue, peeking at many cuts until one is significant, a tracking break, an AI summary that
invents a number.

### Step 1.6 · One issue per question
Create one GitHub issue per question with the **Analysis question** template ("As a Head of
Product, I want to know whether mobile pays less after checkout, within the same channel, so that I
can decide on the rebuild"), with acceptance criteria and an estimate. Link the issues from the
requirements file. Commit on a branch, open a PR, merge when CI is green.

## 4. AI-assist prompts

### Prompt 1: Play the stakeholder
```text
You are the Head of Product of a mid-sized Indian e-commerce company. Mobile is ~69 % of sessions but
~61 % of revenue, and you are convinced the mobile checkout is broken. I am your new analyst. Answer my
questions in character, in 2-3 sentences each, and push back when I try to delay. Stay consistent:
do not invent data I could check. My first question: what decision will you take, and by when?
```
**Verify the output by:** writing down the decision, deadline and constraints it gave you and
checking they are consistent with the brief; anything new (a deadline, a budget) is role-play, not a
fact, and must be confirmed with the real stakeholder (here: the brief and `data-contract.yaml`).

### Prompt 2: Make my questions measurable
```text
Here are my draft analysis questions and the data dictionary: <paste your questions and data/README.md>.
For each question: (1) the metric that answers it, with numerator, denominator and unit of analysis,
(2) whether this export can answer it, (3) the confounder that could fake the result. Flag any
question that is really a solution in disguise.
```
**Verify the output by:** checking each metric against `contract/questions.md` (same numerator and
denominator?) and rejecting any metric that needs data the export does not have (for example
page-load times or app versions).

### Prompt 3: Attack my decision rule
```text
Here is my decision rule for a checkout-rebuild decision: <paste §4 of your requirements>. Act as a
sceptical finance partner and a sceptical statistician. List the ways this rule could lead to a
wrong decision (thresholds, multiple comparisons, sampling, observational data) and what I should add.
```
**Verify the output by:** keeping only objections you can explain in your own words, and checking
that each one is either handled by the plan (channel adjustment, a single pre-registered test, a
threshold in rupees) or written down as a risk. Do not let it talk you into changing the thresholds
without a business reason.

## 5. Deliverables
- [ ] `spec/requirements.md` without `TODO`s: decision, stakeholders, questions, decision rule, data limits, acceptance criteria, risks, out of scope.
- [ ] The decision rule states α, the ₹ threshold and where each number comes from.
- [ ] At least eight testable acceptance criteria and five risks with mitigations.
- [ ] One GitHub issue per question, linked from the requirements.
- [ ] An `AI_LOG.md` entry for at least one prompt, with what you rejected.

## 6. Self-check quiz

### Q1. Why write the decision rule before computing anything?
- [ ] It makes the analysis faster
- [x] So the result cannot bend the rule: thresholds chosen after seeing the numbers invite picking the ones that give the hoped-for answer
- [ ] Because the rule is needed to load the data
- [ ] Because GitHub requires it
> **Answer:** Pre-registering the rule (and the test) is the analyst's defence against the garden of forking paths: with enough cuts and thresholds, any dataset "supports" any decision.

### Q2. Where does the ₹25 lakh a month threshold come from?
- [ ] It is the industry standard for checkouts
- [ ] It is the largest uplift in the data
- [x] From the cost of the rebuild (≈ ₹75 lakh of engineering) and the agreed three-month payback
- [ ] From the p-value
> **Answer:** A business threshold comes from the business case, not from the data. It is recorded in the contract so the code, the memo and the dashboard all use the same number.

### Q3. The export is a 1-in-20 sample of sessions. What does that change?
- [ ] Nothing: rates are the same
- [x] Rates and tests are fine on the sample, but counts and rupee figures must be scaled by 20 to describe the business
- [ ] The p-values must be multiplied by 20
- [ ] The sample cannot be used for statistics
> **Answer:** Proportions estimated from a random sample are unbiased; totals are not. The opportunity sizing (Q7) divides by `sample_rate`.

### Q4. Why is "mobile has a lower purchase rate after checkout" not proof that the checkout causes it?
- [ ] Because the sample is too small
- [x] Because the data is observational: mobile and desktop users differ (for example in how they arrived), and such differences can produce the gap
- [ ] Because purchase is not an event in the data
- [ ] Because p-values cannot be computed on proportions
> **Answer:** Nobody randomised users to devices. Adjusting for a known confounder (channel) helps; only an experiment can show cause. That is why "run a targeted experiment" is one of the outcomes.

### Q5. Which of these is a good acceptance criterion for an analysis?
- [ ] "The analysis is high quality"
- [ ] "The charts look professional"
- [x] "`make report` runs top to bottom from a clean checkout and the three tracks' answers.json are identical"
- [ ] "The Head of Product agrees with the result"
> **Answer:** An acceptance criterion is something a reviewer can check without trusting you. Agreement is not a criterion; reproducibility and parity are.

### Q6. Which risk does comparing mobile and desktop *within each acquisition channel* address?
- [ ] A join that multiplies revenue
- [ ] A tracking break in one week
- [x] Confounding by traffic mix: if mobile gets more of a low-converting channel, the overall gap can be a mix effect
- [ ] An AI summary inventing numbers
> **Answer:** Stratifying by channel compares like with like. It is the core of Q4 (Cochran-Mantel-Haenszel) and the check for a Simpson's paradox.

## 7. What you learned
- A stakeholder's solution is a hypothesis; the analyst turns it into measurable questions.
- A decision rule written before the data protects the analysis from forking paths.
- Business thresholds come from the business case and live in the contract.
- What an observational, sampled export can and cannot establish.
- Acceptance criteria and risks a reviewer can check, filed as issues.

## 8. Catch-up git commands
```bash
git fetch upstream --tags
git switch -c my-phase-2 phase-1-end
# Compare your requirements with the reference:
git diff phase-1-end -- spec/requirements.md
git show phase-1-end:spec/requirements.md | less
```
