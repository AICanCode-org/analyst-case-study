---
phase: 6
slug: phase-6-deploy
title: Dashboard, AI narrator, Docker and delivery
duration: 3 h
start_tag: phase-5-end
end_tag: phase-6-end
release: v1.0.0
---
# Phase 6 · Dashboard, AI narrator, Docker and delivery

## 1. Why it matters
An analysis that lives in a notebook reaches the people who open notebooks. The Head of Product
needs the recommendation, the evidence and the caveat on one screen, and a memo to forward. In this
phase you ship the old "Present" step as a product: the shared **Streamlit dashboard** reads your
`answers.json`, an optional **AI narrator** writes the summary under strict guardrails, and
everything runs in **Docker** with one command, so anyone can reproduce the numbers without
installing pandas, DuckDB or R. A version tag publishes the images; that is release **v1.0.0**.

## 2. Objectives
By the end of this phase you can:
- Run the dashboard on your own track's `answers.json` and explain what each tab shows.
- Explain the narrator's design (facts in, guardrails out, template fallback) and see each guardrail reject a bad summary.
- Read the Dockerfiles: few layers, non-root user, read-only file system, no secrets in the image.
- Run every track's pipeline and the parity check in containers, and smoke-test the dashboard, also with the AI provider down.
- Release v1.0.0: CHANGELOG, tag, images on GHCR, and (optionally) a free public deployment.

## 3. Step-by-step instructions

### Step 6.1 · The dashboard on your answers
```bash
cd dashboard
make install
make run ANSWERS=../tracks/<python|sql|r>/out/answers.json     # http://localhost:18120 by default (PORT=…)
```
`make prepare` validates the answers against the schema, then writes `static/answers.json`,
`static/narrative.json` (the summary) and `static/onepager.md` (the decision memo). The app only
displays those files: it never sees raw data. Walk through the tabs and check three numbers against
your report. Any track's answers work, because they are identical.

### Step 6.2 · The AI narrator and its guardrails
Read `funnellens_dashboard/facts.py` and `narrator.py`. The model receives numbered facts
(`[F1] Mobile is 69.2% of sessions but 60.6% of revenue.`) and must cite them. `validate()` rejects a
summary that is longer than 900 characters, cites an unknown fact, contains a number that is not a
correct rounding of a fact value, mentions a date that is not in the facts, uses causal words
("caused", "proves", "guaranteed"), or omits the recommendation or the caveat. On any rejection,
timeout or HTTP error, the deterministic template is used and the reason is shown.

Try it with a real model if you have one (all optional, nothing is paid):
```bash
# a local Ollama (no key):  ollama pull llama3.2
AI_PROVIDER=llm LLM_BASE_URL=http://localhost:11434/v1 LLM_MODEL=llama3.2 make prepare ANSWERS=…
cat static/narrative.json        # source "llm", or "template" with the reason it was rejected
```
Then read `tests/test_narrator.py`: every guardrail has a test against a fake LLM server, so CI
needs no key. Write down one way a summary could still mislead (emphasis, omission) that no
guardrail catches; a human review of the memo stays part of the process.

### Step 6.3 · The Dockerfiles
Open `tracks/<yours>/Dockerfile` and `dashboard/Dockerfile`. They share four habits:
1. **Few layers:** a `FROM scratch AS src` stage collects the files; the final stage installs the
   dependencies in one `RUN` (with a bind mount, so `requirements.txt` is not even copied) and copies
   the code in one `COPY`. Small images, fast rebuilds.
2. **Non-root:** user `10001`, created in the same `RUN`.
3. **No data, no secrets in the image:** the export is mounted read-only at run time; the AI key, if
   any, is an environment variable.
4. **The dashboard image bakes answers:** its first stage runs the Python pipeline on the committed
   export, so the image starts with real answers; `ANSWERS_PATH` can point to another track's output.

<!-- track:r -->
The R image installs R and the tidyverse from Debian's `r-base-core` and `r-cran-*` packages (binary,
one `apt-get` layer), on the same slim Python base as the other images: about 300 MB instead of the
1-2 GB of a full `rocker/tidyverse` image.
<!-- /track -->

### Step 6.4 · Compose: pipelines, parity and the dashboard
```bash
cp .env.example .env                                   # optional: ports, AI provider
docker compose --profile pipelines build
for t in python sql r; do docker compose --profile pipelines run --rm "$t"; done
docker compose --profile pipelines run --rm --no-deps parity        # IDENTICAL x3
docker compose up -d --wait dashboard                               # http://localhost:8501
scripts/smoke-test.sh http://localhost:8501
```
The pipelines run read-only, non-root, and write to a named volume that the dashboard can read
(`ANSWERS_PATH=/answers/r/answers.json docker compose up -d dashboard` shows the R track's answers).

### Step 6.5 · Smoke test with the AI provider down
```bash
AI_PROVIDER=llm LLM_BASE_URL=http://10.255.255.1:9/v1 LLM_TIMEOUT_MS=1500 \
  docker compose up -d --wait --force-recreate dashboard
EXPECT_FALLBACK=true scripts/smoke-test.sh http://localhost:8501   # 10 checks, incl. "fell back to the template"
docker compose --profile pipelines down -v
```
The dashboard must work, and say why the summary is the template, when the model is unreachable.

### Step 6.6 · CI builds the images; a tag publishes them
Compare `.github/workflows/ci.yml` at `phase-6-end` with Phase 5: a `docker` job builds the four
images, runs the three pipelines and the parity check in containers, and runs both smoke tests.
`.github/workflows/deploy.yml` runs on a version tag: it pushes
`ghcr.io/<owner>/funnellens-{dashboard,python,sql,r}:<version>` with the built-in `GITHUB_TOKEN`
(see [GitHub Actions explained](github-actions-explained.md) §12).

**Optional free deployment.** Render can run the dashboard image for free (it sleeps when idle):
create a *Web Service* from the image `ghcr.io/<owner>/funnellens-dashboard:latest` (make the package
public first), copy its *Deploy Hook* URL into the repository secret `RENDER_DEPLOY_HOOK_URL` of an
environment named `production`, and its URL into the variable `RENDER_APP_URL`. Without them the
deploy job succeeds with a notice. Keep `AI_PROVIDER=offline` on a public deployment unless you set a
spending limit on the key.

### Step 6.7 · Release v1.0.0
1. Move the `Unreleased` notes in `CHANGELOG.md` to `## [1.0.0]` with today's date.
2. Write `docs/runbook.md`: how to re-run the analysis on a new export, what each exit code means,
   what to do when a check fails, how to switch the narrator off.
3. Forward the memo (`static/onepager.md`, also downloadable from the dashboard) to the Head of
   Product: recommendation, evidence, caveat, next step (the experiment).
4. Tag and push: `git tag -a v1.0.0 -m "FunnelLens v1.0.0" && git push origin v1.0.0`.

## 4. AI-assist prompts

### Prompt 1: Try to break the guardrails
```text
Here is the system prompt and the numbered facts of an AI summary feature: <paste SYSTEM_PROMPT from
narrator.py and the facts block from static/onepager.md>. Write five summaries that a careless or
manipulated model might produce, each violating a different rule (an invented number, a wrong
rounding, a causal claim, a missing caveat, a fake citation), and one that is misleading but follows
every rule.
```
**Verify the output by:** feeding each summary to `validate()` (a quick test with the fake LLM
fixture) and checking that the five are rejected for the reason you expect. Add a test for any that
passes, and write the "misleading but valid" one into your notes as a known limitation.

### Prompt 2: Review my Dockerfile
```text
Review this Dockerfile for a data pipeline image: <paste>. Check: layer count and order for cache
efficiency, the final image size, running as non-root, secrets or data baked into layers, and whether
the container works with a read-only root file system. Suggest changes with the reason for each, and
do not change the base image.
```
**Verify the output by:** rebuilding and comparing `docker image ls` sizes and `docker history`
layer counts before and after, running the container with `--read-only`, and checking `docker run
--rm <image> id -u` prints 10001.

### Prompt 3: Write the decision memo
```text
Here is the one-page decision memo generated from my analysis: <paste static/onepager.md>. Rewrite
it for a Head of Product who has 2 minutes: recommendation first, three supporting facts with their
intervals, one sentence on what the data cannot show, and the next step. Use only numbers that appear
in the memo, and keep every number exactly as written.
```
**Verify the output by:** checking every number in the rewrite against the memo character by
character, and rejecting any causal phrasing ("the checkout causes"). Keep the original as the
attachment: the rewrite is a cover note, not a replacement.

## 5. Deliverables
- [ ] The dashboard running on your track's answers, locally and in Docker.
- [ ] Notes: the guardrails in your own words, one limitation no guardrail catches.
- [ ] `docker compose` pipelines + parity `IDENTICAL`, smoke test 9/9 and the fallback smoke test 10/10.
- [ ] CI with the Docker job green; `deploy.yml` in place (Render optional).
- [ ] `CHANGELOG.md` 1.0.0, `docs/runbook.md`, the tag `v1.0.0`, and the memo sent (or drafted).

## 6. Self-check quiz

### Q1. Why does the narrator receive numbered facts instead of answers.json?
- [ ] The model cannot read JSON
- [x] Facts are short aggregates whose exact values are known, so every citation and every number in the summary can be checked against them
- [ ] It is required by the OpenAI API
- [ ] Facts are encrypted
> **Answer:** The guardrails work because the input is small and structured: a number in the output must be a correct rounding of a fact value, and a citation must name a fact that exists.

### Q2. The model is unreachable. What does the dashboard show?
- [ ] An error page
- [ ] Nothing until the model is back
- [x] The deterministic template summary, marked as such, with the reason the AI was not used
- [ ] The last summary the model wrote
> **Answer:** The template is computed from the same facts and always passes the guardrails, so the product works offline and the fallback is visible, never silent.

### Q3. A model writes "The checkout caused a ₹16.3 lakh monthly loss [F7]". Why is it rejected?
- [ ] The number is wrong
- [ ] The citation is unknown
- [x] "caused" is a causal claim the observational data cannot support
- [ ] It is too long
> **Answer:** The number and citation may be correct; the claim is not. Causal language is banned because only an experiment could establish it.

### Q4. Why does each image install its dependencies and create the user in a single `RUN`?
- [ ] Docker allows only one `RUN`
- [x] Each instruction adds a layer; fewer layers make smaller images and faster pulls, and the dependency layer stays cached when only the code changes
- [ ] It makes the image run faster
- [ ] It hides the user from `docker inspect`
> **Answer:** Layer discipline matters on every laptop and CI runner. Code is copied last so changing it does not invalidate the expensive dependency layer.

### Q5. Why are the pipeline containers run with a read-only file system and as user 10001?
- [ ] Docker requires it
- [x] Least privilege: a compromised or buggy container cannot modify its own code or write outside the output volume, and does not run as root
- [ ] It makes the analysis faster
- [ ] The CSVs are read-only
> **Answer:** An analysis container needs to read the export and write one folder. Everything else is denied by default.

### Q6. What does pushing the tag `v1.0.0` trigger?
- [ ] Nothing: tags are only labels
- [ ] A new golden file
- [x] The deploy workflow: the four images are pushed to GHCR with the version, and the optional Render deploy runs if configured
- [ ] A merge of `solution` into `main`
> **Answer:** `on: push: tags: ["v*.*.*"]` ties releases to tags, so the image version always matches the code that produced it.

## 7. What you learned
- Presenting an analysis as a product: dashboard, memo and recommendation on one screen.
- A safe AI feature: aggregates in, guardrails out, a visible deterministic fallback.
- Small, non-root, read-only Docker images with few layers, and Compose for pipelines, parity and the app.
- Smoke tests that include the failure of an external dependency.
- Releasing with a tag: CHANGELOG, runbook, images on GHCR, optional free deployment.

## 8. Catch-up git commands
```bash
git fetch upstream --tags
git switch -c my-phase-7 phase-6-end      # = v1.0.0
git diff phase-5-end phase-6-end --stat
```
