"""v1.1 · sql/06_monitoring.sql and sql/07_payment_methods.sql on the tiny export."""

from datetime import date

import pytest

from funnellens_sql import runner
from tests.conftest import TINY, prepared


def view(con, name):
    cur = con.execute(f"SELECT * FROM {name}")
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r, strict=True)) for r in cur.fetchall()]


def test_freshness_and_full_weeks_only(tiny_monitoring):
    assert view(tiny_monitoring, "freshness") == [
        {"period_end": date(2026, 3, 31), "last_session_date": date(2026, 3, 11), "days_behind": 20, "stale": True}
    ]
    assert [w["week"] for w in view(tiny_monitoring, "monitoring_weeks")] == ["2026-W10", "2026-W11"]


def test_weekly_values_and_medians(tiny_monitoring):
    assert view(tiny_monitoring, "monitoring_weeks") == [
        {"week": "2026-W10", "sessions": 5, "mobile_checkout_given_cart": 0.5},  # S1 checks out, S2 does not
        {"week": "2026-W11", "sessions": 3, "mobile_checkout_given_cart": 1.0},  # S6 (S12 never carts)
    ]
    assert view(tiny_monitoring, "monitoring_medians") == [{"sessions": 4.0, "mobile_checkout_given_cart": 0.75}]


def test_anomalies_beyond_the_threshold(tiny_monitoring):
    got = view(tiny_monitoring, "monitoring_anomalies")
    assert [(a["week"], a["metric"], a["value"], a["median"]) for a in got] == [
        ("2026-W10", "mobile_checkout_given_cart", 0.5, 0.75),
        ("2026-W11", "mobile_checkout_given_cart", 1.0, 0.75),
    ]  # sessions deviate by 25 %: not flagged
    assert [a["deviation"] for a in got] == [pytest.approx(-1 / 3), pytest.approx(1 / 3)]
    tiny_monitoring.execute("SET VARIABLE max_relative_deviation = 1.0")
    assert view(tiny_monitoring, "monitoring_anomalies") == []  # |deviation| must EXCEED it


def test_excluded_weeks_are_dropped_and_counted(contract):
    c = {**contract, "cleaning": {**contract["cleaning"], "exclude_weeks": ["2026-W11"]}}
    con = prepared(TINY, c)
    issues = con.execute("SELECT issue, n FROM issues ORDER BY position").fetchall()
    assert issues[-1] == ("sessions_excluded_week", 3)
    assert con.execute("SELECT DISTINCT week FROM sessions").fetchall() == [("2026-W10",)]


def test_payment_methods_only_when_the_column_exists(contract, export_copy):
    data = export_copy()
    path = data / "orders.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    methods = ["UPI ", "card", "", "upi", "Card", "cod", "upi", "upi", "card", "upi"]
    lines = [lines[0] + ",payment_method"] + [f"{line},{m}" for line, m in zip(lines[1:], methods, strict=True)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    con = prepared(data, contract, "06_monitoring.sql")
    runner.run_script(con, runner.PAYMENT_METHODS)
    rows = view(con, "payment_methods")
    assert {r["device"] for r in rows} == {"desktop", "mobile"}
    total = {}
    for r in rows:
        total[r["method"]] = total.get(r["method"], 0) + r["orders"]
    n = con.execute("SELECT count(*) FROM orders").fetchone()[0]
    assert sum(total.values()) == n and set(total) <= {"card", "cod", "unknown", "upi"}


def test_a_week_without_mobile_carts_has_a_null_rate(tiny_monitoring):
    tiny_monitoring.execute("DELETE FROM session_funnel WHERE device = 'mobile'")
    assert [w["mobile_checkout_given_cart"] for w in view(tiny_monitoring, "monitoring_weeks")] == [None, None]
    assert view(tiny_monitoring, "monitoring_medians")[0]["mobile_checkout_given_cart"] is None
    assert [a["metric"] for a in view(tiny_monitoring, "monitoring_anomalies")] == ["sessions", "sessions"]
