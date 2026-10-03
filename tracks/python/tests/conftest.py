import json
import shutil
from pathlib import Path

import pytest

from funnellens.clean import clean
from funnellens.contract import load_contract, load_export
from funnellens.load import load_raw

# ---------------------------------------------------------------------------
# PENDING tests describe behaviour you have not built yet, so they are skipped
# (reported as "s" by pytest). When you start a milestone, delete its line here,
# watch the tests fail (red), implement until they pass (green). See docs/phase-3.
# ---------------------------------------------------------------------------
PENDING: dict[str, str] = {
    "test_load.py": "Phase 3 M1 - load the raw export as text",
    "test_clean.py": "Phase 3 M1 - cleaning rules and the issue counts",
    "test_checks.py": "Phase 3 M2 - data-contract checks",
    "test_metrics.py": "Phase 3 M3 - funnel by device, channel and week",
    "test_stats.py": "Phase 3 M4 - two-proportion z, CMH and Welch tests",
    "test_answers.py": "Phase 3 M5 - answers.json and the decision",
    "test_cli.py": "Phase 3 M5 - command line and exit codes",
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
Z = 1.959963984540054


@pytest.fixture(scope="session")
def contract():
    return load_contract()


@pytest.fixture
def tiny(contract):
    """The hand-made 14-session export, cleaned (see contract/fixtures/tiny-expected.json)."""
    export = load_export(TINY)
    return clean(load_raw(TINY, contract), export, contract), export


@pytest.fixture
def export_copy(tmp_path):
    """A writable copy of an export folder, to corrupt on purpose."""

    def make(source: Path = TINY) -> Path:
        target = tmp_path / source.name
        shutil.copytree(source, target)
        return target

    return make
