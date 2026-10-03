import pytest

from funnellens.answers import decision, opportunity, strata
from funnellens.contract import Export

CHANNELS = [
    {
        "channel": "email",
        "mobile": {"view": 100, "cart": 40, "checkout": 20, "purchase": 10},
        "desktop": {"view": 100, "cart": 40, "checkout": 20, "purchase": 15},
    },
    {
        "channel": "organic",
        "mobile": {"view": 50, "cart": 10, "checkout": 5, "purchase": 4},
        "desktop": {"view": 80, "cart": 30, "checkout": 10, "purchase": 6},
    },
    {
        "channel": "referral",
        "mobile": {"view": 9, "cart": 3, "checkout": 2, "purchase": 1},
        "desktop": {"view": 0, "cart": 0, "checkout": 0, "purchase": 0},
    },
]
EXPORT = Export(
    name="2026-03",
    period_start=__import__("datetime").date(2026, 1, 1),
    period_end=__import__("datetime").date(2026, 2, 28),
    sample_rate=0.5,
)


def test_strata_skip_channels_missing_a_device():
    assert strata(CHANNELS, "purchase", "checkout") == [("email", (10, 10, 15, 5)), ("organic", (4, 1, 6, 4))]


def test_opportunity_counts_only_positive_gaps_and_scales_the_sample():
    funnel = {"by_device": {"mobile": {"revenue_paise": 1_000_000}}}
    value = {"mobile": {"mean_inr": 2000.0}}
    opp = opportunity(CHANNELS, funnel, value, EXPORT)
    assert [r["gap"] for r in opp["by_channel"]] == [pytest.approx(0.25), 0.0]  # organic: mobile is better
    assert opp["extra_orders_in_sample"] == pytest.approx(20 * 0.25)
    assert opp["months"] == 2
    assert opp["extra_orders_per_month"] == pytest.approx(5 / 2 / 0.5)
    assert opp["monthly_revenue_uplift_inr"] == pytest.approx(5 * 2000)
    assert opp["mobile_monthly_revenue_inr"] == pytest.approx(10_000 / 2 / 0.5)
    assert opp["uplift_share_of_mobile_revenue"] == pytest.approx(1.0)


def channel(pay_p, cart_p=0.5, cart_or=1.1, cart_gap=-0.05):
    return {
        "cmh": {
            "purchase_given_checkout": {"p_value": pay_p},
            "cart_given_view": {"p_value": cart_p, "odds_ratio_mh": cart_or},
        },
        "simpson": {"aggregate_gap": cart_gap},
    }


@pytest.mark.parametrize(
    ("pay_p", "uplift", "expected"),
    [
        (0.20, 9e9, ("no_checkout_gap_found", ["adjusted_payment_gap_not_significant"])),
        (
            0.05,
            9e9,
            ("no_checkout_gap_found", ["adjusted_payment_gap_not_significant"]),
        ),  # p = alpha is not significant
        (0.01, 2_500_000, ("rebuild_checkout", ["adjusted_payment_gap_significant", "uplift_above_rebuild_threshold"])),
        (
            0.01,
            2_499_999,
            ("run_targeted_experiment", ["adjusted_payment_gap_significant", "uplift_below_rebuild_threshold"]),
        ),
    ],
)
def test_decision_rules(contract, pay_p, uplift, expected):
    d = decision(channel(pay_p, cart_gap=0.01), {"monthly_revenue_uplift_inr": uplift}, contract)
    assert (d["recommendation"], d["reasons"]) == expected
    assert d["thresholds"] == {"alpha": 0.05, "rebuild_min_monthly_uplift_inr": 2500000}


@pytest.mark.parametrize(
    ("cart_p", "cart_or", "cart_gap", "mix"),
    [
        (0.30, 0.9, -0.05, True),  # not significant within channels
        (0.01, 1.08, -0.05, True),  # significant, but mobile carts MORE within channels
        (0.01, 0.9, -0.05, False),  # a real within-channel cart gap
        (0.30, 1.1, 0.02, False),  # no aggregate gap to explain
    ],
)
def test_channel_mix_reason(contract, cart_p, cart_or, cart_gap, mix):
    d = decision(channel(0.01, cart_p, cart_or, cart_gap), {"monthly_revenue_uplift_inr": 0}, contract)
    assert ("aggregate_cart_gap_is_channel_mix" in d["reasons"]) is mix
