# M2: run the contract checks (contract/data-contract.yaml `checks`) on the clean tables.
# Each check counts failing rows; it passes when that count is 0 (or the ratio is at most `max`).

failing_rows <- function(check, clean, export, contract) {
  # TODO(M2) failing_rows: one contract check -> (failing rows, observed value), by check type (unique,
  # not_null, accepted_values, range, relationship, in_period, max_ratio, row_count_min). Spec:
  # contract/questions.md §2 and contract/data-contract.yaml `checks`; tests: checks.
  stop("TODO(M2) failing_rows: see the comment above")
}

run_checks <- function(clean, export, contract) {
  # TODO(M2) run_checks: every check of contract/data-contract.yaml, in contract order. Spec:
  # contract/questions.md §2 and contract/data-contract.yaml `checks`; tests: checks.
  stop("TODO(M2) run_checks: see the comment above")
}

raise_on_errors <- function(results) {
  # TODO(M2) raise_on_errors: a failing check with severity error stops the run with a ContractError (exit 3): a
  # wrong number is worse than no number. Spec: contract/questions.md §2 and contract/data-contract.yaml
  # `checks`; tests: checks.
  stop("TODO(M2) raise_on_errors: see the comment above")
}
