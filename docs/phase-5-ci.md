---
phase: 5
slug: phase-5-ci
title: CI with GitHub Actions
duration: 2.5 h
start_tag: phase-4-end
end_tag: phase-5-end
---
# Phase 5 · CI with GitHub Actions

## 1. Why it matters
"It runs on my laptop" is the analyst's version of "works on my machine". A notebook that only runs
in your kernel, with packages only you installed, is not reproducible; neither is a report someone
re-ran "with a small fix". Continuous integration runs the whole analysis from a clean checkout on
every push: lint, unit tests, data tests with a coverage gate, the report executed top to bottom,
and a **parity job** that compares every track's `answers.json` with the golden answers. Every PR now
carries proof that the numbers did not change, or a red X that says exactly which one did.

## 2. Objectives
By the end of this phase you can:
- Explain workflows, jobs, steps, runners, triggers, matrices, caches, artifacts and reusable workflows.
- Replace the starter CI with a pipeline that runs only the tracks whose files changed, through one reusable workflow.
- Execute the notebook / SQL report / R Markdown report in CI and upload it as an artifact.
- Pass `answers.json` between jobs with artifacts and fail the build when tracks disagree with the golden answers.
- Protect `main` with a required check and read a red run quickly.

## 3. Step-by-step instructions

### Step 5.1 · Read the starter workflow
Open `.github/workflows/ci.yml` next to [GitHub Actions explained](github-actions-explained.md) §1-§5.
It has one job with a matrix of three tracks: each gets a fresh Ubuntu runner, sets up Python (or R
with `r-lib/actions`), installs, lints and runs the unit tests. Find in the YAML: the triggers, the
matrix, the cache and the `working-directory` default. Note what it does **not** do: data tests,
coverage, reports, parity.

### Step 5.2 · One reusable workflow for all tracks
Create `.github/workflows/reusable-track-ci.yml` (`on: workflow_call`, input `track`). Because every
track has the same Makefile targets, the steps are identical: install, lint, test, coverage, run,
report. Only the setup differs:

<!-- track:python -->
`actions/setup-python@v5` with `cache: pip` keyed on `tracks/python/requirements-dev.txt`; `make
report` executes the notebook with `jupyter nbconvert --execute`, which fails the job on any cell error.
<!-- /track -->

<!-- track:sql -->
`actions/setup-python@v5` (the SQL track's runner is Python; DuckDB is a pip package, so there is no
database service to start); `make lint` runs `sqlfluff` on every SQL file, `make report` writes `out/report.md`.
<!-- /track -->

<!-- track:r -->
`r-lib/actions/setup-r@v2` with `use-public-rspm: true` (binary packages from Posit Package Manager:
minutes instead of compiling the tidyverse), `r-lib/actions/setup-r-dependencies@v2` reads
`DESCRIPTION` and caches the library, `r-lib/actions/setup-pandoc@v2` lets `rmarkdown::render` knit HTML.
<!-- /track -->

Upload `out/answers.json` as an artifact named `answers-<track>`, and the report and coverage as `report-<track>`.

### Step 5.3 · The main workflow: path filters, parity, dashboard, ci-ok
Replace `ci.yml` with the full pipeline (compare with the reference at `phase-5-end`):
1. `changes` uses `dorny/paths-filter` to decide what changed: a track folder, `dashboard/`, docs, or
   shared files (`contract/`, `data/`, `scripts/`, workflows). Shared changes run everything.
2. `contract` checks the shared files: `generate_data.py --check`, the golden answers against the
   schema, `shellcheck`, and `build-cms.py --check`.
3. `python`, `sql`, `r` call the reusable workflow.
4. `parity` downloads every `answers-*` artifact and runs `scripts/parity.py` against the golden
   file of the same export. It writes the result to the job summary.
5. `dashboard` lints and tests the dashboard (its AI narrator is tested against a fake LLM server, no key).
6. `ci-ok` depends on everything and fails if any needed job failed: the one check to require.

### Step 5.4 · Validate locally, then push
```bash
pipx run actionlint            # or: brew install actionlint / go install …
python3 scripts/build-cms.py --check
git switch -c ci/full-pipeline && git add .github && git commit -m "ci: reusable track workflow, parity and dashboard jobs, ci-ok"
git push -u origin ci/full-pipeline
```
Open the PR and watch the Actions tab: the first R run takes longer (the package cache is cold); the
second is much faster. Download the `report-<track>` artifact and open the executed report.

### Step 5.5 · Protect main
In your fork: **Settings → Branches → Add branch ruleset** (or classic protection) for `main`:
require a pull request, require the status check **`ci-ok`**, require branches to be up to date,
block force pushes. From now on a PR that changes a number without changing the golden file (with a
reason in the contract) cannot be merged.

### Step 5.6 · Make it fail once
On a branch, change one cleaning rule (for example keep the first row of a conflicting id), push, and
read the red run: which job failed, which step, which JSON path? Practise going from the red X to the
cause in under two minutes ([GitHub Actions explained](github-actions-explained.md) §16). Then revert.

## 4. AI-assist prompts

### Prompt 1: Explain this workflow line by line
```text
Explain this GitHub Actions workflow to a data analyst who has never used CI, line by line, and say
for each job what would make it fail: <paste .github/workflows/ci.yml>. Then list what it would cost
in minutes per push and how the path filter changes that.
```
**Verify the output by:** checking every action and input it mentions against the action's README
(`dorny/paths-filter`, `actions/upload-artifact`, `r-lib/actions`); assistants invent inputs that do
not exist. Confirm the minutes with a real run's timing.

### Prompt 2: Why is my R job slow or failing?
```text
My GitHub Actions job for an R package fails or takes 15 minutes at "setup-r-dependencies". Here is
the log excerpt: <paste the last 40 lines>. The DESCRIPTION is: <paste>. What is the cause and the
smallest fix (binary packages, system libraries, the cache key)?
```
**Verify the output by:** applying one change at a time and comparing the job's timing and log; never
add `sudo apt install` lines for libraries the log does not ask for.

### Prompt 3: Review my parity job
```text
Here is a CI job that downloads artifacts from three jobs and compares JSON files: <paste the parity
job>. What happens if one track job is skipped by the path filter, or fails? Is the job's `if:`
correct? Suggest the minimal change so the build fails when any compared file differs, and passes
when a track was legitimately skipped.
```
**Verify the output by:** reasoning through the three cases (all ran; one skipped; one failed) with
the `needs.*.result` values and `ci-ok`'s logic, and testing one case with a PR that only touches one track.

## 5. Deliverables
- [ ] `.github/workflows/reusable-track-ci.yml` and the full `ci.yml` with changes, contract, tracks, parity, dashboard and ci-ok.
- [ ] A green run on a PR, with the executed report downloadable as an artifact and the parity result in the job summary.
- [ ] `main` protected with `ci-ok` as the required check.
- [ ] Notes on one deliberately red run: job, step, cause, time to diagnose.
- [ ] An `AI_LOG.md` entry.

## 6. Self-check quiz

### Q1. Why do the three tracks share one reusable workflow?
- [ ] GitHub allows only one workflow per repository
- [x] The steps are identical because every track has the same Makefile targets; one definition means one place to fix and no drift between tracks
- [ ] Reusable workflows are faster
- [ ] Matrix builds cannot run R
> **Answer:** The Makefile is the interface; CI calls `make install lint test coverage run report` in any track. Only the toolchain setup differs, and that is a few `if:` lines.

### Q2. How does the parity job get the other jobs' answers.json?
- [ ] It reads them from the runner's disk
- [ ] It re-runs the three pipelines
- [x] Each track job uploads `answers-<track>` as an artifact; the parity job downloads them
- [ ] Through a database service
> **Answer:** Every job runs on a fresh machine. Artifacts are the way to pass files between jobs (and to let humans download reports).

### Q3. Why execute the notebook or R Markdown report in CI?
- [ ] To make the run longer
- [x] To prove the report runs top to bottom from a clean checkout with the pinned dependencies, so its numbers are reproducible
- [ ] Because GitHub displays notebooks
- [ ] To generate the golden answers
> **Answer:** A report that fails or depends on hidden state fails CI. The executed report is attached to the run as evidence.

### Q4. Why is `ci-ok`, not every job, the required status check?
- [ ] Required checks cannot be reusable workflows
- [x] With path filters, some jobs are legitimately skipped; one aggregator job that fails on any failure or cancellation (and accepts skips) gives branch protection one stable name
- [ ] It is cheaper
- [ ] GitHub limits required checks to one
> **Answer:** A required check that is skipped never reports, so the PR would wait forever. The aggregator turns "all needed jobs passed or were skipped" into one result.

### Q5. What does `use-public-rspm: true` in `setup-r` do?
- [ ] Uses a public R mirror for documentation
- [x] Installs binary packages from Posit Public Package Manager instead of compiling them from source, which cuts minutes from each run
- [ ] Makes the R job public
- [ ] Disables the cache
> **Answer:** Compiling dplyr and friends from source on Linux takes a long time; binaries for the runner's Ubuntu version install in seconds.

### Q6. A PR changes a cleaning rule and CI fails only in the parity job. What does that mean?
- [ ] CI is flaky
- [x] The rule change moved at least one number: either the change is a bug, or it is intended and needs a contract change and new golden answers agreed by all tracks
- [ ] The artifact upload failed
- [ ] The golden file must be deleted
> **Answer:** Parity makes number changes visible and deliberate. An intended change updates `questions.md` (with a version bump), all tracks and the golden file in one reviewed PR.

## 7. What you learned
- The vocabulary and building blocks of GitHub Actions, applied to an analysis instead of an app.
- One reusable workflow driven by a uniform Makefile interface across Python, SQL and R.
- Reports executed in CI and attached as artifacts; reproducibility as an automatic check.
- Artifacts between jobs and a parity job that guards every number.
- Branch protection with an aggregator check, and fast diagnosis of a red run.

## 8. Catch-up git commands
```bash
git fetch upstream --tags
git switch -c my-phase-6 phase-5-end
git diff phase-4-end phase-5-end -- .github     # the reference workflows
```
