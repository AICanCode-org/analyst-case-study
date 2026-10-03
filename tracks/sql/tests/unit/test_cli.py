import json

import pytest

from funnellens_sql.__main__ import main
from tests.conftest import EXPORT_V10, TINY


def test_run_writes_answers_json(tmp_path, capsys):
    assert main(["run", "--data", str(EXPORT_V10), "--out", str(tmp_path)]) == 0
    answers = json.loads((tmp_path / "answers.json").read_text(encoding="utf-8"))
    assert answers["schema"] == "funnellens-answers"
    assert answers["generator"]["track"] == "sql"
    assert answers["decision"]["recommendation"] == "run_targeted_experiment"
    assert "recommendation run_targeted_experiment" in capsys.readouterr().out


def test_a_contract_violation_exits_3_and_writes_nothing(tmp_path, capsys):
    assert main(["run", "--data", str(TINY), "--out", str(tmp_path)]) == 3  # 8 sessions < row_count min
    assert "sessions.row_count" in capsys.readouterr().err
    assert not (tmp_path / "answers.json").exists()


def test_a_folder_without_export_json_exits_3(tmp_path):
    assert main(["run", "--data", str(tmp_path), "--out", str(tmp_path / "out")]) == 3


def test_unreadable_output_exits_2(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("not a folder")
    assert main(["run", "--data", str(EXPORT_V10), "--out", str(blocker)]) == 2


def test_usage_error():
    with pytest.raises(SystemExit) as exc:
        main(["run"])
    assert exc.value.code == 2


def test_report_writes_markdown_tables(tmp_path):
    assert main(["report", "--data", str(EXPORT_V10), "--out", str(tmp_path)]) == 0
    text = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "## Q8 · Decision" in text and "run_targeted_experiment" in text
    assert (tmp_path / "answers.json").exists()
