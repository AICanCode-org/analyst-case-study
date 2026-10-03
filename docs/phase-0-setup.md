---
phase: 0
slug: phase-0-setup
title: Setup and the brief
duration: 1.5 h
start_ref: main
end_tag: phase-0-end
---
# Phase 0 · Setup and the brief

## 1. Why it matters
An analysis nobody else can re-run is an opinion with charts. Professional analysts start where
engineers start: a repository that installs with one command, data whose origin you can prove, tests
that say what "right" means, and a log of how AI helped. In this phase you set up the tools for
**one** track, read the brief and the data, run the starter, meet the pending tests and the contract
that will guide you, open your first pull request and start your `AI_LOG.md`. You will not compute a
single number yet, on purpose: first you learn what question is being asked and what the data can say.

## 2. Objectives
By the end of this phase you can:
- Fork the repository **with all branches and tags**, clone it and add the `upstream` remote.
- Pick a track (Python, SQL or R), install its toolchain on Windows (WSL2), macOS or Linux, and run `make lint test`.
- Explain the brief in two sentences: who decides what, and why "rebuild the mobile checkout" is a solution, not a question.
- Prove the export in `data/raw/2026-06` is exactly the published one (`generate_data.py --check`) and list three defects you can see in the raw CSVs.
- Open a pull request that passes CI and write your first `AI_LOG.md` entry.

## 3. Step-by-step instructions

### Step 0.1 · Fork and clone (keep the tags!)
1. On GitHub open `AICanCode-org/analyst-case-study` → **Fork**. **Untick "Copy the `main` branch
   only"**. The `solution` branch and the `phase-N-end` tags are your safety net in later phases.
2. Clone **your** fork and connect the original as `upstream`:
   ```bash
   git clone https://github.com/<you>/analyst-case-study.git
   cd analyst-case-study
   git remote add upstream https://github.com/AICanCode-org/analyst-case-study.git
   git fetch upstream --tags
   git tag -l 'phase-*'      # phase-0-end … phase-8-end
   ```
3. **Windows:** do all of this inside **WSL2** (Ubuntu) and keep the repo in the Linux file system
   (`~/code/analyst-case-study`), not under `/mnt/c`.

### Step 0.2 · Install the tools for ONE track
Every track needs Git, `make` and Python 3.11+ (the data generator, the parity script and the
dashboard are Python). Run the doctor script; it tells you exactly what is missing:
```bash
scripts/doctor.sh
```

<!-- track:python -->
**Python track:** pandas, Jupyter, SciPy and statsmodels, installed into a virtual environment.
```bash
cd tracks/python && make install     # creates .venv with the pinned versions
.venv/bin/python -c "import pandas, scipy, statsmodels; print(pandas.__version__)"
```
Open the notebook with `.venv/bin/jupyter lab notebooks/analysis.ipynb` (or VS Code with the
Jupyter extension, selecting `.venv` as the kernel).
<!-- /track -->

<!-- track:sql -->
**SQL track:** DuckDB, an in-process analytical database: no server, it reads the CSVs directly.
The analysis is written in `sql/*.sql`; a thin Python runner sets variables and writes `answers.json`.
```bash
cd tracks/sql && make install        # .venv with duckdb, sqlfluff, pytest
.venv/bin/python -c "import duckdb; print(duckdb.sql(\"SELECT count(*) FROM '../../data/raw/2026-06/orders.csv'\"))"
```
Optional: the DuckDB CLI (`brew install duckdb`, or the binary from duckdb.org) to explore by hand.
<!-- /track -->

<!-- track:r -->
**R track:** R 4.3+ with the tidyverse core, testthat, lintr and R Markdown (pandoc renders it).
```bash
sudo apt install r-base pandoc        # Ubuntu/WSL; macOS/Windows: R from CRAN + RStudio (includes pandoc)
cd tracks/r && make install            # installs the packages listed in DESCRIPTION (pak)
Rscript -e 'packageVersion("dplyr")'
```
RStudio users: open `tracks/r` as a project; the package is loaded with `devtools::load_all()` or
`pkgload::load_all()`.
<!-- /track -->

### Step 0.3 · Read the brief and the data
1. Read the top of `README.md` (the situation) and `contract/questions.md` §1 (the decision and the
   eight questions). Write down, in your own words: **who decides, what, and what a wrong decision costs.**
2. Read `data/README.md`, then look at the raw files themselves. They are small on purpose:
   ```bash
   head -5 data/raw/2026-06/sessions.csv
   grep -c '/' data/raw/2026-06/sessions.csv          # rows with the day-first date format
   cut -d, -f4 data/raw/2026-06/users.csv | sort | uniq -c | sort -rn | head -12   # city spellings
   python3 scripts/generate_data.py --check            # byte-identical to the seeded generator
   ```
3. Note three defects you can see without any code (duplicate rows? two date formats? amounts as
   text?). Phase 2 turns each of them into a rule.

### Step 0.4 · Run the checks and meet the pending tests and the contract
```bash
make lint test
```
All the tests are **skipped**. They are *pending*: the complete test suite is already written and
switched off in one list per track:

| Track | Pending list |
|---|---|
| Python | `tracks/python/tests/conftest.py` (`PENDING`) |
| SQL | `tracks/sql/tests/conftest.py` (`PENDING`) |
| R | `tracks/r/tests/testthat/helper-funnellens.R` (`PENDING`) |

Each entry names a milestone ("Phase 3 M1 - cleaning rules and the issue counts"). In Phase 3 you
delete one entry at a time, watch the tests go red, and make them green.

Now open the four files of `contract/` that make "right" precise:
- `questions.md`: every cleaning rule, in order, and every formula;
- `data-contract.yaml`: the columns each CSV must have and the checks (an `error` stops the run);
- `answers.schema.json`: the shape of `answers.json`, the one output every track writes;
- `fixtures/tiny/` + `tiny-expected.json`: a 14-session export small enough to check by hand, and
  `golden/answers-2026-06.json`: the reference answers for the real export.

### Step 0.5 · Your first pull request
1. Create a branch: `git switch -c chore/phase-0-setup`.
2. Fill in the first entry in `AI_LOG.md`, e.g. how an assistant explained a `duckdb` / `pandas` /
   `readr` error during the install and how you checked its advice.
3. Commit and push, then open a PR **in your fork** against your `main`:
   ```bash
   git add AI_LOG.md
   git commit -m "docs: start AI_LOG for phase 0"
   git push -u origin chore/phase-0-setup
   ```
4. Open the **Actions** tab. Forks have Actions switched off until you click **"I understand my
   workflows, go ahead and enable them"**. CI runs lint + unit tests for all three tracks. Wait for
   green, fill in the PR template and merge.

## 4. AI-assist prompts

### Prompt 1: Fix my toolchain install
```text
I'm on <Windows 11 + WSL2 Ubuntu 24.04 | macOS 15 | Ubuntu 24.04>. I want to run a <Python 3.12 with
pandas and Jupyter | DuckDB 1.x from Python | R 4.5 with the tidyverse, testthat and R Markdown>
project. Here is the output of scripts/doctor.sh: <paste output>. Give me the exact commands to
install what is missing, explain each one in one line, and tell me how to verify each install.
```
**Verify the output by:** running each verification command, re-running `scripts/doctor.sh` until
every line for your track is green, and checking any download URL against the official site
(python.org, duckdb.org, cloud.r-project.org, pandoc.org). Never pipe an unknown URL into `bash`.

### Prompt 2: Restate the brief as a decision
```text
Here is a stakeholder brief: <paste the "situation" paragraph of README.md and contract/questions.md §1>.
Restate it as: (1) the decision to be made, by whom, (2) the cost of each wrong decision, (3) the
question the data must answer, (4) three alternative explanations for "69 % of sessions but 61 % of
revenue" that would NOT call for a checkout rebuild. Do not compute anything and do not guess numbers.
```
**Verify the output by:** checking every claim against the brief (assistants add details that are
not there, such as a conversion rate or a budget), and keeping at least one alternative explanation
that involves *who* uses mobile (traffic mix) rather than *how* the checkout works. You will test them in Phase 3.

### Prompt 3: Read a raw file like an analyst
```text
Here are the header and 15 sample rows of a raw CSV export: <paste head -16 data/raw/2026-06/orders.csv>.
List every data-quality problem you can see or suspect, how you would detect each one in code, and
what you would ask the data owner. Do not clean anything yet.
```
**Verify the output by:** finding each problem in the real file with `grep` or a quick count (an
assistant may "see" problems that are not in your sample), and comparing your list with
`contract/questions.md` §2. These rows are synthetic; with real customer data you would paste
column names and aggregates only, never rows.

## 5. Deliverables
- [ ] Your fork contains the `solution` branch and the `phase-*` tags (`git tag -l` shows them).
- [ ] `make lint test` passes locally in your track (all tests skipped).
- [ ] `python3 scripts/generate_data.py --check` says the export is identical.
- [ ] A note (in your PR description or `AI_LOG.md`): the decision, the question, three raw-data defects.
- [ ] A merged PR with a green CI run.
- [ ] `AI_LOG.md` has its first entry.

## 6. Self-check quiz

### Q1. Why must you untick "Copy the main branch only" when forking?
- [ ] Otherwise GitHub Actions is disabled in the fork
- [x] Otherwise the `solution` branch and phase tags are missing from your fork
- [ ] Otherwise you cannot open pull requests
- [ ] Otherwise the CSV files are not copied
> **Answer:** Forks copy only `main` by default. The tags (`phase-N-end`) live on the `solution` branch; without them you cannot compare your work or catch up. Fix it later with `git fetch upstream --tags`.

### Q2. The Head of Product says "rebuild the mobile checkout". What is your job?
- [ ] Prove the Head of Product right, since they own the decision
- [ ] Prove them wrong, to show independence
- [x] Find out what the data supports and say it clearly enough that the decision can be made, including what you could not establish
- [ ] Build the rebuild's business case
> **Answer:** A stakeholder's proposed solution is a hypothesis. The analysis is judged on whether the conclusion follows from the evidence and states its limits, not on agreement.

### Q3. Why are the raw CSV files read as text, and never "fixed" by hand?
- [ ] Text is faster to read
- [ ] The CSV format cannot store numbers
- [x] Type guessing hides defects (a `₹1,299` becomes missing silently), and a hand edit cannot be reproduced or counted; the cleaning rules do it in code and count every row
- [ ] GitHub cannot store edited CSV files
> **Answer:** Defensive loading means you decide every type yourself, so every rejected value is visible and counted in `data_quality.issues`. `generate_data.py --check` proves nobody touched the raw files.

### Q4. Why are all tests skipped in the starter?
- [ ] They are flaky
- [ ] CI is too slow to run them
- [x] They describe behaviour you build in Phases 3-4 and are switched on one milestone at a time
- [ ] They only run on the solution branch
> **Answer:** The full suite is written up-front (test-first). Deleting a line from the pending list turns a group back on, so you always have a clear red → green target.

### Q5. What is `contract/fixtures/tiny/` for?
- [ ] A smaller export to save disk space
- [x] A 14-session export small enough to check by hand, with every expected count and rate written down, so unit tests can pin each rule exactly
- [ ] Training data for the AI narrator
- [ ] The data of a different shop
> **Answer:** Real exports are too big to check by eye. The tiny fixture contains one example of each defect; `tiny-expected.json` says what every rule must produce on it, so a wrong rule fails a test in milliseconds.

### Q6. Which of these may you paste into an AI prompt for this project?
- [ ] Your `.env` file with an LLM API key
- [ ] 500 rows of a real customer orders export
- [x] Column names, your own code, an error message and aggregate numbers
- [ ] Another student's notebook
> **Answer:** Secrets and row-level personal data never go into prompts. The FunnelLens data is synthetic, but practise the habit you will need at work: aggregates and code, not rows.

## 7. What you learned
- A reproducible local environment for one track, checked by `scripts/doctor.sh`.
- The difference between `origin` (your fork) and `upstream` (the course repo), and why tags matter.
- The brief as a decision: who decides, what a wrong call costs, and which question the data must answer.
- The contract (`questions.md`, `data-contract.yaml`, the schema, fixtures and golden answers) that defines "right".
- The PR + CI loop and the habit of logging AI assistance without leaking secrets or rows.

## 8. Catch-up git commands
```bash
git fetch upstream --tags
# Start Phase 1 from the reference end of Phase 0:
git switch -c my-phase-1 phase-0-end
# See what the reference changed in this phase:
git diff main phase-0-end --stat
```
