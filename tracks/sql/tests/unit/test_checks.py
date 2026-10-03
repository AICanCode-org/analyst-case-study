import pytest

from funnellens_sql.runner import ContractError, analyse, check_sql, run_checks
from tests.conftest import EXPECTED, TINY


def statuses(results):
    return {r["id"]: [r["status"], r["failing_rows"]] for r in results}


def test_every_contract_check_on_the_tiny_export(tiny, contract):
    results = run_checks(tiny, contract)
    assert [r["id"] for r in results] == [c["id"] for c in contract["checks"]]  # contract order
    assert statuses(results) == EXPECTED["checks"]


def test_ratio_checks_report_the_observed_ratio(tiny, contract):
    by_id = {r["id"]: r for r in run_checks(tiny, contract)}
    assert by_id["sessions.unknown_channel.ratio"]["observed"] == pytest.approx(2 / 8)
    assert by_id["sessions.duplicate_rows.ratio"]["observed"] == pytest.approx(1 / 14)
    assert by_id["users.user_id.unique"]["observed"] is None


def test_a_new_channel_value_fails_the_accepted_values_check(tiny, contract):
    tiny.execute("UPDATE sessions SET channel = 'referral' WHERE session_id = 'S1'")
    assert statuses(run_checks(tiny, contract))["sessions.channel.accepted"] == ["fail", 1]


def test_duplicate_keys_and_broken_relationships_fail(tiny, contract):
    tiny.execute("INSERT INTO orders SELECT * FROM orders WHERE order_id = 'O1'")
    tiny.execute("UPDATE events SET session_id = 'S404' WHERE session_id = 'S1' AND event_name = 'view'")
    s = statuses(run_checks(tiny, contract))
    assert s["orders.order_id.unique"] == ["fail", 2]  # both rows of the duplicated id
    assert s["events.session_id.relationship"] == ["fail", 1]


def test_out_of_range_amounts_and_dates_fail(tiny, contract):
    tiny.execute("UPDATE orders SET amount_paise = 50 WHERE order_id = 'O1'")
    tiny.execute("UPDATE sessions SET started_at = TIMESTAMP '2026-04-01 00:00:00' WHERE session_id = 'S1'")
    s = statuses(run_checks(tiny, contract))
    assert s["orders.amount_paise.range"] == ["fail", 1]
    assert s["sessions.started_at.in_period"] == ["fail", 1]


def test_not_null_check(tiny, contract):
    check = {
        "id": "users.signup_channel.not_null",
        "type": "not_null",
        "table": "users",
        "column": "signup_channel",
        "severity": "warn",
    }
    result = run_checks(tiny, {**contract, "checks": [check]})
    assert statuses(result) == {"users.signup_channel.not_null": ["warn", 1]}


def test_unknown_check_type_is_a_contract_error(tiny, contract):
    with pytest.raises(ContractError, match="unknown check type"):
        run_checks(
            tiny,
            {
                **contract,
                "checks": [{"id": "x", "type": "regex", "table": "users", "column": "city", "severity": "warn"}],
            },
        )


def test_contract_values_cannot_inject_sql():
    bad = {"id": "x", "type": "not_null", "table": "users; DROP TABLE users", "column": "city", "severity": "warn"}
    with pytest.raises(ContractError, match="not a plain identifier"):
        check_sql(bad)


def test_only_failed_error_checks_stop_the_pipeline():
    with pytest.raises(ContractError, match=r"sessions.row_count \(1 rows\)"):
        analyse(TINY)
