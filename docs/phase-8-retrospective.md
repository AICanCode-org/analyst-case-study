---
phase: 8
slug: phase-8-retrospective
title: Retrospective and portfolio
duration: 1.5 h
start_tag: phase-7-end
end_tag: phase-8-end
---
# Phase 8 · Retrospective and portfolio

## 1. Why it matters
Hiring managers for analyst roles see hundreds of Titanic notebooks. What they rarely see is an
analysis that states a decision, survives messy data, quantifies uncertainty, reproduces in CI and
in Docker, and was re-run on new data with an incident handled properly. You have all of that, but
only if a reader can find it in a minute. This phase turns the repository into a portfolio piece:
a README case study, an honest retrospective, and a walkthrough you can give in an interview.

## 2. Objectives
By the end of this phase you can:
- Present the case study as problem → approach → result → evidence, with numbers and links.
- Write a retrospective that separates what worked, what did not, and what you would change.
- Explain your statistical choices (CMH, Welch, intervals) and their limits in plain language.
- Describe your use of AI precisely: where it helped, where you rejected its output, and how you verified.

## 3. Step-by-step instructions

### Step 8.1 · Collect your evidence
Make a list with links: the green CI run on `v1.1.0`, the parity job, the coverage numbers, the
report (`tracks/<yours>/out/…`, rendered as a CI artifact), the dashboard screenshot, the memo, the
post-mortem, the ADRs, and two or three `AI_LOG.md` entries where you corrected the AI.

### Step 8.2 · README case study
Insert a **Case study** section under the badges of `README.md` (see the `phase-8-end` README):
1. **The question**: mobile is 69% of sessions but 61% of revenue; rebuild the mobile checkout?
2. **The answer**: run a targeted experiment on the mobile payment step first.
3. **The evidence**: the payment-step gap within channels (CMH odds ratio 0.71, 95% CI 0.62-0.81),
   no difference in order value (Welch p 0.53), the aggregate cart gap explained by the channel mix
   (Simpson's paradox), an estimated ₹16 lakh/month below the ₹25 lakh rebuild threshold.
4. **How it is built**: three tracks with identical answers, a data contract, CI, Docker, a guarded AI narrator.
5. **What happened next**: the August refresh, the W31 tracking incident, v1.1.0.
6. **Limits**: observational data, one month, a sampled export; what the experiment must measure.

<!-- track:python -->
Link the executed notebook (`notebooks/analysis.ipynb`): GitHub renders it, including the charts.
<!-- /track -->
<!-- track:sql -->
Link `out/report.md` from a CI artifact or commit a copy under `docs/`: every view as a table is
easy to read on GitHub.
<!-- /track -->
<!-- track:r -->
Publish the knitted `analysis.html` (a CI artifact, or GitHub Pages) and link it: R Markdown output
is the most readable report of the three tracks.
<!-- /track -->

### Step 8.3 · Retrospective (`docs/retrospective.md`)
Use the template on `phase-8-end`: what went well, what went badly, what surprised you, what you would
do next, and the AI section (where it saved time, where it was wrong, how you caught it). Use evidence:
"the parity check caught a spec ambiguity in v1.1" beats "testing was useful".

### Step 8.4 · Practise the walkthrough
Five minutes, out loud: the question, the data problems (name two), the method and why (CMH rather
than a pooled z-test), the result with its interval, the decision rule, the incident, what you would
do next. Then answer the three questions in the quiz below without notes.

### Step 8.5 · Share it
Pin the repository on your GitHub profile, add the dashboard screenshot to the README, and post a
short write-up (what you found, one chart, one lesson) where your network is. Tag the final commit
`phase-8-end` if you follow the tags.

## 4. AI-assist prompts

### Prompt 1: Draft the case study from evidence
```text
Here are my project facts: <paste the answers.json summary, the CI run link, the parity output, the
post-mortem summary and three AI_LOG entries>. Draft a README "Case study" section of at most 250
words: question, answer, evidence (with the intervals), how it is built, what happened next, limits.
Use only the numbers I gave you, keep their precision, and make no causal claims.
```
**Verify the output by:** checking every number against `answers.json` or the post-mortem, deleting
any adjective you cannot back with evidence, and making sure the limits section survives the edit.

### Prompt 2: Mock analyst interview
```text
Act as a hiring manager for a product analyst role. Read my case study: <paste>. Ask me eight
questions, one at a time, mixing statistics (why CMH, what the interval means, multiple testing),
data quality (what you dropped and why), business (why the threshold), and judgement (what would
change your recommendation). After each answer, tell me what a strong answer would add.
```
**Verify the output by:** checking its "strong answer" notes against `contract/questions.md`, the ADRs
and a statistics reference before you adopt them: an interviewer persona can be confidently wrong too.

### Prompt 3: Retrospective review
```text
Here is my project retrospective: <paste docs/retrospective.md>. Point out vague items without
evidence, missing failures, and action items that are not specific. Do not add achievements.
```
**Verify the output by:** keeping only changes you can support with a link (commit, run, log entry).

## 5. Deliverables
- [ ] README case study with numbers, intervals and links.
- [ ] `docs/retrospective.md` with evidence and an honest AI section.
- [ ] A five-minute walkthrough you have practised once out loud.
- [ ] The repository pinned, a screenshot, and (optionally) a public write-up.

## 6. Self-check quiz

### Q1. Which README claim is strongest?
- [ ] "Advanced statistical analysis of e-commerce data"
- [ ] "Used AI to find insights"
- [x] "Within channels, mobile completes the payment step less often (CMH OR 0.71, 95% CI 0.62-0.81); the estimated uplift (₹16 lakh/month) is below the rebuild threshold, so I recommended an experiment"
- [ ] "Cleaned a large dataset"
> **Answer:** A specific, bounded, verifiable result tied to a decision. The others are unfalsifiable.

### Q2. An interviewer asks "So the mobile checkout causes lost revenue?" Best answer?
- [ ] "Yes, the p-value proves it"
- [x] "The data is observational: the gap holds within channels, which rules out the channel mix, but other differences between mobile and desktop users could explain it; that is why I recommended an experiment"
- [ ] "Probably, the effect is large"
- [ ] "Correlation is never useful"
> **Answer:** Show what the analysis does establish, what it cannot, and what would.

### Q3. Why did you use the Cochran-Mantel-Haenszel test instead of a pooled two-proportion z-test?
- [ ] It is more modern
- [ ] It needs less data
- [x] Device and channel are related; CMH compares mobile and desktop within each channel, so the channel mix cannot create or hide the gap
- [ ] The z-test cannot handle percentages
> **Answer:** The aggregate cart gap reversed within channels (Simpson's paradox), which is exactly the confounding CMH controls for.

### Q4. What belongs in "What I'd do next"?
- [ ] "Use deep learning"
- [x] "Design the experiment: payment-step variant on mobile UPI users, primary metric payment completion, sample size for a 5-point lift, guardrail on order value"
- [ ] "Make the dashboard prettier"
- [ ] Nothing: the project is finished
> **Answer:** A concrete next step that follows from the limits of the current analysis.

### Q5. How should you describe AI use in your portfolio?
- [ ] Hide it
- [ ] "AI did most of the analysis"
- [x] Specifically: what you used it for, examples where you rejected or corrected its output, and how every number was verified (tests, parity, golden files)
- [ ] Only mention it if asked
> **Answer:** Honest, specific AI use with verification is a strength; the AI_LOG is your evidence.

### Q6. Which retrospective item is most useful?
- [ ] "Testing was good"
- [ ] "Statistics are hard"
- [x] "Parity between three implementations exposed an ambiguity in how unknown channels were counted after a week exclusion; next time I would write a worked example for every counting rule"
- [ ] "I should have started earlier"
> **Answer:** Evidence, a cause and a specific change of practice.

## 7. What you learned
- Presenting an analysis as a portfolio case study: question, answer, evidence, limits.
- Retrospectives with evidence and specific changes.
- Explaining statistical choices and their limits to non-specialists and interviewers.
- Describing AI assistance honestly, with your verification process.

## 8. Catch-up git commands
```bash
git fetch upstream --tags
git switch -c my-final phase-8-end
git diff phase-7-end phase-8-end --stat
```
