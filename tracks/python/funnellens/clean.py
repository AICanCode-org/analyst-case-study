"""M1: the cleaning rules of contract/questions.md §2, in the order they are written there.

Every rule that removes or changes rows also counts what it did, so the numbers in the report can
be traced back to raw rows (the `issues` dict, reported as data_quality.issues).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from itertools import pairwise

import pandas as pd

from .contract import Export

ISO = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
DMY = re.compile(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$")
AMOUNT = re.compile(r"^(-?)(\d+)(?:\.(\d{1,2}))?$")
AMOUNT_NOISE = ("₹", "Rs.", ",", " ")


@dataclass
class Clean:
    users: pd.DataFrame
    sessions: pd.DataFrame
    events: pd.DataFrame  # one row per (session_id, event_name) with the first timestamp
    orders: pd.DataFrame
    issues: dict[str, int] = field(default_factory=dict)
    raw_rows: dict[str, int] = field(default_factory=dict)


def parse_timestamp(text: str) -> datetime | None:
    """'2026-01-05 14:03:00' or '05/01/2026 14:03' (day first); anything else, or an impossible date, is None."""
    text = text.strip()
    try:
        if ISO.match(text):
            return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        if DMY.match(text):
            return datetime.strptime(text, "%d/%m/%Y %H:%M")
    except ValueError:
        return None
    return None


def parse_amount_paise(text: str) -> int | None:
    """'₹1,299.00' / '1299' / 'Rs. 1,299' / '-₹499.00' -> integer paise; None if it is not a number."""
    t = text.strip()
    for noise in AMOUNT_NOISE:
        t = t.replace(noise, "")
    m = AMOUNT.match(t)
    if not m:
        return None
    sign, rupees, frac = m.groups()
    paise = int(rupees) * 100 + int((frac or "0").ljust(2, "0"))
    return -paise if sign else paise


def normalise_label(series: pd.Series) -> pd.Series:
    return series.str.strip().str.lower()


def clean_users(raw: pd.DataFrame, contract: dict, issues: dict) -> pd.DataFrame:
    aliases = contract["cleaning"]["city_aliases"]
    users = pd.DataFrame(
        {
            "user_id": raw["user_id"].str.strip().astype("int64"),
            "signup_channel": raw["signup_channel"].str.strip().replace("", None),
            "city": normalise_label(raw["city"]).replace(aliases),
        }
    )
    issues["users_missing_signup_channel"] = int(users["signup_channel"].isna().sum())
    issues["users_city_variants_merged"] = int(raw["city"].nunique() - users["city"].nunique())
    return users


def clean_sessions(
    raw: pd.DataFrame, users: pd.DataFrame, export: Export, contract: dict, issues: dict
) -> pd.DataFrame:
    unknown = set(contract["cleaning"]["unknown_channel_values"])
    s = pd.DataFrame(
        {
            "session_id": raw["session_id"].str.strip(),
            "user_id": raw["user_id"].str.strip(),
            "device": normalise_label(raw["device"]),
            "channel": normalise_label(raw["channel"]),
            "started_at": raw["started_at"].map(parse_timestamp),
        }
    )
    s.loc[s["channel"].isin(unknown), "channel"] = "unknown"

    bad = s["started_at"].isna()
    issues["sessions_bad_timestamp"] = int(bad.sum())
    s = s[~bad]

    before = len(s)
    s = s.drop_duplicates()
    issues["sessions_exact_duplicates"] = before - len(s)

    conflicting = s["session_id"].duplicated(keep=False)
    issues["sessions_conflicting_ids"] = int(s.loc[conflicting, "session_id"].nunique())
    s = s[~conflicting]

    day = s["started_at"].map(lambda t: t.date())
    outside = (day < export.period_start) | (day > export.period_end)
    issues["sessions_out_of_period"] = int(outside.sum())
    s = s[~outside]

    s = s.assign(user_id=s["user_id"].astype("int64"))
    orphan = ~s["user_id"].isin(users["user_id"])
    issues["sessions_orphan_user"] = int(orphan.sum())
    s = s[~orphan]

    issues["sessions_unknown_channel"] = int((s["channel"] == "unknown").sum())
    iso = s["started_at"].map(lambda t: t.isocalendar())
    return (
        s.assign(
            week=[f"{y}-W{w:02d}" for y, w, _ in iso],
            month=s["started_at"].map(lambda t: t.strftime("%Y-%m")),
        )
        .sort_values("session_id")
        .reset_index(drop=True)
    )


def clean_events(raw: pd.DataFrame, sessions: pd.DataFrame, contract: dict, issues: dict) -> pd.DataFrame:
    steps = contract["cleaning"]["steps"]
    e = pd.DataFrame(
        {
            "session_id": raw["session_id"].str.strip(),
            "event_name": normalise_label(raw["event_name"]),
            "event_at": raw["event_at"].map(parse_timestamp),
        }
    )
    unknown = ~e["event_name"].isin(steps)
    issues["events_unknown_name"] = int(unknown.sum())
    e = e[~unknown]
    orphan = ~e["session_id"].isin(sessions["session_id"])
    issues["events_orphan_session"] = int(orphan.sum())
    e = e[~orphan]

    first = e.groupby(["session_id", "event_name"], as_index=False)["event_at"].min()
    issues["events_repeated_steps"] = len(e) - len(first)

    wide = first.pivot(index="session_id", columns="event_name", values="event_at")
    out_of_order = pd.Series(False, index=wide.index)
    for earlier, later in pairwise(steps):
        if earlier in wide and later in wide:
            out_of_order |= wide[later] < wide[earlier]  # NaT compares False: both steps must exist
    issues["sessions_out_of_order"] = int(out_of_order.sum())
    return (
        first.rename(columns={"event_at": "first_at"}).sort_values(["session_id", "event_name"]).reset_index(drop=True)
    )


def clean_orders(raw: pd.DataFrame, sessions: pd.DataFrame, events: pd.DataFrame, issues: dict) -> pd.DataFrame:
    before = len(raw)
    o = raw.drop_duplicates()
    issues["orders_exact_duplicates"] = before - len(o)
    o = o.assign(
        order_id=o["order_id"].str.strip(),
        session_id=o["session_id"].str.strip(),
        amount_paise=o["amount"].map(parse_amount_paise),
    )
    unparseable = o["amount_paise"].isna()
    issues["orders_unparseable_amount"] = int(unparseable.sum())
    o = o[~unparseable]
    non_positive = o["amount_paise"] <= 0
    issues["orders_non_positive_amount"] = int(non_positive.sum())
    o = o[~non_positive]
    orphan = ~o["session_id"].isin(sessions["session_id"])
    issues["orders_orphan_session"] = int(orphan.sum())
    o = o[~orphan]
    checkout_sessions = events.loc[events["event_name"] == "checkout", "session_id"]
    issues["orders_without_checkout"] = int((~o["session_id"].isin(checkout_sessions)).sum())
    cols = ["order_id", "session_id", "amount_paise"] + [
        c for c in raw.columns if c not in ("order_id", "session_id", "amount")
    ]
    o = o.assign(amount_paise=o["amount_paise"].astype("int64"))
    return o[cols].sort_values("order_id").reset_index(drop=True)


ISSUE_ORDER = [
    "sessions_bad_timestamp",
    "sessions_exact_duplicates",
    "sessions_conflicting_ids",
    "sessions_out_of_period",
    "sessions_orphan_user",
    "sessions_unknown_channel",
    "users_missing_signup_channel",
    "users_city_variants_merged",
    "events_unknown_name",
    "events_orphan_session",
    "events_repeated_steps",
    "sessions_out_of_order",
    "orders_exact_duplicates",
    "orders_unparseable_amount",
    "orders_non_positive_amount",
    "orders_orphan_session",
    "orders_without_checkout",
]


def clean(raw: dict[str, pd.DataFrame], export: Export, contract: dict) -> Clean:
    issues: dict[str, int] = {}
    users = clean_users(raw["users"], contract, issues)
    sessions = clean_sessions(raw["sessions"], users, export, contract, issues)
    events = clean_events(raw["events"], sessions, contract, issues)
    orders = clean_orders(raw["orders"], sessions, events, issues)
    return Clean(
        users=users,
        sessions=sessions,
        events=events,
        orders=orders,
        issues={k: issues[k] for k in ISSUE_ORDER},
        raw_rows={t: len(df) for t, df in raw.items()},
    )
