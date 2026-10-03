import pytest

from funnellens.contract import ContractError, load_export
from funnellens.load import load_raw
from tests.conftest import EXPECTED, TINY


def test_reads_every_table_as_text_and_keeps_empty_cells(contract):
    raw = load_raw(TINY, contract)
    assert {t: len(df) for t, df in raw.items()} == EXPECTED["raw_rows"]
    assert all(isinstance(v, str) for v in raw["orders"].iloc[0])
    assert raw["users"].loc[1, "signup_channel"] == ""  # empty, not NaN
    assert raw["users"].loc[1, "city"] == " pune "  # whitespace kept for clean.py to decide
    assert raw["orders"].loc[0, "amount"] == "₹1,299.00"  # text, not a guessed float


def test_missing_column_is_a_contract_error(contract, export_copy):
    data = export_copy()
    path = data / "orders.csv"
    path.write_text(path.read_text(encoding="utf-8").replace("amount", "amt", 1), encoding="utf-8")
    with pytest.raises(ContractError, match=r"orders.csv is missing column\(s\) \['amount'\]"):
        load_raw(data, contract)


def test_extra_columns_are_allowed(contract, export_copy):
    data = export_copy()
    path = data / "orders.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    lines = [lines[0] + ",payment_method"] + [line + ",upi" for line in lines[1:]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert "payment_method" in load_raw(data, contract)["orders"].columns


def test_missing_file_is_a_contract_error(contract, export_copy):
    data = export_copy()
    (data / "events.csv").unlink()
    with pytest.raises(ContractError, match="missing file"):
        load_raw(data, contract)


def test_export_manifest(tmp_path):
    e = load_export(TINY)
    assert (e.name, str(e.period_start), str(e.period_end), e.sample_rate, e.months) == (
        "2026-03",
        "2026-03-01",
        "2026-03-31",
        1.0,
        1,
    )
    with pytest.raises(ContractError, match=r"export\.json not found"):
        load_export(tmp_path)
