# FunnelLens specification

The **contract** (what every track computes, exactly) lives in [`../contract/`](../contract/questions.md)
and is provided on `main`. This folder holds the documents you write yourself, before the code:

| File | What it is | Written in |
|---|---|---|
| `requirements.md` | The brief turned into questions, a decision rule, stakeholders, acceptance criteria, risks | Phase 1 |
| `analysis-plan.md` | Hypotheses, metrics, tests, confounders, what would change the decision, the pipeline | Phase 2 |
| `adr/` | Analysis Decision Records (one decision per file: tools, tests, rules) | Phase 2+ |

How they relate: `requirements.md` says *what* must be decided and how good the answer must be;
`analysis-plan.md` says *how* it will be answered before anyone looks at a p-value (so the analysis
cannot be bent towards the answer someone wants); `contract/questions.md` pins the exact rules so three
implementations agree to the last digit.
