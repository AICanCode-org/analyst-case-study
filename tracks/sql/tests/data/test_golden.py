"""Phase 4 data test: the full 2026-06 export must reproduce the golden answers that the Python,
SQL and R tracks agree on (contract/golden/answers-2026-06.json), and match the JSON Schema.
v1.1: that golden is the v1.0 file and stays frozen, so the comparison allows the additive v1.1 fields."""

import importlib.util
import json

import jsonschema
import pytest

from funnellens_sql.runner import analyse
from tests.conftest import CONTRACT, EXPORT_V10, REPO

spec = importlib.util.spec_from_file_location("parity", REPO / "scripts" / "parity.py")
parity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)


@pytest.fixture(scope="module")
def answers():
    return analyse(EXPORT_V10)


def test_matches_the_golden_answers(answers):
    golden = json.loads((CONTRACT / "golden" / "answers-2026-06.json").read_text(encoding="utf-8"))
    assert list(parity.diff(golden, json.loads(json.dumps(answers)), subset=True)) == []


def test_matches_the_json_schema(answers):
    schema = json.loads((CONTRACT / "answers.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(json.loads(json.dumps(answers)), schema)


def test_headline_findings(answers):
    """The story the numbers must tell (a regression here changes the recommendation)."""
    assert 0.65 < answers["funnel"]["mobile_share_of_sessions"] < 0.72
    pay = answers["by_channel"]["cmh"]["purchase_given_checkout"]
    assert pay["p_value"] < 0.001 and pay["ci95"][1] < 1  # mobile pays less, even within channels
    assert pay["odds_ratio_mh"] > answers["by_channel"]["cmh"]["purchase_given_checkout"]["crude_odds_ratio"]
    assert answers["order_value"]["p_value"] > 0.5  # basket size is not the problem
    assert answers["decision"]["recommendation"] == "run_targeted_experiment"
