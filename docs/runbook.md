# FunnelLens runbook

Who this is for: whoever re-runs the analysis on a new export, or answers "is the dashboard right?".

## 1. Re-run the analysis on a new export
1. Put the export in `data/raw/<YYYY-MM>/` (`users.csv`, `sessions.csv`, `events.csv`, `orders.csv`)
   and update `data/README.md` if the files changed shape.
2. Run one track (any; they agree): `cd tracks/python && make run DATA=../../data/raw/<YYYY-MM>`.
   Or, without installing anything: `EXPORT=<YYYY-MM> docker compose --profile pipelines up`.
3. Read the exit code:

| Exit | Meaning | What to do |
|---|---|---|
| 0 | `out/answers.json` written | Check the warnings in `data_quality.checks` (§3), then publish (§2). |
| 2 | A file or folder could not be read | Check the path and the four file names. |
| 3 | The data contract is violated (an `error` check failed) | No answers were written. Go to §3. |

## 2. Publish the new answers
1. Run the other tracks, or at least the parity check against the golden file of a known export.
2. Rebuild the dashboard with the new answers: `docker compose up -d --build dashboard`
   (or `cd dashboard && make run ANSWERS=…`).
3. Read the generated memo (`static/onepager.md`, or *Download the decision memo* in the app) **before** sending
   it. A human reads every AI summary: the guardrails check facts and words, not emphasis.
4. Smoke test: `scripts/smoke-test.sh http://localhost:8501`.

## 3. A check failed or warned
1. The message names the check and the failing row count, e.g.
   `data contract violated: sessions.channel.accepted (878 rows)`.
2. Look at the failing rows (`SELECT channel, count(*) FROM sessions GROUP BY 1`) and decide:
   - **The data is wrong** (a broken load, a tracking bug): tell the data owner, do not publish; keep
     the previous answers live.
   - **The business changed** (a new channel, a new payment method): change the contract with a
     version bump and a CHANGELOG line, keep the old version, re-run every track and the parity check.
   - **Never** delete a check or loosen a threshold to make a run pass without writing down why.
3. A `warn` check does not stop the run. Read it anyway: a small warning can hide a large, local problem.

## 4. The AI narrator
- Off by default (`AI_PROVIDER=offline`): the template summary is used, nothing leaves the machine.
- To switch it off in an emergency: set `AI_PROVIDER=offline` and restart the dashboard
  (`docker compose up -d --force-recreate dashboard`).
- If the model is slow or down, the dashboard shows the template and the reason; nothing else breaks.
  `LLM_TIMEOUT_MS` (default 8000) bounds the wait.
- Never put an API key in the image, the repository or a prompt; use `.env` (git-ignored) or a platform secret.

## 5. Releases
- A release is a tag `vX.Y.Z` on a commit with green CI. `deploy.yml` pushes
  `ghcr.io/<owner>/funnellens-{dashboard,python,sql,r}:X.Y.Z`; the optional Render job deploys the dashboard.
- Roll back: redeploy the previous image tag (Render: *Manual Deploy* → the previous image URL), or
  `git switch --detach vX.Y.Z && docker compose up -d --build dashboard` locally.
