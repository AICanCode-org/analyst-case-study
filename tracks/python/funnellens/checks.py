"""M2: run the contract checks (contract/data-contract.yaml `checks`) on the clean tables.

Each check counts *failing rows*; a check passes when that count is 0 (or the ratio is at most `max`).
The same eight check types exist in every track, so a check means the same thing everywhere.
"""

from __future__ import annotations

from .clean import Clean
from .contract import Export


def _table(clean: Clean, name: str):
    # TODO(M2) _table: the table a check runs on: raw_<table> for raw checks, else the clean table. Spec:
    # contract/questions.md §2 and contract/data-contract.yaml `checks`; tests: checks.
    raise NotImplementedError("TODO(M2) _table: see the comment above")


def failing_rows(check: dict, clean: Clean, export: Export, contract: dict) -> tuple[int, float | None]:
    """Return (failing_rows, observed) for one check. `observed` is the ratio for max_ratio, else None."""
    # TODO(M2) failing_rows: one contract check -> (failing rows, observed value), by check type (unique,
    # not_null, accepted_values, range, relationship, in_period, max_ratio, row_count_min). Spec:
    # contract/questions.md §2 and contract/data-contract.yaml `checks`; tests: checks.
    raise NotImplementedError("TODO(M2) failing_rows: see the comment above")


def run_checks(clean: Clean, export: Export, contract: dict) -> list[dict]:
    # TODO(M2) run_checks: every check of contract/data-contract.yaml, in contract order. Spec:
    # contract/questions.md §2 and contract/data-contract.yaml `checks`; tests: checks.
    raise NotImplementedError("TODO(M2) run_checks: see the comment above")


def raise_on_errors(results: list[dict]) -> None:
    # TODO(M2) raise_on_errors: a failing check with severity error stops the run with a ContractError (exit 3):
    # a wrong number is worse than no number. Spec: contract/questions.md §2 and contract/data-contract.yaml
    # `checks`; tests: checks.
    raise NotImplementedError("TODO(M2) raise_on_errors: see the comment above")
