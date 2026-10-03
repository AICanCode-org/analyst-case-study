"""M5 · the decision rules of sql/05_answers.sql, on stub cmh / simpson / opportunity inputs."""

import pytest

from funnellens_sql import runner


def decide(contract, pay_p, uplift, cart_p=0.5, cart_or=1.1, cart_gap=0.01):
    con = runner.connect()
    con.execute("SET VARIABLE alpha = 0.05")
    con.execute("SET VARIABLE rebuild_min_monthly_uplift_inr = 2500000")
    con.execute("SET VARIABLE months = 2.0")
    con.execute("SET VARIABLE sample_rate = 0.5")
    con.execute(
        "CREATE TABLE cmh AS SELECT * FROM (VALUES ('purchase_given_checkout', ?, 1.0), "
        "('cart_given_view', ?, ?)) AS t (step, p_value, odds_ratio_mh)",
        [pay_p, cart_p, cart_or],
    )
    con.execute("CREATE TABLE simpson AS SELECT ? AS aggregate_gap, false AS reversal", [cart_gap])
    con.execute("CREATE TABLE opportunity AS SELECT ? AS monthly_revenue_uplift_inr", [uplift])
    sql = runner.SQL_DIR.joinpath("05_answers.sql").read_text(encoding="utf-8")
    con.execute(sql[sql.index("CREATE OR REPLACE VIEW decision") :])
    rec, reasons = con.execute("SELECT recommendation, reasons FROM decision").fetchone()
    return rec, list(reasons)


@pytest.mark.parametrize(
    ("pay_p", "uplift", "expected"),
    [
        (0.20, 9e9, ("no_checkout_gap_found", ["adjusted_payment_gap_not_significant"])),
        (0.05, 9e9, ("no_checkout_gap_found", ["adjusted_payment_gap_not_significant"])),  # p = alpha
        (0.01, 2_500_000, ("rebuild_checkout", ["adjusted_payment_gap_significant", "uplift_above_rebuild_threshold"])),
        (
            0.01,
            2_499_999,
            ("run_targeted_experiment", ["adjusted_payment_gap_significant", "uplift_below_rebuild_threshold"]),
        ),
    ],
)
def test_decision_rules(contract, pay_p, uplift, expected):
    assert decide(contract, pay_p, uplift) == expected


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
    _, reasons = decide(contract, 0.01, 0, cart_p, cart_or, cart_gap)
    assert ("aggregate_cart_gap_is_channel_mix" in reasons) is mix


def test_opportunity_counts_only_positive_gaps_and_scales_the_sample(contract):
    con = runner.connect()
    con.execute("SET VARIABLE months = 2.0")
    con.execute("SET VARIABLE sample_rate = 0.5")
    con.execute(
        "CREATE TABLE cmh_strata AS SELECT * FROM (VALUES "
        "('purchase_given_checkout', 'email', 10, 10, 15, 5), ('purchase_given_checkout', 'organic', 4, 1, 6, 4)) "
        "AS t (step, channel, a, b, c, d)"
    )
    con.execute("CREATE TABLE order_value_by_device AS SELECT 'mobile' AS device, 2000.0 AS mean_inr")
    con.execute("CREATE TABLE funnel_by_device AS SELECT 'mobile' AS device, 1000000 AS revenue_paise")
    sql = runner.SQL_DIR.joinpath("05_answers.sql").read_text(encoding="utf-8")
    con.execute(sql[: sql.index("CREATE OR REPLACE VIEW decision")])
    gaps = con.execute("SELECT channel, gap, extra_orders FROM opportunity_by_channel ORDER BY channel").fetchall()
    assert [g[1] for g in gaps] == [pytest.approx(0.25), 0.0]  # organic: mobile is better
    opp = con.execute("SELECT * FROM opportunity").fetchone()
    assert opp[0] == pytest.approx(20 * 0.25)  # extra orders in sample
    assert opp[1:] == (pytest.approx(5 / 2 / 0.5), 2000.0, pytest.approx(5 * 2000), pytest.approx(10_000 / 2 / 0.5))
