"""answers.json -> a short list of numbered facts [F1]..[Fn].

The facts are the ONLY thing the AI narrator ever sees: aggregates from answers.json, never raw rows,
user ids or order ids. Each fact keeps its exact values so the guardrails can check every number the
model writes against them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

RECOMMENDATION_LABELS = {
    "run_targeted_experiment": "run a targeted experiment on the mobile payment step",
    "rebuild_checkout": "rebuild the mobile checkout",
    "no_checkout_gap_found": "do not rebuild the mobile checkout",
}


@dataclass(frozen=True)
class Fact:
    id: str
    text: str
    values: tuple[float, ...] = field(default_factory=tuple)


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def lakh(inr: float) -> str:
    return f"₹{inr / 1e5:.1f} lakh"


def p_text(p: float) -> str:
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def build_facts(a: dict) -> list[Fact]:
    f = a["funnel"]
    pay = a["payment_step_test"]
    cmh = a["by_channel"]["cmh"]
    simpson = a["by_channel"]["simpson"]
    value = a["order_value"]
    opp = a["opportunity"]
    dec = a["decision"]
    ds = a["dataset"]
    threshold = dec["thresholds"]["rebuild_min_monthly_uplift_inr"]
    pay_cmh = cmh["purchase_given_checkout"]
    cart_cmh = cmh["cart_given_view"]
    every = round(1 / ds["sample_rate"])
    facts = [
        (
            f"Export {ds['export']} covers {ds['period_start']} to {ds['period_end']} ({ds['months']} months, "
            f"a 1-in-{every} sample of sessions).",
            (ds["months"], 1, every),
        ),
        (
            f"Mobile is {pct(f['mobile_share_of_sessions'])} of sessions but {pct(f['mobile_share_of_revenue'])} "
            "of revenue.",
            (100 * f["mobile_share_of_sessions"], 100 * f["mobile_share_of_revenue"]),
        ),
        (
            f"After checkout, {pct(pay['mobile']['rate'])} of mobile sessions purchase vs "
            f"{pct(pay['desktop']['rate'])} on desktop ({100 * pay['difference']:+.1f} percentage points, "
            f"{p_text(pay['p_value'])}).",
            (100 * pay["mobile"]["rate"], 100 * pay["desktop"]["rate"], 100 * pay["difference"], 0.001, pay["p_value"]),
        ),
        (
            f"Within acquisition channels the mobile payment gap remains: odds ratio {pay_cmh['odds_ratio_mh']:.2f} "
            f"(95% CI {pay_cmh['ci95'][0]:.2f} to {pay_cmh['ci95'][1]:.2f}, {p_text(pay_cmh['p_value'])}).",
            (pay_cmh["odds_ratio_mh"], 95, *pay_cmh["ci95"], 0.001, pay_cmh["p_value"]),
        ),
        (
            f"The aggregate mobile cart gap ({100 * simpson['aggregate_gap']:+.1f} percentage points) is channel "
            f"mix: within channels mobile adds to cart at an odds ratio of {cart_cmh['odds_ratio_mh']:.2f}.",
            (100 * simpson["aggregate_gap"], cart_cmh["odds_ratio_mh"]),
        ),
        (
            f"Order values are similar: ₹{value['mobile']['mean_inr']:,.0f} on mobile vs "
            f"₹{value['desktop']['mean_inr']:,.0f} on desktop ({p_text(value['p_value'])}).",
            (value["mobile"]["mean_inr"], value["desktop"]["mean_inr"], value["p_value"]),
        ),
        (
            f"If mobile paid like desktop within each channel, revenue would rise by about "
            f"{lakh(opp['monthly_revenue_uplift_inr'])} a month ({pct(opp['uplift_share_of_mobile_revenue'])} of "
            "mobile revenue).",
            (opp["monthly_revenue_uplift_inr"] / 1e5, 100 * opp["uplift_share_of_mobile_revenue"]),
        ),
        (f"The agreed threshold for a rebuild is {lakh(threshold)} a month.", (threshold / 1e5,)),
        (f"Recommendation: {RECOMMENDATION_LABELS[dec['recommendation']]}.", ()),
    ]
    facts += extra_facts(a)
    return [
        Fact(id=f"F{i}", text=text, values=tuple(float(v) for v in values))
        for i, (text, values) in enumerate(facts, start=1)
    ]


def extra_facts(a: dict) -> list[tuple[str, tuple]]:
    """Facts from optional answer sections (none in schema 1.0)."""
    return []


def facts_block(facts: list[Fact]) -> str:
    return "\n".join(f"[{f.id}] {f.text}" for f in facts)
