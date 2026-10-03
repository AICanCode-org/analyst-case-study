# FunnelLens documentation

Start with [Phase 0](phase-0-setup.md). Each phase lists its start and end tag in the header, so you can
start any phase from the reference state (`git switch -c my-phase-N phase-(N-1)-end`).

| # | Phase | Duration | Start | End |
|---|---|---|---|---|
| 0 | [Setup and the brief](phase-0-setup.md) | 1.5 h | `main` | `phase-0-end` |
| 1 | [Requirements: questions, decisions and acceptance criteria](phase-1-requirements.md) | 2 h | `phase-0-end` | `phase-1-end` |
| 2 | [Design: data contract, analysis plan and ADRs](phase-2-design.md) | 3 h | `phase-1-end` | `phase-2-end` |
| 3 | [Implementation in five milestones](phase-3-implementation.md) | 12 h | `phase-2-end` | `phase-3-end` |
| 4 | [Testing the analysis](phase-4-testing.md) | 3.5 h | `phase-3-end` | `phase-4-end` |
| 5 | [CI with GitHub Actions](phase-5-ci.md) | 2.5 h | `phase-4-end` | `phase-5-end` |
| 6 | [Dashboard, AI narrator, Docker and delivery](phase-6-deploy.md) | 3 h | `phase-5-end` | `phase-6-end` / `v1.0.0` |
| 7 | [Data refresh, monitoring and a post-mortem](phase-7-observability.md) | 3 h | `phase-6-end` | `phase-7-end` / `v1.1.0` |
| 8 | [Retrospective and portfolio](phase-8-retrospective.md) | 1.5 h | `phase-7-end` | `phase-8-end` |

Reference material:
- [GitHub Actions explained](github-actions-explained.md): triggers, jobs, matrix, caching, reusable
  workflows, artifacts, permissions, secrets vs variables, GHCR.
- [`../contract/`](../contract/questions.md): the questions, the cleaning rules and every formula,
  the data contract, the answers schema, the fixtures and the golden answers.
- [`../spec/`](../spec/README.md): requirements, analysis plan, ADRs.
- Solution branch only: `runbook.md` (Phase 6), `postmortem-2026-W31.md` (Phase 7),
  `retrospective.md` (Phase 8).

## From the old five-step guide
The old guide had five steps. The site keeps them in order as the first five phases, and the content
moved like this:

| Old step | Now |
|---|---|
| 0 · The Brief | Phase 0 (the brief, the data, the deliverables) and Phase 1 (questions, decision rule, acceptance criteria) |
| 1 · Load and Clean | Phase 2 (the data contract) and Phase 3 M1-M2 (text-first loading, counted cleaning rules, contract checks) |
| 2 · Explore | Phase 3 M3 (funnel by device, channel and week; Simpson's paradox) |
| 3 · Test the Hypothesis | Phase 3 M4 (z test, Cochran-Mantel-Haenszel, Welch) and Phase 4 (golden answers, invariants, parity) |
| 4 · Present | Phase 3 M5 (decision + memo) and Phase 6 (dashboard, AI narrator, delivery) |

## Page format
Every phase page has front matter (`phase`, `slug`, `title`, `duration`, `start_*`, `end_tag`,
`release`) and the same eight sections, which `scripts/build-cms.py` turns into
`cms/analyst-case-study.json` (project metadata comes from `cms/project.json`):

1. Why it matters · 2. Objectives · 3. Step-by-step instructions (`### Step N.x`) ·
4. AI-assist prompts (`### Prompt n`, a `text` block, **Verify the output by**) · 5. Deliverables ·
6. Self-check quiz (`### Qn`, `- [ ]` / `- [x]`, `> **Answer:**`) · 7. What you learned ·
8. Catch-up git commands

Track-specific parts are wrapped in `<!-- track:python -->` … `<!-- /track -->` (also `sql`, `r`).
The site shows only the learner's track. On GitHub you see all three.
