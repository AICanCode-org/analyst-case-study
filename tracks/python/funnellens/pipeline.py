"""The whole run: load -> clean -> checks (stop on error) -> answers.json."""

from __future__ import annotations

import json
from pathlib import Path

from .answers import build_answers
from .checks import raise_on_errors, run_checks
from .clean import clean
from .contract import load_contract, load_export
from .load import load_raw


def analyse(data_dir: str | Path, contract_file: str | Path | None = None) -> dict:
    contract = load_contract(contract_file)
    export = load_export(data_dir)
    tables = clean(load_raw(data_dir, contract), export, contract)
    checks = run_checks(tables, export, contract)
    raise_on_errors(checks)
    return build_answers(tables, checks, export, contract)


def write_answers(answers: dict, out_dir: str | Path) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "answers.json"
    path.write_text(json.dumps(answers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
