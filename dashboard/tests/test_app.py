"""Render the Streamlit app headlessly with streamlit.testing (no browser, no server)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from funnellens_dashboard.narrator import Settings
from funnellens_dashboard.prepare import prepare
from tests.conftest import GOLDEN

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
