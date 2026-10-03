# FunnelLens retrospective (reference solution, v1.0.0 → v1.1.0)

Format: *What went well / What didn't / What I'd change*, plus one technical, one process and one AI
lesson, as asked in Phase 8. Written by the maintainers who built the reference solution. Yours will
(and should) look different.

## What went well
- **A decision, not a description.** The requirements fixed the decision rule before any number was
  computed: a significant adjusted payment-step gap **and** an uplift above ₹25 lakh/month means
  rebuild; otherwise a targeted experiment. The result (₹16.3 lakh, then ₹14.3 lakh on the refresh)
  could not be argued into a different answer after the fact.
- **The spec made three tracks agree.** `contract/questions.md` defines every cleaning rule, count
  and formula. Python (pandas), SQL (DuckDB) and R (tidyverse) produce the same `answers.json` to 1e-9 on
  both exports, checked in CI by `scripts/parity.py` against golden files.
- **Simpson's paradox was caught by design.** The analysis plan required every device comparison to be
  repeated within channels. The aggregate mobile cart gap (−4.5 points) disappeared within channels
  (CMH OR 1.08), which kept the recommendation focused on the payment step.
- **Contract checks failed loudly.** On the August refresh, the v1.0 pipeline exited 3 on a new
  channel instead of quietly counting referral sessions as `unknown`.
- **A safe AI feature.** The narrator only sees numbered aggregate facts; guardrails reject invented
  numbers, unknown citations, causal words and a missing caveat; the template fallback is visible.
  CI tests every guardrail against a fake LLM server, without a key.

## What didn't go well
- **Row checks missed a broken week.** Every `error` check passed on 2026-08; one `warn` fired (3.3 %
  orders without checkout). Only weekly monitoring, added in Phase 7, showed that mobile
  checkout-given-cart had collapsed by 80 % in 2026-W31. Detection took eight days after the app release.
- **The spec had an ambiguity.** "Count sessions with an unknown channel" did not say whether before or
  after the new week exclusion. Python and SQL disagreed (3,478 vs 3,361); both were faithful to the text.
- **R in CI was slow at first.** Installing the tidyverse from source took 14 minutes per run, until
  binary packages (Posit Public Package Manager) and the dependency cache brought it to about 2.
- **Statistics from assistants needed full re-derivation.** A CMH variance term and a worked example
  were wrong in otherwise excellent explanations.

## What I'd change next time
1. Add **time-based monitoring to v1.0**, not after the first incident: a weekly view of the key
   funnel rates with a median baseline costs about 40 lines per track.
2. Write a **worked example for every counting rule** in the spec, with the tiny fixture's expected
   value next to it, before implementing the second track.
3. **Schedule the pipeline** (weekly, on the latest export) so data problems are found days, not
   weeks, after they happen.
4. Write the **experiment design** (metric, minimum detectable effect, sample size, duration) as part
   of the recommendation, not as a follow-up.

## Three lessons
- **Technical:** adjust for the obvious confounder before you interpret a gap. A pooled comparison of
  mobile and desktop mixed the channel effect into the device effect, and pointed at the wrong step.
- **Process:** treat data like an API: a versioned contract, checks with severities, golden files and
  additive schema changes made the refresh a reviewable change instead of a silent drift.
- **AI:** an assistant is fastest at explanations and slowest to be trusted with arithmetic. Every
  formula went through `contract/fixtures/stats-cases.json`, and every number in a summary must be
  traceable to `answers.json`; the narrator's guardrails apply the same rule to the model at run time.
