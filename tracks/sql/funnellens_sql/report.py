"""`report`: the SQL track's report. Runs the pipeline, then prints the result views as Markdown
tables (out/report.md) so a reviewer can read every number next to the query that produced it."""

from __future__ import annotations

import os
from pathlib import Path

from .runner import analyse, connect, write_answers

SECTIONS = [
    ("Q1 · Data quality: rows removed per rule", "SELECT issue, n FROM issues ORDER BY position"),
    (
        "Q2 · Funnel by device",
        "SELECT device, sessions, view, cart, checkout, purchase, round(conversion, 4) AS conversion "
        "FROM funnel_by_device",
    ),
    (
        "Q3 · Payment step, mobile vs desktop",
        "SELECT round(p1, 4) AS mobile, round(p2, 4) AS desktop, "
        "round(difference, 4) AS difference, round(z, 2) AS z, p_value FROM payment_step_test",
    ),
    (
        "Q4 · Within channels (Cochran-Mantel-Haenszel)",
        "SELECT step, round(odds_ratio_mh, 3) AS odds_ratio_mh, "
        "round(ci_low, 3) AS ci_low, round(ci_high, 3) AS ci_high, p_value, "
        "round(crude_odds_ratio, 3) AS crude FROM cmh",
    ),
    (
        "Q5 · Order value (Welch)",
        "SELECT round(difference, 2) AS difference_inr, round(t, 3) AS t, round(df, 1) AS df, "
        "round(p_value, 4) AS p_value FROM welch",
    ),
    (
        "Q6 · Weekly conversion",
        "SELECT week, sessions_desktop, sessions_mobile, purchases_desktop, purchases_mobile FROM weekly",
    ),
    (
        "Q7 · Opportunity",
        "SELECT round(extra_orders_per_month, 1) AS extra_orders_per_month, "
        "round(monthly_revenue_uplift_inr) AS monthly_uplift_inr FROM opportunity",
    ),
    ("Q8 · Decision", "SELECT recommendation, array_to_string(reasons, ', ') AS reasons FROM decision"),
]


def markdown(con, sql: str) -> str:
    cur = con.execute(sql)
    names = [d[0] for d in cur.description]
    lines = ["| " + " | ".join(names) + " |", "|" + "---|" * len(names)]
    lines += ["| " + " | ".join("" if v is None else str(v) for v in row) + " |" for row in cur.fetchall()]
    return "\n".join(lines)


def build_report(data_dir: str | os.PathLike, out_dir: str | os.PathLike, contract=None) -> Path:
    con = connect()
    answers = analyse(data_dir, contract, con)
    write_answers(answers, out_dir)
    parts = [f"# FunnelLens · SQL track report · export {answers['dataset']['export']}", ""]
    for title, sql in SECTIONS:
        parts += [f"## {title}", "", "```sql", sql, "```", "", markdown(con, sql), ""]
    path = Path(out_dir) / "report.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path
