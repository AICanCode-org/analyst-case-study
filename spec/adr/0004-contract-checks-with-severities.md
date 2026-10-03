# ADR-0004: Contract checks with severities: `error` stops the run, `warn` is reported

* **Status:** accepted
* **Date:** 2026-07-04
* **Deciders:** analytics team

## Context
Exports change without notice (new values, broken tracking, duplicated loads). A pipeline that always
produces numbers will eventually produce wrong numbers that look right.

## Options considered
1. **No checks; trust the cleaning** — simple; silent failures.
2. **Checks that only warn** — never blocks; warnings get ignored.
3. **Declarative checks with a severity** in the contract (`unique`, `not_null`, `accepted_values`,
   `range`, `relationship`, `in_period`, `max_ratio`, `row_count_min`).

## Decision
Option 3. Checks run on the clean tables and issue counts, in contract order, and are all reported in
`data_quality.checks`. A failing `error` check raises a contract error: exit code 3, no `answers.json`.

## Consequences
A wrong number is replaced by a clear failure naming the check and the failing row count. Adding a
new accepted value (for example a new channel) needs a contract change with a version bump, which is
exactly the review a business change deserves. Thresholds of `warn` checks need occasional tuning.

## AI assistance
An assistant proposed great_expectations; rejected for the course (heavy, Python only); the eight
check types are 10-20 lines each in every track.
