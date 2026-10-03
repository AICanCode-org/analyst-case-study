"""Render the Streamlit app headlessly with streamlit.testing (no browser, no server)."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from funnellens_dashboard.narrator import Settings
from funnellens_dashboard.prepare import prepare
from tests.conftest import GOLDEN, GOLDEN_V11

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def static(tmp_path, monkeypatch):
    monkeypatch.setenv("STATIC_DIR", str(tmp_path))
    return tmp_path


def test_the_dashboard_renders_the_answers(static):
    prepare(GOLDEN, static, Settings())
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert at.title[0].value == "FunnelLens · mobile checkout decision"
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Mobile share of sessions"] == "69.2%"
    assert metrics["Monthly uplift if closed"] == "₹16.3 lakh"
    assert "run a targeted experiment" in at.subheader[0].value
    assert any("Summary (template)" in m.value for m in at.markdown)


def test_model_text_is_shown_literally(static):
    prepare(GOLDEN, static, Settings())
    narrative = static / "narrative.json"
    narrative.write_text(
        narrative.read_text(encoding="utf-8").replace('"text": "', '"text": "[click](http://x) '), encoding="utf-8"
    )
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert any("\\[click\\]\\(http://x\\)" in m.value for m in at.markdown)


def test_without_answers_it_explains_what_to_do(static):
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert "Run a track pipeline" in at.error[0].value


def test_v1_1_answers_add_the_monitoring_tab(static):
    prepare(GOLDEN_V11, static, Settings())
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert [t.label for t in at.tabs][-1] == "Monitoring"
    assert any("excluded weeks: 2026-W31" in m.value for m in at.markdown)
    assert any("No full week deviates" in s.value for s in at.success)


def test_v1_0_answers_have_no_monitoring_tab(static):
    prepare(GOLDEN, static, Settings())
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert "Monitoring" not in [t.label for t in at.tabs]


def test_anomalies_are_shown_as_a_warning(static):
    a = json.loads(GOLDEN_V11.read_text(encoding="utf-8"))
    a["monitoring"]["anomalies"] = [
        {"week": "2026-W31", "metric": "mobile_checkout_given_cart", "value": 0.1, "median": 0.5, "deviation": -0.8}
    ]
    path = static / "in.json"
    path.write_text(json.dumps(a), encoding="utf-8")
    prepare(path, static, Settings())
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert "1 anomalous week(s)" in at.warning[0].value
