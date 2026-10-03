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
