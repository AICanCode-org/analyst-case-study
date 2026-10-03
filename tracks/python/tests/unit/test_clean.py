from datetime import datetime

import pytest

from funnellens.clean import parse_amount_paise, parse_timestamp
from tests.conftest import EXPECTED


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
def test_parse_timestamp(text, expected):
    assert parse_timestamp(text) == expected


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
def test_parse_amount_paise(text, expected):
    assert parse_amount_paise(text) == expected


def test_issue_counts_match_the_hand_checked_fixture(tiny):
    clean, _ = tiny
    assert clean.issues == EXPECTED["issues"]
    assert list(clean.issues) == list(EXPECTED["issues"])  # same order in every track


def test_clean_rows_and_keys(tiny):
    clean, _ = tiny
    assert {t: len(getattr(clean, t)) for t in EXPECTED["clean_rows"]} == EXPECTED["clean_rows"]
    assert clean.sessions["session_id"].tolist() == EXPECTED["clean_session_ids"]
    assert (
        dict(zip(clean.orders["order_id"], clean.orders["amount_paise"].astype(int), strict=True))
        == EXPECTED["clean_order_paise"]
    )


def test_labels_are_normalised(tiny):
    clean, _ = tiny
    assert set(clean.sessions["device"]) == {"desktop", "mobile"}
    assert set(clean.sessions["channel"]) == {"email", "organic", "paid_social", "unknown"}
    assert sorted(clean.users["city"].unique()) == ["bengaluru", "pune"]
    assert clean.users["signup_channel"].isna().sum() == 1


def test_iso_week_and_month(tiny):
    clean, _ = tiny
    s = clean.sessions.set_index("session_id")
    assert s.loc["S1", "week"] == "2026-W10"  # Monday 2 March 2026
    assert s.loc["S6", "week"] == "2026-W11"
    assert s.loc["S11", "started_at"] == datetime(2026, 3, 10, 18, 45)
    assert set(s["month"]) == {"2026-03"}


def test_events_keep_the_first_timestamp_per_step(tiny):
    clean, _ = tiny
    e = clean.events.set_index(["session_id", "event_name"])
    assert e.loc[("S2", "view"), "first_at"] == datetime(2026, 3, 2, 11, 0, 5)
    assert not clean.events.duplicated(["session_id", "event_name"]).any()
