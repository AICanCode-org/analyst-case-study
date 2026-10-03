import json

import pytest

from funnellens_dashboard.__main__ import main
from funnellens_dashboard.narrator import Settings
from funnellens_dashboard.prepare import AnswersError, load_answers, prepare
from tests.conftest import GOLDEN


def test_prepare_writes_the_static_files(tmp_path):
    narrative = prepare(GOLDEN, tmp_path, Settings())
    assert sorted(p.name for p in tmp_path.iterdir()) == ["answers.json", "narrative.json", "onepager.md"]
    assert json.loads((tmp_path / "narrative.json").read_text(encoding="utf-8")) == narrative
    memo = (tmp_path / "onepager.md").read_text(encoding="utf-8")
    assert "## Recommendation: run a targeted experiment on the mobile payment step" in memo
    assert "_Summary source: template._" in memo and "- [F9] Recommendation" in memo


def test_answers_from_any_track_are_accepted(tmp_path, answers):
    for track in ("python", "sql", "r"):
        answers["generator"]["track"] = track
        path = tmp_path / f"{track}.json"
        path.write_text(json.dumps(answers), encoding="utf-8")
        assert load_answers(path)["generator"]["track"] == track


@pytest.mark.parametrize(
    ("content", "message"),
    [(None, "not found"), ("{nope", "is not JSON"), ('{"schema": "funnellens-answers"}', "does not match")],
)
def test_bad_answers_are_refused(tmp_path, content, message):
    path = tmp_path / "answers.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    with pytest.raises(AnswersError, match=message):
        load_answers(path)


def test_cli(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "offline")
    assert main(["prepare", "--answers", str(GOLDEN), "--out", str(tmp_path / "static")]) == 0
    assert "narrative source template (ok)" in capsys.readouterr().out
    assert main(["prepare", "--answers", str(tmp_path / "missing.json"), "--out", str(tmp_path)]) == 3
    blocker = tmp_path / "file"
    blocker.write_text("x")
    assert main(["prepare", "--answers", str(GOLDEN), "--out", str(blocker)]) == 2


def test_cli_with_an_unreachable_provider_still_succeeds(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "llm")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-should-never-appear")
    monkeypatch.setenv("LLM_TIMEOUT_MS", "500")
    assert main(["prepare", "--answers", str(GOLDEN), "--out", str(tmp_path)]) == 0
    out = capsys.readouterr()
    assert "fallback: provider unreachable" in out.out
    assert "sk-should-never-appear" not in out.out + out.err
    assert "sk-should-never-appear" not in "".join(p.read_text(encoding="utf-8") for p in tmp_path.iterdir())
