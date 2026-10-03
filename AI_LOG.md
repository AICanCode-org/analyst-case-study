# AI_LOG: how I used AI on this project

Employers and reviewers increasingly ask *how* you used AI, not *whether*. This log is your evidence
that you stayed in control. Add one entry every time an AI assistant (ChatGPT, Gemini, Copilot,
Cursor, Claude, a local Ollama model, ...) produced something you kept, changed or rejected.

**Rules**
1. Never paste secrets, `.env` contents, LLM API keys or **row-level data** (user ids, session ids,
   cities, order amounts of real people) into a prompt. Column names, aggregates, your own code and
   the synthetic tiny fixture are fine.
2. Every AI output is a *draft*. Record how you **verified** it: a test, the golden answers,
   `contract/fixtures/stats-cases.json`, `scripts/parity.py` against another track, the docs of the
   library, a second source.
3. Be honest about rejections: they are the most valuable entries. Statistics get the strictest
   review: a formula, a test choice or a causal sentence is only right if you can reproduce it, and an
   assistant that "simplifies" a cleaning rule has just changed every number downstream.

## Entry template (copy for each entry)

### YYYY-MM-DD · Phase N · <short title>
* **Tool / model:** e.g. Gemini 2.0 Flash (free tier), Copilot in VS Code, Ollama llama3.2
* **Prompt (summary or paste):**
  > ...
* **What it produced:** one or two lines, or a link to the commit
* **What I kept / changed / rejected, and why:**
* **How I verified it:** e.g. `make coverage` (93 passed), parity with the golden file IDENTICAL, statsmodels docs
* **Time saved / lost (honest guess):**
* **What I learned:**

---

## My entries

<!-- Start below this line. Phase 0 asks you to write your first entry. -->

### 2026-07-01 · Phase 0 · Installing the R track on WSL
* **Tool / model:** Gemini 2.0 Flash (free tier)
* **Prompt (summary or paste):**
  > Prompt 1 of Phase 0 with the output of `scripts/doctor.sh` (R found, packages and pandoc missing).
* **What it produced:** `sudo apt install r-base pandoc`, then `install.packages("tidyverse")`.
* **What I kept / changed / rejected, and why:** kept the apt line; rejected installing the whole
  tidyverse (60+ packages) and used `make install` instead, which installs only what `DESCRIPTION` lists.
* **How I verified it:** `scripts/doctor.sh` all green for the R track; `make lint test` (all skipped).
* **Time saved / lost (honest guess):** saved ~20 minutes.
* **What I learned:** the project's own install target is the source of truth, not a generic answer.

### 2026-07-02 · Phase 1 · Attacking the decision rule
* **Tool / model:** Claude (chat)
* **Prompt (summary or paste):**
  > Prompt 3 of Phase 1 with my draft decision rule.
* **What it produced:** six objections: multiple comparisons, a one-sided test, no minimum effect,
  sampling, observational data, "use Bayesian methods instead".
* **What I kept / changed / rejected, and why:** kept "no minimum effect" (added the ₹25 lakh
  threshold from the rebuild cost) and "observational" (added the experiment outcome); kept one
  primary test to answer multiple comparisons. Rejected the one-sided test (we would also want to know
  if mobile were better) and the Bayesian rewrite (not wrong, but not what the team can review).
* **How I verified it:** every remaining objection maps to a line in requirements §4 or §7.
* **Time saved / lost (honest guess):** saved ~30 minutes of review later.
* **What I learned:** a threshold in rupees is what turns "significant" into a decision.

### 2026-07-03 · Phase 2 · Checking a CMH example
* **Tool / model:** ChatGPT (free tier)
* **Prompt (summary or paste):**
  > Prompt 2 of Phase 2 (CMH and Simpson's paradox with made-up 2x2 tables).
* **What it produced:** a clear explanation and two strata whose Mantel-Haenszel odds ratio it gave as 0.62.
* **What I kept / changed / rejected, and why:** kept the explanation; the number was wrong: by hand
  Σ(ad/n) / Σ(bc/n) = 0.71 for its own tables.
* **How I verified it:** recomputed by hand and with `statsmodels.stats.contingency_tables.StratifiedTable`.
* **Time saved / lost (honest guess):** saved ~20 minutes of reading; the wrong number would have cost more.
* **What I learned:** never trust arithmetic in an explanation; recompute every example.

### 2026-07-06 · Phase 3 · A "simpler" timestamp parser
* **Tool / model:** Copilot in VS Code
* **Prompt (summary or paste):**
  > Prompt 1 of Phase 3: implement the session timestamp rule of questions.md §2 (two formats, day first).
* **What it produced:** `pd.to_datetime(df["started_at"], errors="coerce")` in one line.
* **What I kept / changed / rejected, and why:** rejected. Format inference read `12/06/2026 10:15`
  month first (6 December, then dropped as out of period instead of counted as 12 June), and it accepted
  texts the spec calls bad. Wrote one explicit `format=` per pattern and combined them instead.
* **How I verified it:** the tiny fixture's expected counts (`sessions_bad_timestamp` 1) and the data
  test on 2026-06 (80 bad timestamps), both red with the one-liner.
* **Time saved / lost (honest guess):** lost ~15 minutes, gained a test I would not have written.
* **What I learned:** a cleaning shortcut is a spec change; the fixture is what catches it.
### 2026-07-08 · Phase 3 · The CMH variance formula
* **Tool / model:** ChatGPT (free tier)
* **Prompt (summary or paste):**
  > Prompt 2 of Phase 3: the Robins-Breslow-Greenland confidence interval for the Mantel-Haenszel odds ratio.
* **What it produced:** the formula and a function; the variance term mixed up P·S and Q·R.
* **What I kept / changed / rejected, and why:** kept the structure; fixed the term from the 1986
  paper's notation.
* **How I verified it:** `contract/fixtures/stats-cases.json` (CI 0.616-0.810 to 1e-9) and
  `statsmodels.stats.contingency_tables.StratifiedTable(...).oddsratio_pooled_confint()`.
* **Time saved / lost (honest guess):** saved ~30 minutes.
* **What I learned:** the stats fixture is the only acceptable judge of a formula.

### 2026-07-14 · Phase 4 · Invariants instead of more examples
* **Tool / model:** Claude (chat)
* **Prompt (summary or paste):**
  > Prompt 2 of Phase 4: properties that must hold for any valid answers.json (column names and rules only).
* **What it produced:** twelve invariants; three were wrong ("revenue share equals session share for
  desktop", "every channel has a payment step gap", "p < 0.05 implies a large odds ratio").
* **What I kept / changed / rejected, and why:** kept nine (funnel monotonic, shares sum to 1, the CI
  contains the OR, clean ≤ raw, ...); rejected the three because they are claims about this data,
  not truths about any data.
* **How I verified it:** each kept invariant passes on 2026-06 and fails on a hand-broken copy of the answers.
* **Time saved / lost (honest guess):** saved ~40 minutes.
* **What I learned:** an invariant must hold for every valid input; findings are not invariants.
### 2026-07-15 · Phase 4 · Parity found a spec ambiguity, not a bug
* **Tool / model:** none at first; then Gemini to compare two readings of the spec.
* **Prompt (summary or paste):**
  > Here are steps 7 and 9 of the cleaning spec and two counts of unknown-channel sessions (3,361 vs 3,478). Which reading does the text support?
* **What it produced:** "both are defensible; the text does not order the count and the exclusion."
* **What I kept / changed / rejected, and why:** kept the diagnosis; did not let either track "win".
  Proposed one sentence for `questions.md` (count after the exclusion) and changed the track that differed.
* **How I verified it:** parity IDENTICAL for the three tracks and the golden file after the change.
* **Time saved / lost (honest guess):** neutral; the value was finding it before a stakeholder did.
* **What I learned:** two independent implementations are the best review a spec can get.

### 2026-07-17 · Phase 5 · Caching the R packages
* **Tool / model:** Copilot Chat
* **Prompt (summary or paste):**
  > Make the R job faster: it installs the tidyverse from source on every run.
* **What it produced:** an `actions/cache` step on `~/R/library` keyed by the date.
* **What I kept / changed / rejected, and why:** rejected; a date key never invalidates on a
  `DESCRIPTION` change. Used `r-lib/actions/setup-r-dependencies@v2` (keyed by the dependencies) with
  binary packages from Posit Public Package Manager (`use-public-rspm: true`).
* **How I verified it:** the second run's R job took 2 minutes instead of 14; changing `DESCRIPTION`
  produced a cache miss as expected.
* **Time saved / lost (honest guess):** saved ~10 minutes per CI run.
* **What I learned:** a cache key must change exactly when its content should.

### 2026-07-21 · Phase 6 · Breaking the narrator's guardrails
* **Tool / model:** Ollama llama3.2 (local) and ChatGPT (free tier)
* **Prompt (summary or paste):**
  > Prompt 1 of Phase 6: five summaries that each violate one rule, and one misleading but valid one.
* **What it produced:** the five violations, and a valid summary that led with the ₹16.3 lakh figure
  and buried the caveat in the last clause.
* **What I kept / changed / rejected, and why:** all five were rejected by `validate()` for the right
  reason; one ("about 70 %" for 69.2 %) was rejected as an invented number, which is the intended
  strictness. The misleading-but-valid one passes: recorded as a known limitation and added "a human
  reads the memo before it is sent" to the runbook.
* **How I verified it:** a test per case in `tests/test_narrator.py` with the fake LLM server.
* **Time saved / lost (honest guess):** saved ~1 hour of inventing adversarial cases.
* **What I learned:** guardrails check facts and words, not emphasis; review stays human.
