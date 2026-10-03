"""v1.1: data-quality monitoring (contract/questions.md §6) and the payment-method breakdown.

Monitoring reports; it never stops the run. It answers "can I compare this week with the others?"
before anyone reads a trend: freshness of the export, and full ISO weeks whose volume or mobile
checkout rate is far from the median week (a tracking break looks exactly like that).
"""

from __future__ import annotations

from datetime import timedelta
from statistics import median

import pandas as pd

from .clean import Clean, normalise_label
from .contract import Export

METRICS = ["sessions", "mobile_checkout_given_cart"]

DEFAULT_MONITORING = {"max_relative_deviation": 0.30, "max_days_behind": 2}


def full_weeks(sf: pd.DataFrame, clean: Clean, export: Export) -> list[dict]:
    day = clean.sessions.set_index("session_id")["started_at"].map(lambda t: t.date())
    monday = sf["session_id"].map(day).map(lambda d: d - timedelta(days=d.weekday()))
    full = (monday >= export.period_start) & (monday + timedelta(days=6) <= export.period_end)
    rows = []
    for week, part in sf[full].groupby("week", sort=True):
        mobile = part[part["device"] == "mobile"]
        carts = int(mobile["cart"].sum())
        rows.append(
            {
                "week": week,
                "sessions": len(part),
                "mobile_checkout_given_cart": int(mobile["checkout"].sum()) / carts if carts else None,
            }
        )
    return rows


def monitoring(sf: pd.DataFrame, clean: Clean, export: Export, contract: dict) -> dict:
    cfg = contract.get("monitoring", DEFAULT_MONITORING)  # a 1.0 contract has no section
    last = max(t.date() for t in clean.sessions["started_at"])
    behind = (export.period_end - last).days
    weeks = full_weeks(sf, clean, export)
    medians = {}
    for m in METRICS:
        values = [w[m] for w in weeks if w[m] is not None]
        medians[m] = median(values) if values else None
    anomalies = []
    for w in weeks:
        for m in METRICS:
            value, mid = w[m], medians[m]
            if value is None or not mid:
                continue
            deviation = (value - mid) / mid
            if abs(deviation) > cfg["max_relative_deviation"]:
                anomalies.append(
                    {"week": w["week"], "metric": m, "value": value, "median": mid, "deviation": deviation}
                )
    return {
        "freshness": {
            "period_end": export.period_end.isoformat(),
            "last_session_date": last.isoformat(),
            "days_behind": behind,
            "stale": behind > cfg["max_days_behind"],
        },
        "excluded_weeks": list(contract["cleaning"].get("exclude_weeks", [])),
        "max_relative_deviation": cfg["max_relative_deviation"],
        "weeks": weeks,
        "medians": medians,
        "anomalies": anomalies,
    }


def payment_methods(clean: Clean) -> dict | None:
    if "payment_method" not in clean.orders.columns:
        return None
    o = clean.orders.merge(clean.sessions[["session_id", "device"]], on="session_id")
    method = normalise_label(o["payment_method"].fillna("")).replace("", "unknown")
    by_device = {}
    for device in ("desktop", "mobile"):
        counts = method[o["device"] == device].value_counts()
        by_device[device] = {m: int(counts[m]) for m in sorted(counts.index)}
    return {"by_device": by_device}
