"""Phase 4 data tests: properties that must hold for ANY export, whatever the numbers are."""

import pytest

from funnellens_sql.runner import analyse
from tests.conftest import EXPORT_V10


@pytest.fixture(scope="module")
def a():
    return analyse(EXPORT_V10)


def test_funnel_never_grows(a):
    for device, f in a["funnel"]["by_device"].items():
        counts = [f[s] for s in a["funnel"]["steps"]]
        assert counts == sorted(counts, reverse=True), device


def test_devices_add_up_to_all(a):
    by = a["funnel"]["by_device"]
    for key in ("sessions", "view", "cart", "checkout", "purchase", "revenue_paise"):
        assert by["desktop"][key] + by["mobile"][key] == by["all"][key], key


def test_channels_and_weeks_add_up_to_devices(a):
    by = a["funnel"]["by_device"]
    for device in ("desktop", "mobile"):
        for key in ("sessions", "view", "cart", "checkout", "purchase"):
            assert sum(c[device][key] for c in a["by_channel"]["channels"]) == by[device][key]
        assert sum(w["sessions"][device] for w in a["weekly"]) == by[device]["sessions"]
        assert sum(w["purchases"][device] for w in a["weekly"]) == by[device]["purchase"]


def test_rows_removed_plus_rows_kept_equals_rows_read(a):
    dq = a["data_quality"]
    i, raw, clean = dq["issues"], dq["raw_rows"], dq["clean_rows"]
    assert (
        raw["orders"]
        - i["orders_exact_duplicates"]
        - i["orders_unparseable_amount"]
        - i["orders_non_positive_amount"]
        - i["orders_orphan_session"]
        == clean["orders"]
    )
    assert (
        raw["events"] - i["events_unknown_name"] - i["events_orphan_session"] - i["events_repeated_steps"]
        == clean["events"]
    )
    assert raw["users"] == clean["users"]
    removed = (
        i["sessions_bad_timestamp"]
        + i["sessions_exact_duplicates"]
        + i["sessions_out_of_period"]
        + i["sessions_orphan_user"]
    )
    assert raw["sessions"] - removed - clean["sessions"] >= 2 * i["sessions_conflicting_ids"]


def test_no_error_check_fails(a):
    assert {c["status"] for c in a["data_quality"]["checks"] if c["severity"] == "error"} == {"pass"}


def test_statistics_are_well_formed(a):
    tests = [a["payment_step_test"], a["order_value"], *a["by_channel"]["cmh"].values()]
    for t in tests:
        assert 0 <= t["p_value"] <= 1
        assert t["ci95"][0] < t["ci95"][1]
    pay = a["payment_step_test"]
    assert pay["ci95"][0] < pay["difference"] < pay["ci95"][1]
    for t in a["by_channel"]["cmh"].values():
        assert t["ci95"][0] < t["odds_ratio_mh"] < t["ci95"][1]
