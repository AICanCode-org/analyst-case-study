import pytest

from funnellens_sql import runner
from funnellens_sql.runner import ContractError, check_raw_columns, load_export
from tests.conftest import EXPECTED, TINY, prepared


def test_reads_every_table_as_text_and_keeps_empty_cells(contract):
    con = prepared(TINY, contract, "01_load.sql")
    got = {t: con.execute(f"SELECT count(*) FROM raw_{t}").fetchone()[0] for t in EXPECTED["raw_rows"]}
    assert got == EXPECTED["raw_rows"]
    types = {r[1] for r in con.execute("DESCRIBE raw_orders").fetchall()}
    assert types == {"VARCHAR"}  # no guessed types: cleaning decides
    assert con.execute("SELECT signup_channel, city FROM raw_users WHERE user_id = '2'").fetchone() == ("", " pune ")
    assert con.execute("SELECT amount FROM raw_orders WHERE order_id = 'O1'").fetchone()[0] == "₹1,299.00"


def test_missing_column_is_a_contract_error(contract, export_copy):
    data = export_copy()
    path = data / "orders.csv"
    path.write_text(path.read_text(encoding="utf-8").replace("amount", "amt", 1), encoding="utf-8")
    with pytest.raises(ContractError, match=r"orders.csv is missing column\(s\) \['amount'\]"):
        check_raw_columns(runner.connect(), data, contract)


def test_extra_columns_are_allowed(contract, export_copy):
    data = export_copy()
    path = data / "orders.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    lines = [lines[0] + ",payment_method"] + [line + ",upi" for line in lines[1:]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    check_raw_columns(runner.connect(), data, contract)
    con = prepared(data, contract, "01_load.sql")
    assert "payment_method" in {r[0] for r in con.execute("DESCRIBE raw_orders").fetchall()}


def test_missing_file_is_a_contract_error(contract, export_copy):
    data = export_copy()
    (data / "events.csv").unlink()
    with pytest.raises(ContractError, match="missing file"):
        prepared(data, contract, "01_load.sql")


def test_export_manifest(tmp_path):
    e = load_export(TINY)
    assert (e["export"], e["period_start"], e["period_end"], e["sample_rate"], e["months"]) == (
        "2026-03",
        "2026-03-01",
        "2026-03-31",
        1.0,
        1,
    )
    with pytest.raises(ContractError, match=r"export\.json not found"):
        load_export(tmp_path)
