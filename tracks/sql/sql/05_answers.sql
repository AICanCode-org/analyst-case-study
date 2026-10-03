-- M5 · Opportunity and decision (contract/questions.md §5).
-- Variables: months, sample_rate, alpha, rebuild_min_monthly_uplift_inr.

CREATE OR REPLACE VIEW opportunity_by_channel AS
SELECT
    channel,
    greatest(0, c / (c + d) - a / (a + b)) AS gap,
    (a + b) * greatest(0, c / (c + d) - a / (a + b)) AS extra_orders
FROM cmh_strata
WHERE step = 'purchase_given_checkout'
ORDER BY channel;

CREATE OR REPLACE VIEW opportunity AS
WITH base AS (
    SELECT
        (SELECT sum(extra_orders) FROM opportunity_by_channel) AS extra_orders_in_sample,
        (SELECT mean_inr FROM order_value_by_device WHERE device = 'mobile') AS mobile_aov_inr,
        (SELECT revenue_paise FROM funnel_by_device WHERE device = 'mobile') AS mobile_revenue_paise
)
SELECT
    extra_orders_in_sample,
    extra_orders_in_sample / getvariable('months') / getvariable('sample_rate') AS extra_orders_per_month,
    mobile_aov_inr,
    extra_orders_in_sample / getvariable('months') / getvariable('sample_rate') * mobile_aov_inr
        AS monthly_revenue_uplift_inr,
    mobile_revenue_paise / 100 / getvariable('months') / getvariable('sample_rate') AS mobile_monthly_revenue_inr
FROM base;

CREATE OR REPLACE VIEW decision AS
WITH inputs AS (
    SELECT
        (SELECT p_value FROM cmh WHERE step = 'purchase_given_checkout') AS pay_p,
        (SELECT p_value FROM cmh WHERE step = 'cart_given_view') AS cart_p,
        (SELECT odds_ratio_mh FROM cmh WHERE step = 'cart_given_view') AS cart_or,
        (SELECT aggregate_gap FROM simpson) AS cart_gap,
        (SELECT monthly_revenue_uplift_inr FROM opportunity) AS uplift
),
base AS (
    SELECT
        *,
        CASE
            WHEN pay_p >= getvariable('alpha') THEN 'no_checkout_gap_found'
            WHEN uplift >= getvariable('rebuild_min_monthly_uplift_inr') THEN 'rebuild_checkout'
            ELSE 'run_targeted_experiment'
        END AS recommendation
    FROM inputs
)
SELECT
    recommendation,
    CASE recommendation
        WHEN 'no_checkout_gap_found' THEN ['adjusted_payment_gap_not_significant']
        WHEN 'rebuild_checkout' THEN ['adjusted_payment_gap_significant', 'uplift_above_rebuild_threshold']
        ELSE ['adjusted_payment_gap_significant', 'uplift_below_rebuild_threshold']
    END
    || CASE
        WHEN cart_gap < 0 AND (cart_p >= getvariable('alpha') OR cart_or >= 1) THEN ['aggregate_cart_gap_is_channel_mix']
        ELSE []
    END AS reasons
FROM base;
