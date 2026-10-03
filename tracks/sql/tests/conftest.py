import json
import shutil
from pathlib import Path

import pytest

from funnellens_sql import runner

# ---------------------------------------------------------------------------
# PENDING tests describe behaviour you have not built yet, so they are skipped
# (reported as "s" by pytest). When you start a milestone, delete its line here,
# watch the tests fail (red), implement until they pass (green). See docs/phase-3.
# ---------------------------------------------------------------------------
PENDING: dict[str, str] = {
    "test_golden.py": "Phase 4 - golden answers on the real export",
    "test_invariants.py": "Phase 4 - invariants on the real export",
    "test_contract_violations.py": "Phase 4 - contract violations stop the run",
}


def pytest_collection_modifyitems(config, items):
    for item in items:
        reason = PENDING.get(item.path.name)
        if reason:
            item.add_marker(pytest.mark.skip(reason=f"PENDING ({reason}) - see tests/conftest.py"))


REPO = Path(__file__).resolve().parents[3]
CONTRACT = REPO / "contract"
TINY = CONTRACT / "fixtures" / "tiny"
EXPORT_V10 = REPO / "data" / "raw" / "2026-06"
EXPECTED = json.loads((CONTRACT / "fixtures" / "tiny-expected.json").read_text(encoding="utf-8"))
STATS_CASES = json.loads((CONTRACT / "fixtures" / "stats-cases.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def contract():
    return runner.load_contract()


def prepared(data_dir, contract, upto="02_clean.sql"):
    """A DuckDB connection with the export loaded and the scripts up to `upto` run."""
    con = runner.connect()
    runner.prepare(con, data_dir, contract, runner.load_export(data_dir))
    for script in runner.SCRIPTS[: runner.SCRIPTS.index(upto) + 1]:
        runner.run_script(con, script)
    return con


@pytest.fixture
def tiny(contract):
    """The hand-made 14-session export, cleaned (see contract/fixtures/tiny-expected.json)."""
    return prepared(TINY, contract)


@pytest.fixture
def tiny_metrics(contract):
    return prepared(TINY, contract, "03_metrics.sql")


@pytest.fixture
def export_copy(tmp_path):
    """A writable copy of an export folder, to corrupt on purpose."""

    def make(source: Path = TINY) -> Path:
        target = tmp_path / source.name
        shutil.copytree(source, target)
        return target

    return make
