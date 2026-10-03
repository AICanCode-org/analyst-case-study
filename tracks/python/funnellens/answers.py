"""M5: answer the business questions and write answers.json (contract/answers.schema.json)."""

from __future__ import annotations

import pandas as pd

from . import __version__
from .clean import Clean
from .contract import Export
from .metrics import DEVICES, by_channel, funnel_by_device, session_funnel, weekly
from .monitoring import monitoring, payment_methods
from .stats import cmh, two_proportion, welch

SCHEMA_VERSION = "1.1"
CMH_STEPS = {"cart_given_view": ("cart", "view"), "purchase_given_checkout": ("purchase", "checkout")}


def payment_step_test(funnel: dict, z_975: float) -> dict:
    m, d = funnel["by_device"]["mobile"], funnel["by_device"]["desktop"]
    res = two_proportion(m["purchase"], m["checkout"], d["purchase"], d["checkout"], z_975)
    return {
        "metric": "purchase_given_checkout",
        "mobile": {"n": m["checkout"], "successes": m["purchase"], "rate": m["purchase"] / m["checkout"]},
        "desktop": {"n": d["checkout"], "successes": d["purchase"], "rate": d["purchase"] / d["checkout"]},
        **res,
    }


def strata(channels: list[dict], success: str, base: str) -> list[tuple[str, tuple[int, int, int, int]]]:
    """2x2 tables (mobile successes, mobile failures, desktop successes, desktop failures) per channel,
    keeping only channels where both devices have at least one session at the `base` step."""
    out = []
    for row in channels:
        m, d = row["mobile"], row["desktop"]
        if m[base] > 0 and d[base] > 0:
            out.append((row["channel"], (m[success], m[base] - m[success], d[success], d[base] - d[success])))
    return out


def channel_section(channels: list[dict], funnel: dict, z_975: float) -> dict:
    tests = {name: cmh([t for _, t in strata(channels, *steps)], z_975) for name, steps in CMH_STEPS.items()}
    agg = funnel["by_device"]
    aggregate_gap = agg["mobile"]["step_rates"]["cart"] - agg["desktop"]["step_rates"]["cart"]
    within = {}
    for channel, (a, b, c, d) in strata(channels, "cart", "view"):
        within[channel] = a / (a + b) - c / (c + d)
    gaps = list(within.values())
    reversal = (aggregate_gap < 0 and all(g > 0 for g in gaps)) or (aggregate_gap > 0 and all(g < 0 for g in gaps))
    return {
        "channels": channels,
        "cmh": tests,
        "simpson": {
            "step": "cart_given_view",
            "aggregate_gap": aggregate_gap,
            "within_channel_gaps": within,
            "reversal": reversal,
        },
    }


def order_value(clean: Clean) -> dict:
    o = clean.orders.merge(clean.sessions[["session_id", "device"]], on="session_id")
    values = {d: (o.loc[o["device"] == d, "amount_paise"] / 100).tolist() for d in DEVICES}
    summary = {
        d: {"orders": len(v), "mean_inr": float(pd.Series(v).mean()), "sd_inr": float(pd.Series(v).std(ddof=1))}
        for d, v in values.items()
    }
    res = welch(values["mobile"], values["desktop"])
    return {
        "mobile": summary["mobile"],
        "desktop": summary["desktop"],
        "difference_inr": res["difference"],
        "welch_t": res["t"],
        "df": res["df"],
        "p_value": res["p_value"],
        "ci95": res["ci95"],
    }


def opportunity(channels: list[dict], funnel: dict, value: dict, export: Export) -> dict:
    rows, total = [], 0.0
    for channel, (a, b, c, d) in strata(channels, "purchase", "checkout"):
        gap = max(0.0, c / (c + d) - a / (a + b))
        extra = (a + b) * gap
        total += extra
        rows.append({"channel": channel, "gap": gap, "extra_orders": extra})
    per_month = total / export.months
    aov = value["mobile"]["mean_inr"]
    scale = 1 / export.sample_rate
    uplift = per_month * aov * scale
    mobile_monthly = funnel["by_device"]["mobile"]["revenue_paise"] / 100 / export.months * scale
    return {
        "by_channel": rows,
        "extra_orders_in_sample": total,
        "months": export.months,
        "sample_rate": export.sample_rate,
        "extra_orders_per_month": per_month * scale,
        "mobile_aov_inr": aov,
        "monthly_revenue_uplift_inr": uplift,
        "mobile_monthly_revenue_inr": mobile_monthly,
        "uplift_share_of_mobile_revenue": uplift / mobile_monthly,
    }


def decision(channel: dict, opp: dict, contract: dict) -> dict:
    a = contract["analysis"]
    pay, cart = channel["cmh"]["purchase_given_checkout"], channel["cmh"]["cart_given_view"]
    if pay["p_value"] >= a["alpha"]:
        rec, reasons = "no_checkout_gap_found", ["adjusted_payment_gap_not_significant"]
    elif opp["monthly_revenue_uplift_inr"] >= a["rebuild_min_monthly_uplift_inr"]:
        rec, reasons = "rebuild_checkout", ["adjusted_payment_gap_significant", "uplift_above_rebuild_threshold"]
    else:
        rec, reasons = "run_targeted_experiment", ["adjusted_payment_gap_significant", "uplift_below_rebuild_threshold"]
    # Mobile carts less overall, but not within channels: the aggregate gap is the channel mix.
    if channel["simpson"]["aggregate_gap"] < 0 and (cart["p_value"] >= a["alpha"] or cart["odds_ratio_mh"] >= 1):
        reasons.append("aggregate_cart_gap_is_channel_mix")
    return {
        "recommendation": rec,
        "reasons": reasons,
        "thresholds": {"alpha": a["alpha"], "rebuild_min_monthly_uplift_inr": a["rebuild_min_monthly_uplift_inr"]},
    }


def build_answers(clean: Clean, checks: list[dict], export: Export, contract: dict, track: str = "python") -> dict:
    z = contract["analysis"]["z_975"]
    sf = session_funnel(clean)
    funnel = funnel_by_device(sf, clean)
    channels = by_channel(sf)
    channel = channel_section(channels, funnel, z)
    value = order_value(clean)
    opp = opportunity(channels, funnel, value, export)
    return {
        "schema": "funnellens-answers",
        "schema_version": SCHEMA_VERSION,
        "generator": {"track": track, "version": __version__},
        "dataset": {
            "export": export.name,
            "period_start": export.period_start.isoformat(),
            "period_end": export.period_end.isoformat(),
            "months": export.months,
            "sample_rate": export.sample_rate,
            "contract_version": contract["version"],
        },
        "data_quality": {
            "raw_rows": clean.raw_rows,
            "clean_rows": {t: len(getattr(clean, t)) for t in ("users", "sessions", "events", "orders")},
            "issues": clean.issues,
            "checks": checks,
        },
        "funnel": funnel,
        "payment_step_test": payment_step_test(funnel, z),
        "by_channel": channel,
        "order_value": value,
        "weekly": weekly(sf),
        "opportunity": opp,
        "decision": decision(channel, opp, contract),
        "monitoring": monitoring(sf, clean, export, contract),  # v1.1
        "payment_methods": payment_methods(clean),  # v1.1
    }
