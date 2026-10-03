import pandas as pd
import pytest

from funnellens.checks import raise_on_errors, run_checks
from funnellens.contract import ContractError
from tests.conftest import EXPECTED


def statuses(results):
    return {r["id"]: [r["status"], r["failing_rows"]] for r in results}


def test_every_contract_check_on_the_tiny_export(tiny, contract):
    clean, export = tiny
    results = run_checks(clean, export, contract)
    assert [r["id"] for r in results] == [c["id"] for c in contract["checks"]]  # contract order
    assert statuses(results) == EXPECTED["checks"]


def test_ratio_checks_report_the_observed_ratio(tiny, contract):
    clean, export = tiny
    by_id = {r["id"]: r for r in run_checks(clean, export, contract)}
    assert by_id["sessions.unknown_channel.ratio"]["observed"] == pytest.approx(2 / 8)
    assert by_id["sessions.duplicate_rows.ratio"]["observed"] == pytest.approx(1 / 14)
    assert by_id["users.user_id.unique"]["observed"] is None


def test_a_new_channel_value_fails_the_accepted_values_check(tiny, contract):
    clean, export = tiny
    clean.sessions.loc[0, "channel"] = "affiliate"
    assert statuses(run_checks(clean, export, contract))["sessions.channel.accepted"] == ["fail", 1]


def test_duplicate_keys_and_broken_relationships_fail(tiny, contract):
    clean, export = tiny
    clean.orders = pd.concat([clean.orders, clean.orders.iloc[[0]]], ignore_index=True)
    clean.events.loc[0, "session_id"] = "S404"
    s = statuses(run_checks(clean, export, contract))
    assert s["orders.order_id.unique"] == ["fail", 2]  # both rows of the duplicated id
    assert s["events.session_id.relationship"] == ["fail", 1]


def test_out_of_range_amounts_and_dates_fail(tiny, contract):
    clean, export = tiny
    clean.orders.loc[0, "amount_paise"] = 50
    clean.sessions.loc[0, "started_at"] = pd.Timestamp("2026-04-01 00:00:00")
    s = statuses(run_checks(clean, export, contract))
    assert s["orders.amount_paise.range"] == ["fail", 1]
    assert s["sessions.started_at.in_period"] == ["fail", 1]


def test_not_null_check(tiny, contract):
    clean, export = tiny
    check = {
        "id": "users.signup_channel.not_null",
        "type": "not_null",
        "table": "users",
        "column": "signup_channel",
        "severity": "warn",
    }
    result = run_checks(clean, export, {**contract, "checks": [check]})
    assert statuses(result) == {"users.signup_channel.not_null": ["warn", 1]}


def test_unknown_check_type_is_a_contract_error(tiny, contract):
    clean, export = tiny
    with pytest.raises(ContractError, match="unknown check type"):
        run_checks(
            clean,
            export,
            {
                **contract,
                "checks": [{"id": "x", "type": "regex", "table": "users", "column": "city", "severity": "warn"}],
            },
        )


def test_only_failed_error_checks_stop_the_pipeline(tiny, contract):
    clean, export = tiny
    results = run_checks(clean, export, contract)
    with pytest.raises(ContractError, match=r"sessions.row_count \(1 rows\)"):
        raise_on_errors(results)
    raise_on_errors([r for r in results if r["id"] != "sessions.row_count"])  # warnings alone are fine
