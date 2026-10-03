from datetime import datetime

import duckdb
import pytest

from tests.conftest import EXPECTED, TINY, prepared


def clean_one(contract, table, column, text):
    """Run 02_clean.sql's own view on a one-row raw table and read back the parsed value."""
    con = prepared(TINY, contract, "02_clean.sql")
    if table == "sessions":
        con.execute(
            "CREATE OR REPLACE TABLE raw_sessions AS SELECT 'S1' AS session_id, '1' AS user_id, "
            "'mobile' AS device, 'email' AS channel, ? AS started_at",
            [text],
        )
        return con.execute("SELECT started_at FROM s1_normalised").fetchone()[0]
    con.execute(
        "CREATE OR REPLACE TABLE raw_orders AS SELECT 'O1' AS order_id, 'S1' AS session_id, ? AS amount", [text]
    )
    return con.execute("SELECT amount_paise FROM o2_parsed").fetchone()[0]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2026-01-05 14:03:00", datetime(2026, 1, 5, 14, 3)),
        ("05/01/2026 14:03", datetime(2026, 1, 5, 14, 3)),  # day first, never month first
        (" 2026-01-05 14:03:00 ", datetime(2026, 1, 5, 14, 3)),
        ("2026-02-30 10:00:00", None),  # impossible date
        ("31/04/2026 10:00", None),
        ("2026-01-05", None),  # neither of the two formats
        ("01/05/2026 14:03:00", None),
        ("", None),
    ],
)
def test_parse_timestamp(contract, text, expected):
    assert clean_one(contract, "sessions", "started_at", text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("₹1,299.00", 129900),
        ("1299", 129900),
        ("Rs. 1,299", 129900),
        ("-₹499.00", -49900),
        ("1,299.5", 129950),
        (" 0 ", 0),
        ("N/A", None),
        ("", None),
        ("1,2O0.00", None),  # letter O, not zero
        ("12.345", None),
        ("₹", None),
    ],
)
def test_parse_amount_paise(contract, text, expected):
    assert clean_one(contract, "orders", "amount", text) == expected


def test_issue_counts_match_the_hand_checked_fixture(tiny):
    got = tiny.execute("SELECT issue, n FROM issues ORDER BY position").fetchall()
    assert dict(got) == EXPECTED["issues"]
    assert [i for i, _ in got] == list(EXPECTED["issues"])  # same order in every track


def test_clean_rows_and_keys(tiny):
    assert {t: tiny.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in EXPECTED["clean_rows"]} == EXPECTED[
        "clean_rows"
    ]
    assert [r[0] for r in tiny.execute("SELECT session_id FROM sessions ORDER BY session_id").fetchall()] == EXPECTED[
        "clean_session_ids"
    ]
    assert dict(tiny.execute("SELECT order_id, amount_paise FROM orders").fetchall()) == EXPECTED["clean_order_paise"]


def test_labels_are_normalised(tiny):
    def distinct(sql):
        return sorted(r[0] for r in tiny.execute(sql).fetchall())

    assert distinct("SELECT DISTINCT device FROM sessions") == ["desktop", "mobile"]
    assert distinct("SELECT DISTINCT channel FROM sessions") == ["email", "organic", "paid_social", "unknown"]
    assert distinct("SELECT DISTINCT city FROM users") == ["bengaluru", "pune"]
    assert tiny.execute("SELECT count(*) FROM users WHERE signup_channel IS NULL").fetchone()[0] == 1


def test_iso_week_and_month(tiny):
    s = dict(tiny.execute("SELECT session_id, week FROM sessions").fetchall())
    assert s["S1"] == "2026-W10"  # Monday 2 March 2026
    assert s["S6"] == "2026-W11"
    assert tiny.execute("SELECT started_at FROM sessions WHERE session_id = 'S11'").fetchone()[0] == datetime(
        2026, 3, 10, 18, 45
    )
    assert tiny.execute("SELECT DISTINCT month FROM sessions").fetchall() == [("2026-03",)]


def test_events_keep_the_first_timestamp_per_step(tiny):
    first = tiny.execute("SELECT first_at FROM events WHERE session_id = 'S2' AND event_name = 'view'").fetchone()[0]
    assert first == datetime(2026, 3, 2, 11, 0, 5)
    dup = tiny.execute(
        "SELECT count(*) FROM (SELECT session_id, event_name FROM events GROUP BY ALL HAVING count(*) > 1)"
    )
    assert dup.fetchone()[0] == 0


def test_clean_tables_have_typed_columns(tiny):
    types = dict((r[0], r[1]) for r in tiny.execute("DESCRIBE sessions").fetchall())
    assert types["started_at"] == "TIMESTAMP" and types["user_id"] == "BIGINT"
    with pytest.raises(duckdb.CatalogException):
        tiny.execute("SELECT * FROM funnel_by_device")  # metrics are M3, not part of cleaning
