"""Thin runner: sets the variables, loads the contract lists, runs sql/*.sql in order, runs the
contract checks (sql/checks/<type>.sql) and turns the result views into answers.json.

No analysis happens here: every number comes out of a SQL view. The runner only formats it.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

import duckdb
import yaml

from . import __version__
from .mathfn import erfc, t_quantile, t_two_sided_p

TRACK = Path(__file__).resolve().parents[1]
REPO = TRACK.parents[1]
SQL_DIR = TRACK / "sql"
DEFAULT_CONTRACT = REPO / "contract" / "data-contract.yaml"
SCRIPTS = ["01_load.sql", "02_clean.sql", "03_metrics.sql", "04_stats.sql", "05_answers.sql"]
TABLES = ["users", "sessions", "events", "orders"]
DEVICES = ["desktop", "mobile"]
IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")
SCHEMA_VERSION = "1.0"


class ContractError(Exception):
    """The input does not match the contract."""


def load_contract(path: str | os.PathLike | None = None) -> dict:
    p = Path(path or os.environ.get("CONTRACT_PATH") or DEFAULT_CONTRACT)
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_export(data_dir: str | os.PathLike) -> dict:
    meta_path = Path(data_dir) / "export.json"
    if not meta_path.exists():
        raise ContractError(f"{meta_path} not found: is --data an export folder like data/raw/2026-06?")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    start, end = date.fromisoformat(meta["period_start"]), date.fromisoformat(meta["period_end"])
    meta["months"] = (end.year - start.year) * 12 + end.month - start.month + 1
    return meta


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    con.create_function("erfc", erfc, ["DOUBLE"], "DOUBLE")
    con.create_function("t_two_sided_p", t_two_sided_p, ["DOUBLE", "DOUBLE"], "DOUBLE")
    con.create_function("t_quantile", t_quantile, ["DOUBLE", "DOUBLE"], "DOUBLE")
    return con


def ident(value: str) -> str:
    """Contract values become SQL identifiers, so accept only plain lower-case names."""
    if not IDENT.match(value):
        raise ContractError(f"not a plain identifier in the contract: {value!r}")
    return value


def prepare(con: duckdb.DuckDBPyConnection, data_dir: str | os.PathLike, contract: dict, export: dict) -> None:
    for table in TABLES:
        path = Path(data_dir) / f"{table}.csv"
        if not path.exists():
            raise ContractError(f"missing file {path}")
    con.execute("SET VARIABLE data_dir = ?", [str(Path(data_dir).resolve())])
    con.execute("SET VARIABLE period_start = CAST(? AS DATE)", [export["period_start"]])
    con.execute("SET VARIABLE period_end = CAST(? AS DATE)", [export["period_end"]])
    con.execute("SET VARIABLE months = CAST(? AS DOUBLE)", [export["months"]])
    con.execute("SET VARIABLE sample_rate = CAST(? AS DOUBLE)", [export["sample_rate"]])
    for key in ("alpha", "z_975", "rebuild_min_monthly_uplift_inr"):
        con.execute(f"SET VARIABLE {key} = CAST(? AS DOUBLE)", [contract["analysis"][key]])
    cleaning = contract["cleaning"]
    for name, key in (
        ("cfg_devices", "devices"),
        ("cfg_channels", "channels"),
        ("cfg_unknown_channels", "unknown_channel_values"),
        ("cfg_steps", "steps"),
    ):
        con.execute(f"CREATE OR REPLACE TABLE {name} (value VARCHAR)")
        con.executemany(f"INSERT INTO {name} VALUES (?)", [[v] for v in cleaning[key]])
    con.execute("CREATE OR REPLACE TABLE cfg_city_aliases (alias VARCHAR, canonical VARCHAR)")
    con.executemany("INSERT INTO cfg_city_aliases VALUES (?, ?)", list(cleaning["city_aliases"].items()))


def run_script(con: duckdb.DuckDBPyConnection, name: str) -> None:
    con.execute((SQL_DIR / name).read_text(encoding="utf-8"))


def check_raw_columns(con: duckdb.DuckDBPyConnection, data_dir: str | os.PathLike, contract: dict) -> None:
    """Compare each CSV header with the contract before 01_load.sql relies on the column names."""
    for table in TABLES:
        path = str(Path(data_dir).resolve() / f"{table}.csv")
        cols = {
            r[0]
            for r in con.execute(
                "DESCRIBE SELECT * FROM read_csv(?, header = true, all_varchar = true)", [path]
            ).fetchall()
        }
        missing = [c for c in contract["raw"][table] if c not in cols]
        if missing:
            raise ContractError(f"{table}.csv is missing column(s) {missing}")


def check_sql(check: dict) -> str:
    """Render sql/checks/<type>.sql for one contract check."""
    kind = ident(check["type"])
    path = SQL_DIR / "checks" / f"{kind}.sql"
    if not path.exists():
        raise ContractError(f"unknown check type {kind!r} in check {check['id']}")
    template = path.read_text(encoding="utf-8")
    params: dict[str, str] = {}
    if kind == "max_ratio":
        layer, table = check["of"].split(".")
        params = {
            "issue": ident(check["issue"]),
            "of_table": ("raw_" if layer == "raw" else "") + ident(table),
            "max": repr(float(check["max"])),
        }
    else:
        params["table"] = ident(check["table"])
        if "column" in check:
            params["column"] = ident(check["column"])
        if "values_from" in check:
            params["values"] = "cfg_" + ident(check["values_from"])
        if "to" in check:
            to_table, to_column = check["to"].split(".")
            params.update(to_table=ident(to_table), to_column=ident(to_column))
        for key in ("min", "max"):
            if key in check:
                params[key] = repr(float(check[key]))
    return template.format(**params)


def run_checks(con: duckdb.DuckDBPyConnection, contract: dict) -> list[dict]:
    results = []
    for check in contract["checks"]:
        failing, observed = con.execute(check_sql(check)).fetchone()
        failing = int(failing)
        status = "pass" if failing == 0 else ("fail" if check["severity"] == "error" else "warn")
        results.append(
            {
                "id": check["id"],
                "type": check["type"],
                "severity": check["severity"],
                "status": status,
                "failing_rows": failing,
                "observed": None if observed is None else float(observed),
            }
        )
    return results


def rows(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    cur = con.execute(sql)
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r, strict=True)) for r in cur.fetchall()]


def one(con: duckdb.DuckDBPyConnection, sql: str) -> dict:
    return rows(con, sql)[0]


def num(value):
    """DuckDB returns ints for counts and floats for ratios; keep that, but NaN/None become null."""
    if value is None:
        return None
    if isinstance(value, float):
        return None if value != value else value
    return int(value)


def counts(r: dict) -> dict:
    return {k: int(r[k]) for k in ("sessions", "view", "cart", "checkout", "purchase")}


def build_answers(con: duckdb.DuckDBPyConnection, checks: list[dict], contract: dict, export: dict) -> dict:
    fb = {r["device"]: r for r in rows(con, "SELECT * FROM funnel_by_device")}
    by_device = {
        d: {
            **counts(fb[d]),
            "revenue_paise": int(fb[d]["revenue_paise"]),
            "conversion": num(fb[d]["conversion"]),
            "step_rates": {s: num(fb[d][f"rate_{s}"]) for s in ("view", "cart", "checkout", "purchase")},
        }
        for d in ("all", *DEVICES)
    }
    funnel = {
        "steps": ["sessions", "view", "cart", "checkout", "purchase"],
        "by_device": by_device,
        "mobile_share_of_sessions": by_device["mobile"]["sessions"] / by_device["all"]["sessions"],
        "mobile_share_of_revenue": by_device["mobile"]["revenue_paise"] / by_device["all"]["revenue_paise"],
    }
    p = one(con, "SELECT * FROM payment_step_test")
    payment = {
        "metric": "purchase_given_checkout",
        "mobile": {"n": int(p["n1"]), "successes": int(p["x1"]), "rate": p["p1"]},
        "desktop": {"n": int(p["n2"]), "successes": int(p["x2"]), "rate": p["p2"]},
        "difference": p["difference"],
        "ci95": [p["ci_low"], p["ci_high"]],
        "z": p["z"],
        "p_value": p["p_value"],
    }
    grid = rows(con, "SELECT * FROM channel_device_grid")
    channels = [
        {"channel": ch, **{r["device"]: counts(r) for r in grid if r["channel"] == ch}}
        for ch in sorted({r["channel"] for r in grid})
    ]
    cmh = {
        r["step"]: {
            "statistic": r["statistic"],
            "p_value": r["p_value"],
            "odds_ratio_mh": r["odds_ratio_mh"],
            "ci95": [r["ci_low"], r["ci_high"]],
            "crude_odds_ratio": r["crude_odds_ratio"],
            "strata": int(r["strata"]),
        }
        for r in rows(con, "SELECT * FROM cmh")
    }
    simpson = one(con, "SELECT * FROM simpson")
    gaps = {r["channel"]: r["gap"] for r in rows(con, "SELECT * FROM simpson_gaps")}
    ov = {r["device"]: r for r in rows(con, "SELECT * FROM order_value_by_device")}
    w = one(con, "SELECT * FROM welch")
    weekly = [
        {
            "week": r["week"],
            "sessions": {d: int(r[f"sessions_{d}"]) for d in DEVICES},
            "purchases": {d: int(r[f"purchases_{d}"]) for d in DEVICES},
            "conversion": {
                d: (r[f"purchases_{d}"] / r[f"sessions_{d}"] if r[f"sessions_{d}"] else None) for d in DEVICES
            },
        }
        for r in rows(con, "SELECT * FROM weekly")
    ]
    opp = one(con, "SELECT * FROM opportunity")
    dec = one(con, "SELECT * FROM decision")
    issues = {r["issue"]: int(r["n"]) for r in rows(con, "SELECT issue, n FROM issues ORDER BY position")}
    raw_rows = {t: int(con.execute(f"SELECT count(*) FROM raw_{t}").fetchone()[0]) for t in TABLES}
    clean_rows = {t: int(con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]) for t in TABLES}
    a = contract["analysis"]
    return {
        "schema": "funnellens-answers",
        "schema_version": SCHEMA_VERSION,
        "generator": {"track": "sql", "version": __version__},
        "dataset": {
            "export": export["export"],
            "period_start": export["period_start"],
            "period_end": export["period_end"],
            "months": export["months"],
            "sample_rate": export["sample_rate"],
            "contract_version": contract["version"],
        },
        "data_quality": {"raw_rows": raw_rows, "clean_rows": clean_rows, "issues": issues, "checks": checks},
        "funnel": funnel,
        "payment_step_test": payment,
        "by_channel": {
            "channels": channels,
            "cmh": cmh,
            "simpson": {
                "step": "cart_given_view",
                "aggregate_gap": simpson["aggregate_gap"],
                "within_channel_gaps": gaps,
                "reversal": bool(simpson["reversal"]),
            },
        },
        "order_value": {
            **{
                d: {"orders": int(ov[d]["orders"]), "mean_inr": ov[d]["mean_inr"], "sd_inr": ov[d]["sd_inr"]}
                for d in ("mobile", "desktop")
            },
            "difference_inr": w["difference"],
            "welch_t": w["t"],
            "df": w["df"],
            "p_value": w["p_value"],
            "ci95": [w["ci_low"], w["ci_high"]],
        },
        "weekly": weekly,
        "opportunity": {
            "by_channel": rows(con, "SELECT channel, gap, extra_orders FROM opportunity_by_channel"),
            "extra_orders_in_sample": opp["extra_orders_in_sample"],
            "months": export["months"],
            "sample_rate": export["sample_rate"],
            "extra_orders_per_month": opp["extra_orders_per_month"],
            "mobile_aov_inr": opp["mobile_aov_inr"],
            "monthly_revenue_uplift_inr": opp["monthly_revenue_uplift_inr"],
            "mobile_monthly_revenue_inr": opp["mobile_monthly_revenue_inr"],
            "uplift_share_of_mobile_revenue": opp["monthly_revenue_uplift_inr"] / opp["mobile_monthly_revenue_inr"],
        },
        "decision": {
            "recommendation": dec["recommendation"],
            "reasons": list(dec["reasons"]),
            "thresholds": {"alpha": a["alpha"], "rebuild_min_monthly_uplift_inr": a["rebuild_min_monthly_uplift_inr"]},
        },
    }


def analyse(
    data_dir: str | os.PathLike,
    contract_file: str | os.PathLike | None = None,
    con: duckdb.DuckDBPyConnection | None = None,
) -> dict:
    contract = load_contract(contract_file)
    export = load_export(data_dir)
    con = con or connect()
    prepare(con, data_dir, contract, export)
    check_raw_columns(con, data_dir, contract)
    run_script(con, SCRIPTS[0])
    run_script(con, SCRIPTS[1])
    checks = run_checks(con, contract)
    failed = [c for c in checks if c["status"] == "fail"]
    if failed:
        raise ContractError(
            "data contract violated: " + ", ".join(f"{c['id']} ({c['failing_rows']} rows)" for c in failed)
        )
    for script in SCRIPTS[2:]:
        run_script(con, script)
    return build_answers(con, checks, contract, export)


def write_answers(answers: dict, out_dir: str | os.PathLike) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "answers.json"
    path.write_text(json.dumps(answers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
