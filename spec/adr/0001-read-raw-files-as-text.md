# ADR-0001: Read every raw CSV as text; the cleaning rules decide every type

* **Status:** accepted
* **Date:** 2026-07-03
* **Deciders:** analytics team

## Context
Exports contain amounts like `₹1,299.00`, `Rs. 1,299` and `-₹499.00`, two date formats (one day-first),
ids with stray spaces and empty strings that mean "unknown". Three tracks (pandas, DuckDB, readr) must
produce identical numbers, and each library guesses types differently.

## Options considered
1. **Let the reader infer types** (`pd.read_csv` defaults, DuckDB `read_csv_auto`, `readr::read_csv`) —
   least code; but each library guesses differently, a bad value becomes missing silently, and
   `05/01/2026` may be read as 1 May.
2. **Declare types at read time** — explicit; but a single bad value fails the read or becomes NA
   without being counted.
3. **Read everything as text, parse in the cleaning rules** — more code; every rejected value is
   counted, and the rule is identical in every language.

## Decision
Option 3. `load_raw` (and `01_load.sql`) read all columns as text with no NA conversion; parsing
happens in the rules of `contract/questions.md` §2, each with its issue counter.

## Consequences
Every defect is visible in `data_quality.issues` and the tracks agree exactly. Cleaning code is longer
and must be unit-tested on the tiny fixture. A new date format in a future export fails loudly (bad
timestamps rise, the check reports it) instead of being half-parsed.

## AI assistance
An assistant suggested `parse_dates=True` with `dayfirst=True`; rejected because pandas would then
interpret the ISO dates day-first too in some versions. Verified with the tiny fixture.
