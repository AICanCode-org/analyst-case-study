"""M2: run the contract checks (contract/data-contract.yaml `checks`) on the clean tables.

Each check counts *failing rows*; a check passes when that count is 0 (or the ratio is at most `max`).
The same eight check types exist in every track, so a check means the same thing everywhere.
"""

from __future__ import annotations

from .clean import Clean
from .contract import ContractError, Export


def _table(clean: Clean, name: str):
    return getattr(clean, name)


def failing_rows(check: dict, clean: Clean, export: Export, contract: dict) -> tuple[int, float | None]:
    """Return (failing_rows, observed) for one check. `observed` is the ratio for max_ratio, else None."""
    kind = check["type"]
    if kind == "max_ratio":
        layer, table = check["of"].split(".")
        denominator = clean.raw_rows[table] if layer == "raw" else len(_table(clean, table))
        count = clean.issues[check["issue"]]
        ratio = count / denominator if denominator else 0.0
        return (count if ratio > check["max"] else 0), ratio
    df = _table(clean, check["table"])
    if kind == "row_count_min":
        return (0 if len(df) >= check["min"] else 1), None
    col = df[check["column"]]
    if kind == "unique":
        return int(col.duplicated(keep=False).sum()), None
    if kind == "not_null":
        return int(col.isna().sum()), None
    if kind == "accepted_values":
        return int((~col.isin(contract["cleaning"][check["values_from"]])).sum()), None
    if kind == "range":
        return int(((col < check["min"]) | (col > check["max"])).sum()), None
    if kind == "in_period":
        day = col.map(lambda t: t.date())
        return int(((day < export.period_start) | (day > export.period_end)).sum()), None
    if kind == "relationship":
        to_table, to_col = check["to"].split(".")
        return int((~col.isin(_table(clean, to_table)[to_col])).sum()), None
    raise ContractError(f"unknown check type {kind!r} in {check['id']}")


def run_checks(clean: Clean, export: Export, contract: dict) -> list[dict]:
    results = []
    for check in contract["checks"]:
        count, observed = failing_rows(check, clean, export, contract)
        status = "pass" if count == 0 else ("fail" if check["severity"] == "error" else "warn")
        results.append(
            {
                "id": check["id"],
                "type": check["type"],
                "severity": check["severity"],
                "status": status,
                "failing_rows": count,
                "observed": observed,
            }
        )
    return results


def raise_on_errors(results: list[dict]) -> None:
    failed = [r for r in results if r["status"] == "fail"]
    if failed:
        detail = ", ".join(f"{r['id']} ({r['failing_rows']} rows)" for r in failed)
        raise ContractError(f"data contract violated: {detail}")
