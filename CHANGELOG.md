# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/). The data contract (`contract/data-contract.yaml`) and the
answers schema have their own versions, recorded in every `answers.json`.

## [Unreleased]

## [1.0.0] - 2026-07-22
### Added
- The analysis of the 2026-06 export in three tracks with identical `answers.json` (Python: pandas,
  SciPy, statsmodels, Jupyter; SQL: DuckDB with a thin Python runner; R: tidyverse, base stats,
  R Markdown): cleaning with counted issues, contract checks with severities, the funnel by device,
  the CMH-adjusted payment-step test, Welch's test on order value, the opportunity in rupees and the
  decision (`run_targeted_experiment`).
- Requirements, the analysis plan and ADRs 0001-0005.
- Tests per track: unit tests on the tiny fixture and the stats cases, data tests on the real
  export, golden answers, invariants and contract-violation tests; coverage gate 85 %.
- CI: path filters, a reusable per-track workflow, parity of the three tracks with the golden file,
  the dashboard tests, a Docker job; Dependabot.
- The Streamlit dashboard with the optional AI narrator (OpenAI-compatible, offline by default,
  guardrails with a deterministic fallback) and the downloadable decision memo.
- Dockerfiles (non-root, read-only, few layers), `docker-compose.yml` (dashboard + `pipelines`
  profile + parity), `scripts/smoke-test.sh`, `deploy.yml` (GHCR, optional Render), `docs/runbook.md`.
