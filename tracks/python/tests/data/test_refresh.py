"""Phase 7 (v1.1) data tests: the refreshed 2026-08 export, the incident it caused, and compatibility."""

import importlib.util
import json

import jsonschema
import pytest
import yaml

from funnellens.contract import ContractError
from funnellens.pipeline import analyse
from tests.conftest import CONTRACT, CONTRACT_V10, EXPORT_V10, EXPORT_V11, REPO

spec = importlib.util.spec_from_file_location("parity", REPO / "scripts" / "parity.py")
parity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)


def golden(name):
    return json.loads((CONTRACT / "golden" / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def answers():
    return analyse(EXPORT_V11)


def test_the_v1_0_contract_refuses_the_new_channel():
    """The incident: v1.0 stopped (exit 3) instead of silently dropping or mislabelling referral traffic."""
    with pytest.raises(ContractError, match=r"sessions.channel.accepted \(\d+ rows\)"):
        analyse(EXPORT_V11, CONTRACT_V10)


def test_matches_the_2026_08_golden_and_the_schema(answers):
    assert list(parity.diff(golden("answers-2026-08.json"), json.loads(json.dumps(answers)))) == []
    jsonschema.validate(json.loads(json.dumps(answers)), json.loads((CONTRACT / "answers.schema.json").read_text()))


def test_monitoring_flags_the_tracking_break_when_the_week_is_not_excluded(tmp_path):
    contract = yaml.safe_load((CONTRACT / "data-contract.yaml").read_text(encoding="utf-8"))
    contract["cleaning"]["exclude_weeks"] = []
    path = tmp_path / "contract.yaml"
    path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    a = analyse(EXPORT_V11, path)
    anomalies = a["monitoring"]["anomalies"]
    assert [(x["week"], x["metric"]) for x in anomalies] == [("2026-W31", "mobile_checkout_given_cart")]
    assert anomalies[0]["deviation"] < -0.5
    checks = {c["id"]: c["status"] for c in a["data_quality"]["checks"]}
    assert checks["orders.without_checkout.ratio"] == "warn"  # the second symptom: orders without a checkout


def test_with_the_week_excluded_the_data_is_clean(answers):
    m = answers["monitoring"]
    assert m["excluded_weeks"] == ["2026-W31"] and m["anomalies"] == []
    assert not m["freshness"]["stale"]
    assert "2026-W31" not in [w["week"] for w in answers["weekly"]]
    assert answers["data_quality"]["issues"]["sessions_excluded_week"] > 0
    assert {c["status"] for c in answers["data_quality"]["checks"]} == {"pass"}


def test_payment_methods_and_the_recommendation(answers):
    pm = answers["payment_methods"]["by_device"]
    assert set(pm["mobile"]) == {"card", "cod", "netbanking", "upi"}
    assert sum(pm["mobile"].values()) + sum(pm["desktop"].values()) == answers["data_quality"]["clean_rows"]["orders"]
    assert answers["decision"]["recommendation"] == "run_targeted_experiment"  # the refresh confirms v1.0


def test_backward_compatible_on_the_v1_0_export():
    """v1.1 on 2026-06 reproduces every v1.0 field of the v1.0 golden; the new fields are additive."""
    a = json.loads(json.dumps(analyse(EXPORT_V10)))
    assert list(parity.diff(golden("answers-2026-06.json"), a, subset=True)) == []
    assert a["payment_methods"] is None and a["schema_version"] == "1.1"
