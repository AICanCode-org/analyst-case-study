"""v1.1 · monitoring and payment methods (contract/questions.md §6) on the tiny export."""

import pandas as pd
import pytest

from funnellens.metrics import session_funnel
from funnellens.monitoring import monitoring, payment_methods


def test_freshness_and_full_weeks_only(tiny, contract):
    clean, export = tiny
    m = monitoring(session_funnel(clean), clean, export, contract)
    assert m["freshness"] == {
        "period_end": "2026-03-31",
        "last_session_date": "2026-03-11",
        "days_behind": 20,
        "stale": True,
    }
    assert [w["week"] for w in m["weeks"]] == ["2026-W10", "2026-W11"]  # 1 March (Sunday) is not a full week
    assert m["excluded_weeks"] == ["2026-W31"]
    assert m["max_relative_deviation"] == 0.30


def test_weekly_values_and_medians(tiny, contract):
    clean, export = tiny
    m = monitoring(session_funnel(clean), clean, export, contract)
    assert m["weeks"] == [
        {"week": "2026-W10", "sessions": 5, "mobile_checkout_given_cart": 0.5},  # S1 checks out, S2 does not
        {"week": "2026-W11", "sessions": 3, "mobile_checkout_given_cart": 1.0},  # S6 (S12 never carts)
    ]
    assert m["medians"] == {"sessions": 4.0, "mobile_checkout_given_cart": 0.75}  # even count: mean of the middle two


def test_anomalies_beyond_the_threshold(tiny, contract):
    clean, export = tiny
    m = monitoring(session_funnel(clean), clean, export, contract)
    assert m["anomalies"] == [
        {
            "week": "2026-W10",
            "metric": "mobile_checkout_given_cart",
            "value": 0.5,
            "median": 0.75,
            "deviation": pytest.approx(-1 / 3),
        },
        {
            "week": "2026-W11",
            "metric": "mobile_checkout_given_cart",
            "value": 1.0,
            "median": 0.75,
            "deviation": pytest.approx(1 / 3),
        },
    ]  # sessions deviate by 25 %: not flagged
    loose = {**contract, "monitoring": {**contract["monitoring"], "max_relative_deviation": 1.0}}
    assert monitoring(session_funnel(clean), clean, export, loose)["anomalies"] == []  # |deviation| must EXCEED it


def test_excluded_weeks_are_dropped_and_counted(tiny, contract):
    from funnellens.clean import clean as clean_tables
    from funnellens.load import load_raw
    from tests.conftest import TINY

    _, export = tiny
    c = {**contract, "cleaning": {**contract["cleaning"], "exclude_weeks": ["2026-W11"]}}
    cleaned = clean_tables(load_raw(TINY, c), export, c)
    assert cleaned.issues["sessions_excluded_week"] == 3
    assert list(cleaned.issues)[-1] == "sessions_excluded_week"
    assert set(cleaned.sessions["week"]) == {"2026-W10"}


def test_payment_methods_only_when_the_column_exists(tiny):
    clean, _ = tiny
    assert payment_methods(clean) is None
    methods = ["UPI ", "card", "", "upi", "Card"]
    clean.orders = clean.orders.assign(payment_method=pd.Series(methods, index=clean.orders.index))
    got = payment_methods(clean)
    assert set(got["by_device"]) == {"desktop", "mobile"}
    total = {}
    for d in got["by_device"].values():
        for k, v in d.items():
            total[k] = total.get(k, 0) + v
        assert list(d) == sorted(d)
    assert total == {"card": 2, "unknown": 1, "upi": 2}


def test_a_week_without_mobile_carts_has_a_null_rate(tiny, contract):
    clean, export = tiny
    clean.sessions = clean.sessions[clean.sessions["device"] == "desktop"]
    m = monitoring(session_funnel(clean), clean, export, contract)
    assert [w["mobile_checkout_given_cart"] for w in m["weeks"]] == [None, None]
    assert m["medians"]["mobile_checkout_given_cart"] is None
    assert [a["metric"] for a in m["anomalies"]] == ["sessions", "sessions"]  # 3 vs 1 around a median of 2
