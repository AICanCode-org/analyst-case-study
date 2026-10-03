"""Phase 4 data tests: broken exports must be refused (exit code 3), never silently analysed."""

import pytest

from funnellens_sql.runner import ContractError, analyse
from tests.conftest import EXPORT_V10


def append_line(path, line):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def test_a_new_channel_value_stops_the_run(export_copy):
    data = export_copy(EXPORT_V10)
    append_line(data / "sessions.csv", "S999999,1,mobile,affiliate,2026-06-30 10:00:00")
    with pytest.raises(ContractError, match=r"sessions.channel.accepted \(1 rows\)"):
        analyse(data)


def test_a_reused_order_id_stops_the_run(export_copy):
    data = export_copy(EXPORT_V10)
    first = (data / "orders.csv").read_text(encoding="utf-8").splitlines()[1].split(",")[0]
    append_line(data / "orders.csv", f"{first},S000002,999")
    with pytest.raises(ContractError, match=r"orders.order_id.unique"):
        analyse(data)


def test_an_absurd_amount_stops_the_run(export_copy):
    data = export_copy(EXPORT_V10)
    append_line(data / "orders.csv", 'O999999,S000002,"₹1,50,00,000.00"')
    with pytest.raises(ContractError, match=r"orders.amount_paise.range"):
        analyse(data)


def test_a_renamed_column_stops_the_run(export_copy):
    data = export_copy(EXPORT_V10)
    path = data / "events.csv"
    path.write_text(path.read_text(encoding="utf-8").replace("event_name", "event", 1), encoding="utf-8")
    with pytest.raises(ContractError, match=r"events\.csv is missing column"):
        analyse(data)
