# ADR-0003: One answers.json contract for three tracks, golden answers and parity to 1e-9

* **Status:** accepted
* **Date:** 2026-07-04
* **Deciders:** analytics team

## Context
Learners pick Python, SQL or R; reviewers must be able to trust any of them. Analyses usually end in
a notebook whose numbers nobody can diff.

## Options considered
1. **Each track produces its own report** — natural; nothing to compare, no way to catch a wrong formula.
2. **A shared machine-readable output** (`answers.json` + JSON Schema) compared to golden answers —
   more upfront work; every number is diffable.
3. **One reference track, the others "inspired by" it** — less work; errors in the reference spread.

## Decision
Option 2. Every track writes `answers.json` (schema `contract/answers.schema.json`); `scripts/parity.py`
compares files (integers exactly, floats to 1e-9 relative, the `generator` field ignored). The golden
file is regenerated only when all three tracks agree.

## Consequences
Three independent implementations act as each other's tests: a parity failure points at an ambiguity
in the contract or a bug. The dashboard reads any track's output. Floating-point order of operations
must be stable enough for 1e-9 (sums of integers stay integers; rates are computed from counts).

## AI assistance
None beyond the review of the schema's `required` lists.
