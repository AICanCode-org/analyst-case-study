# FunnelLens: a data analyst case study on a messy e-commerce funnel, with AI as your pair analyst

[![CI](https://github.com/AICanCode-org/analyst-case-study/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AICanCode-org/analyst-case-study/actions/workflows/ci.yml)
[![CI (solution)](https://github.com/AICanCode-org/analyst-case-study/actions/workflows/ci.yml/badge.svg?branch=solution)](https://github.com/AICanCode-org/analyst-case-study/actions/workflows/ci.yml?query=branch%3Asolution)

## Case study (reference solution)

> **Mobile is 69 % of FunnelLens's sessions but 61 % of its revenue. The data does not support a
> mobile checkout rebuild; it supports a targeted experiment on the mobile payment step. The analysis
> is built three times, in Python, SQL and R, against one written spec, and every track produces the
> same `answers.json` to 1e-9.**

```console
$ docker compose --profile pipelines run --rm --no-deps parity
IDENTICAL  /out/sql/answers.json (sql)
IDENTICAL  /out/r/answers.json (r)
$ jq '.decision.recommendation, .by_channel.cmh.purchase_given_checkout.odds_ratio_mh' tracks/r/out/answers.json
"run_targeted_experiment"
0.7254582744768108
```

**Problem → answer.** The Head of Product wanted to rebuild the mobile checkout (a quarter of
engineering time). After cleaning a deliberately messy export (17 counted issue types: duplicate and
conflicting ids, two date formats, rupee amounts as text, orphan rows, out-of-order funnel events),
the analysis finds:

- The aggregate mobile cart gap (−4.5 points) is **channel mix** (Simpson's paradox): within channels,
  mobile carts at least as well as desktop (cart-step CMH odds ratio 1.08).
- The real gap is the **payment step**: 54.4 % of mobile checkouts end in a purchase against 65.6 %
  on desktop; adjusted for channel, CMH odds ratio **0.71 (95 % CI 0.62-0.81), p = 6.4e-7** (2026-06; 0.73 on the
  2026-08 refresh).
- Mobile and desktop orders are worth the same (₹2,001 vs ₹1,967, Welch p = 0.53), so the gap is in
  conversion, not basket size.
- Closing the payment gap is worth about **₹16 lakh/month**, below the ₹25 lakh/month that justifies a
  rebuild. Recommendation: **run a targeted experiment on the mobile payment step** (UPI first: 1,252 of
  2,072 mobile orders in 2026-08).

**Decisions I'd defend in an interview** ([analysis plan](spec/analysis-plan.md)):
[read raw files as text](spec/adr/0001-read-raw-files-as-text.md) ·
[CMH-adjusted primary test](spec/adr/0002-cmh-adjusted-primary-test.md) ·
[one answers contract, three tracks](spec/adr/0003-one-answers-contract-three-tracks.md) ·
[contract checks with severities](spec/adr/0004-contract-checks-with-severities.md) ·
[AI narrator: facts in, guardrails out](spec/adr/0005-ai-narrator-facts-and-guardrails.md) ·
[versioned contract and monitoring](spec/adr/0006-versioned-contract-and-monitoring.md).

**Evidence**

| | Python (pandas, Jupyter) | SQL (DuckDB) | R (tidyverse, R Markdown) | Dashboard |
|---|---|---|---|---|
| Tests v1.1.0 (unit + data + golden + invariants) | 93 | 97 | 66 `test_that` blocks | 49 |
| Line coverage (gate 85 %) | 99 % | 96 % | 99.5 % | 97 % |
| Parity with the golden answers (2026-06, 2026-08, `--backcompat`) | IDENTICAL | IDENTICAL | IDENTICAL | |

The Docker smoke test passes against the dashboard image of v1.0.0 and v1.1.0, also with the AI
provider unreachable (the narrator falls back to its template and says so). Images: dashboard ~560 MB,
python ~480 MB, R ~300 MB, SQL ~260 MB, all non-root with a read-only file system.

- **Data contract:** declarative checks with severities; an `error` stops the run (exit 3) instead of
  producing numbers on changed data. On the August refresh it stopped v1.0 on a new channel
  (`referral`) and led to contract 1.1.0, with 1.0.0 kept for reproducibility.
- **Monitoring and an incident:** weekly monitoring found 2026-W31, where app release 8.14 lost about
  70 % of mobile checkout events (mobile checkout-given-cart 10.7 % against a 53.4 % median). The week is
  excluded with a [post-mortem](docs/postmortem-2026-W31.md); the effect on the decision is measured
  (₹14.1 vs ₹14.3 lakh/month) and nil.
- **AI narrator:** an optional OpenAI-compatible model writes the executive summary from numbered
  aggregate facts; guardrails reject invented numbers, unknown citations, causal claims and a missing
  caveat, with a deterministic fallback. It never sees row-level data and needs no paid key.

**How I used AI.** Assistants drafted code, tests and docs; every entry is in
[`AI_LOG.md`](AI_LOG.md). Rejected: a one-line timestamp parser that read day-first dates month
first, an "unexpected channel → unknown" fix that would have hidden the referral programme, a CMH
interval with a wrong variance term (caught by the stats fixture), and an ML anomaly detector where a
median rule was enough. The three-track parity check caught an ambiguity in the spec itself (when to
count unknown channels relative to the week exclusion), fixed by one sentence in `questions.md`.

**Limits and next steps.** The data is observational and sampled (1 in 20): the payment gap holds
within channels but other differences between mobile and desktop users could explain part of it.
Next: design and size the experiment (mobile UPI users, primary metric payment completion, guardrail
on order value), run the pipeline weekly on a schedule (post-mortem action 1), and revisit the median
monitoring rule once the history covers a season.

FunnelLens is a guided project from **[AiCanCode](https://www.aicancode.org)**, the capstone of the
Data Analyst track. Over 9 phases (about 32 hours) you carry **one messy dataset the whole way**, the
way a professional analytics team does: requirements, a data contract and an analysis plan, a
test-first implementation, data tests, CI, a containerised dashboard, monitoring after a data refresh,
and a retrospective. AI assistants help at every step, and you **verify** every number they produce.

**The situation.** You are the first analyst at FunnelLens, a mid-sized Indian e-commerce company.
Mobile is about **69 % of sessions but only about 61 % of revenue**. The Head of Product is sure the
mobile checkout is at fault and wants to rebuild it: a quarter of engineering time. Your job is not to
agree or disagree. It is to find out what the data supports, and to say so clearly enough that a
decision can be made.

**The data.** A six-month export (a 1-in-20 sample of sessions) in four deliberately imperfect CSVs,
with the problems real exports have: duplicate and conflicting session ids, two date formats, amounts
as text with rupee signs and thousands separators, inconsistent city spellings, missing signup
channels, out-of-order funnel events and orders without a checkout.

| Table | Raw rows | Known problems |
|---|---|---|
| `sessions.csv` | 27,515 | exact duplicates, conflicting ids, mixed date formats, out-of-period rows, unknown channels |
| `events.csv` | 40,031 | unknown event names, orphan events, repeated and out-of-order steps |
| `orders.csv` | 2,522 | amounts like `₹1,299.00` / `Rs. 1,299` / `-₹499`, duplicates, orphan orders |
| `users.csv` | 5,986 | ~9 % missing signup channel, `Bangalore` / `bengaluru ` / `BENGALURU` |

**What you deliver:** an analysis that runs top to bottom from a clean checkout (a notebook, SQL
report or R Markdown report), an `answers.json` that matches the shared contract, a one-page decision
memo, and a dashboard. It is judged not on whether you agree with the Head of Product, but on whether
the conclusion follows from the evidence and whether you were honest about what you could not establish.

**Pick one track.** The data, the contract, the golden answers and the dashboard are shared; only the
analysis code differs, and the three tracks must produce **the same numbers to 1e-9**.

| Track | Stack | Folder |
|---|---|---|
| Python | Python 3.11+ · pandas · Jupyter · SciPy · statsmodels · pytest · ruff | `tracks/python` |
| SQL | DuckDB SQL (views you can query step by step) · sqlfluff · a thin Python runner · pytest | `tracks/sql` |
| R | R 4.3+ · tidyverse (dplyr, tidyr, readr, stringr) · base `stats` · R Markdown · testthat · covr · lintr | `tracks/r` |

The dashboard (`dashboard/`) is a small Streamlit app that reads any track's `answers.json`. Its
optional **AI narrator** sees only numbered aggregate facts and is checked by guardrails; offline, it
falls back to a deterministic template. Everything runs **on your laptop, with no API key and no paid
service**.

Course repository: **<https://github.com/AICanCode-org/analyst-case-study>** (`main` = starter,
`solution` = reference).

---

## Repository layout
```text
.
├── README.md                 ← you are here
├── AI_LOG.md                 ← your log of AI prompts, outputs and how you verified them
├── docs/                     ← the course: phase-0 … phase-8 + GitHub Actions explained
├── spec/                     ← requirements, analysis plan, ADRs (you write them in Phases 1-2)
├── contract/                 ← the shared contract: questions.md (every rule and formula), data-contract.yaml,
│                               answers.schema.json, the tiny fixture, stats cases and the golden answers
├── data/raw/2026-06/         ← the export (CSV + export.json), generated by scripts/generate_data.py
├── tracks/{python,sql,r}/    ← analysis code + tests (same Makefile targets in each)
├── dashboard/                ← the shared Streamlit dashboard + AI narrator
├── scripts/                  ← doctor.sh, check-all.sh, verify-tags.sh, build-cms.py, parity.py,
│                               generate_data.py (+ smoke-test.sh from Phase 6)
├── cms/                      ← machine-readable export of the course for the AiCanCode site
└── .github/                  ← CI workflows, issue/PR templates
```

## Prerequisites (per operating system)
You need **Git, `make` and Python 3.11+** (the scripts, the SQL runner and the dashboard use it) plus
the toolchain of **one** track. Docker is needed from Phase 6. Run `scripts/doctor.sh` at any time.

| | Windows 10/11 | macOS | Linux (Ubuntu/Debian) |
|---|---|---|---|
| Shell | **WSL2** with Ubuntu: `wsl --install` in an admin PowerShell, reboot | Terminal (zsh) | any |
| Git, make | inside WSL: `sudo apt install git make` | `xcode-select --install` | `sudo apt install git make` |
| Python (all tracks) | inside WSL: `sudo apt install python3 python3-venv` | `brew install python@3.12` | `sudo apt install python3 python3-venv` |
| R track | inside WSL: `sudo apt install r-base pandoc` (or R + RStudio on Windows) | R from CRAN + RStudio (pandoc included) | `sudo apt install r-base pandoc` |
| Docker (Phase 6+) | Docker Desktop with the WSL 2 engine | Docker Desktop (or Colima) | Docker Engine + compose plugin |

**Windows, important:** clone and work **inside the WSL file system** (`~/code/analyst-case-study`),
not under `/mnt/c/...`. Hardware: 8 GB RAM is plenty; the export is small on purpose.

## Quick start (5 minutes)
```bash
git clone https://github.com/<you>/analyst-case-study.git && cd analyst-case-study   # your fork (Phase 0)
scripts/doctor.sh                        # check your tools
cd tracks/python                         # or tracks/sql, tracks/r
make install                             # dependencies (Python/SQL: creates .venv)
make lint test                           # all tests are "pending" (skipped) until Phase 3
python3 ../../scripts/generate_data.py --check   # the export in data/raw is exactly the published one
```

Every track offers the same commands:

| Command | What it does |
|---|---|
| `make install` | install dependencies |
| `make lint` | linter + formatter check (ruff / ruff + sqlfluff / lintr) |
| `make test` | unit tests on the tiny hand-made fixture (seconds) |
| `make coverage` | unit + data tests on the real export, with an 85 % line-coverage gate |
| `make run` | write `out/answers.json` for one export (`DATA=../../data/raw/2026-06`) |
| `make report` | execute the notebook / SQL report / R Markdown report top to bottom |

Compare two tracks (or yours with the golden file): `python3 scripts/parity.py contract/golden/answers-2026-06.json tracks/python/out/answers.json`.

## How the phases work
| Phase | Topic | You end at tag |
|---|---|---|
| 0 | [Setup and the brief](docs/phase-0-setup.md) | `phase-0-end` |
| 1 | [Requirements: questions, decisions and acceptance criteria](docs/phase-1-requirements.md) | `phase-1-end` |
| 2 | [Design: data contract, analysis plan and ADRs](docs/phase-2-design.md) | `phase-2-end` |
| 3 | [Implementation in five milestones: load, clean, explore, test, decide](docs/phase-3-implementation.md) | `phase-3-end` |
| 4 | [Testing the analysis: golden answers, invariants, parity, coverage](docs/phase-4-testing.md) | `phase-4-end` |
| 5 | [CI with GitHub Actions](docs/phase-5-ci.md) | `phase-5-end` |
| 6 | [Dashboard, AI narrator, Docker and delivery](docs/phase-6-deploy.md) | `phase-6-end` = **`v1.0.0`** |
| 7 | [Data refresh, monitoring and a post-mortem](docs/phase-7-observability.md) | `phase-7-end` = **`v1.1.0`** |
| 8 | [Retrospective and portfolio](docs/phase-8-retrospective.md) | `phase-8-end` |

Each phase page has the same 8 blocks: *Why it matters · Objectives · Step-by-step instructions ·
AI-assist prompts · Deliverables · Self-check quiz · What you learned · Catch-up git commands*.

### Branches and tags
- **`main`**: the **starter**. Every track has its structure, the full (pending) test suite and a
  `TODO` with a hint in every function or SQL view; the notebook and the R Markdown report are
  skeletons with the questions and no answers.
- **`solution`**: the reference, one or more commits per phase, an annotated tag at the end of every
  phase (`phase-0-end` … `phase-8-end`) and the releases `v1.0.0` and `v1.1.0`. Every tag passes the
  checks of all three tracks.

**Stuck or behind?** Start the next phase from the reference end of the previous one:
```bash
git fetch upstream --tags
git switch -c my-phase-4 phase-3-end
```
**Compare with the reference:** `git diff phase-3-end -- tracks/python`. Try first, then compare.

### Pending tests
The complete test suite is already on `main` but switched off in one list per track
(`tests/conftest.py` for Python and SQL, `tests/testthat/helper-funnellens.R` for R). In Phase 3 you
remove one entry at a time, watch the tests fail, and make them pass. Skipped is never reported as passed.

## Working with AI
Use any assistant you like. Each phase has copy-paste prompts and a **"Verify the output by"**
checklist; log what you asked and how you checked it in [`AI_LOG.md`](AI_LOG.md). Two rules matter
most in analysis work: never paste row-level customer data or secrets into a prompt (aggregates and
your own code are fine), and never accept a number, a formula or a statistical claim from an assistant
without reproducing it: the golden answers, the stats cases and the other tracks are there to check it.

## Coming from the old five-step guide?
The earlier version (Brief · Load and Clean · Explore · Test a Hypothesis · Present) had the right
story but no data, no tests and no way to know if your numbers were right. This version ships the
data, a contract with every rule written down, golden answers, three tracks that check each other,
CI, a dashboard and a data refresh. The mapping of the old steps is in [`docs/README.md`](docs/README.md).

## More
- [docs/README.md](docs/README.md): index of all docs
- [docs/github-actions-explained.md](docs/github-actions-explained.md): every CI concept used here
- [contract/questions.md](contract/questions.md): the questions, every cleaning rule and every formula
- [CONTRIBUTING.md](CONTRIBUTING.md) · [CHANGELOG.md](CHANGELOG.md) · [LICENSE](LICENSE) (MIT)

Questions or problems: open an issue using the templates, or contact us via <https://www.aicancode.org/contact>.
