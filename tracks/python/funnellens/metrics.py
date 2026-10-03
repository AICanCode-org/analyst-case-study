"""M3: the funnel, per device, per channel and per ISO week (contract/questions.md §3)."""

from __future__ import annotations

import pandas as pd

from .clean import Clean

STEPS = ["view", "cart", "checkout", "purchase"]
DEVICES = ["desktop", "mobile"]


def session_funnel(clean: Clean) -> pd.DataFrame:
    """One row per clean session with booleans view/cart/checkout/purchase (each implies the previous)."""
    has = clean.events.assign(flag=True).pivot_table(
        index="session_id", columns="event_name", values="flag", aggfunc="any", fill_value=False
    )
    s = clean.sessions[["session_id", "device", "channel", "week", "month"]].copy()
    for step in ("view", "cart", "checkout"):
        s[step] = s["session_id"].map(has.get(step, {})).fillna(False).astype(bool)
    s["cart"] &= s["view"]
    s["checkout"] &= s["cart"]
    s["purchase"] = s["checkout"] & s["session_id"].isin(clean.orders["session_id"])
    return s


def counts(df: pd.DataFrame) -> dict:
    return {"sessions": len(df), **{step: int(df[step].sum()) for step in STEPS}}


def rates(c: dict) -> dict:
    def ratio(a: int, b: int) -> float | None:
        return a / b if b else None

    return {
        "conversion": ratio(c["purchase"], c["sessions"]),
        "step_rates": {
            "view": ratio(c["view"], c["sessions"]),
            "cart": ratio(c["cart"], c["view"]),
            "checkout": ratio(c["checkout"], c["cart"]),
            "purchase": ratio(c["purchase"], c["checkout"]),
        },
    }


def funnel_by_device(funnel: pd.DataFrame, clean: Clean) -> dict:
    revenue = clean.orders.merge(clean.sessions[["session_id", "device"]], on="session_id")
    out = {}
    for device in ["all", *DEVICES]:
        part = funnel if device == "all" else funnel[funnel["device"] == device]
        c = counts(part)
        paise = revenue["amount_paise"] if device == "all" else revenue.loc[revenue["device"] == device, "amount_paise"]
        out[device] = {**c, "revenue_paise": int(paise.sum()), **rates(c)}
    total = out["all"]
    return {
        "steps": ["sessions", *STEPS],
        "by_device": out,
        "mobile_share_of_sessions": out["mobile"]["sessions"] / total["sessions"],
        "mobile_share_of_revenue": out["mobile"]["revenue_paise"] / total["revenue_paise"],
    }


def by_channel(funnel: pd.DataFrame) -> list[dict]:
    rows = []
    for channel in sorted(funnel["channel"].unique()):
        part = funnel[funnel["channel"] == channel]
        rows.append({"channel": channel, **{d: counts(part[part["device"] == d]) for d in DEVICES}})
    return rows


def weekly(funnel: pd.DataFrame) -> list[dict]:
    rows = []
    for week in sorted(funnel["week"].unique()):
        part = funnel[funnel["week"] == week]
        sessions = {d: int((part["device"] == d).sum()) for d in DEVICES}
        purchases = {d: int(part.loc[part["device"] == d, "purchase"].sum()) for d in DEVICES}
        rows.append(
            {
                "week": week,
                "sessions": sessions,
                "purchases": purchases,
                "conversion": {d: (purchases[d] / sessions[d] if sessions[d] else None) for d in DEVICES},
            }
        )
    return rows
