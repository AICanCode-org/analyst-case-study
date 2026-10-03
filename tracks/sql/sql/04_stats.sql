-- M4 · Statistics (contract/questions.md §4), mobile = group 1, desktop = group 2.
-- SQL has no normal or Student-t distribution, so the runner registers three scalar functions:
--   erfc(x), t_two_sided_p(t, df), t_quantile(p, df)   (funnellens_sql/mathfn.py, standard library)
-- Everything else (sums, variances, test statistics, intervals) is computed here.

-- Q3: payment step, two proportions ------------------------------------------------------------
CREATE OR REPLACE VIEW payment_step_test AS
WITH g AS (
    SELECT
        max(purchase) FILTER (WHERE device = 'mobile') AS x1,
        max(checkout) FILTER (WHERE device = 'mobile') AS n1,
        max(purchase) FILTER (WHERE device = 'desktop') AS x2,
        max(checkout) FILTER (WHERE device = 'desktop') AS n2
    FROM funnel_by_device
),
r AS (
    SELECT
        *,
        x1 / n1 AS p1,
        x2 / n2 AS p2,
        (x1 + x2) / (n1 + n2) AS pooled
    FROM g
),
z AS (
    SELECT
        *,
        (p1 - p2) / sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2)) AS z,
        sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2) AS se
    FROM r
)
SELECT
    n1, x1, p1, n2, x2, p2,
    p1 - p2 AS difference,
    p1 - p2 - getvariable('z_975') * se AS ci_low,
    p1 - p2 + getvariable('z_975') * se AS ci_high,
    z,
    erfc(abs(z) / sqrt(2)) AS p_value
FROM z;

-- Q4: Cochran-Mantel-Haenszel per step -----------------------------------------------------------
CREATE OR REPLACE VIEW cmh_strata AS
WITH grid AS (
    SELECT
        channel,
        max(cart) FILTER (WHERE device = 'mobile') AS m_cart,
        max(view) FILTER (WHERE device = 'mobile') AS m_view,
        max(purchase) FILTER (WHERE device = 'mobile') AS m_purchase,
        max(checkout) FILTER (WHERE device = 'mobile') AS m_checkout,
        max(cart) FILTER (WHERE device = 'desktop') AS d_cart,
        max(view) FILTER (WHERE device = 'desktop') AS d_view,
        max(purchase) FILTER (WHERE device = 'desktop') AS d_purchase,
        max(checkout) FILTER (WHERE device = 'desktop') AS d_checkout
    FROM channel_device_grid
    GROUP BY channel
)
SELECT 'cart_given_view' AS step, channel,
    m_cart AS a, m_view - m_cart AS b, d_cart AS c, d_view - d_cart AS d
FROM grid WHERE m_view > 0 AND d_view > 0
UNION ALL
SELECT 'purchase_given_checkout', channel,
    m_purchase, m_checkout - m_purchase, d_purchase, d_checkout - d_purchase
FROM grid WHERE m_checkout > 0 AND d_checkout > 0
ORDER BY step, channel;

CREATE OR REPLACE VIEW cmh AS
WITH t AS (
    SELECT
        step, channel,
        CAST(a AS DOUBLE) AS a, CAST(b AS DOUBLE) AS b, CAST(c AS DOUBLE) AS c, CAST(d AS DOUBLE) AS d,
        CAST(a + b + c + d AS DOUBLE) AS n
    FROM cmh_strata
),
terms AS (
    SELECT
        *,
        (a + b) * (a + c) / n AS e,
        (a + b) * (c + d) * (a + c) * (b + d) / (n * n * (n - 1)) AS v,
        a * d / n AS r,
        b * c / n AS s,
        (a + d) / n AS p,
        (b + c) / n AS q
    FROM t
),
sums AS (
    SELECT
        step,
        count(*) AS strata,
        sum(a) AS sa, sum(b) AS sb, sum(c) AS sc, sum(d) AS sd,
        sum(e) AS se, sum(v) AS sv, sum(r) AS sr, sum(s) AS ss,
        sum(p * r) AS spr, sum(p * s + q * r) AS spsqr, sum(q * s) AS sqs
    FROM terms
    GROUP BY step
),
stat AS (
    SELECT
        *,
        (sa - se) ^ 2 / sv AS statistic,
        sr / ss AS odds_ratio_mh,
        spr / (2 * sr ^ 2) + spsqr / (2 * sr * ss) + sqs / (2 * ss ^ 2) AS var_log_or
    FROM sums
)
SELECT
    step,
    statistic,
    erfc(sqrt(statistic / 2)) AS p_value,
    odds_ratio_mh,
    exp(ln(odds_ratio_mh) - getvariable('z_975') * sqrt(var_log_or)) AS ci_low,
    exp(ln(odds_ratio_mh) + getvariable('z_975') * sqrt(var_log_or)) AS ci_high,
    sa * sd / (sb * sc) AS crude_odds_ratio,
    strata
FROM stat
ORDER BY step;

-- Q4: Simpson check on the cart step -------------------------------------------------------------
CREATE OR REPLACE VIEW simpson_gaps AS
SELECT channel, a / (a + b) - c / (c + d) AS gap
FROM cmh_strata
WHERE step = 'cart_given_view'
ORDER BY channel;

CREATE OR REPLACE VIEW simpson AS
WITH agg AS (
    SELECT
        max(rate_cart) FILTER (WHERE device = 'mobile') - max(rate_cart) FILTER (WHERE device = 'desktop') AS gap
    FROM funnel_by_device
)
SELECT
    agg.gap AS aggregate_gap,
    (agg.gap < 0 AND (SELECT bool_and(gap > 0) FROM simpson_gaps))
    OR (agg.gap > 0 AND (SELECT bool_and(gap < 0) FROM simpson_gaps)) AS reversal
FROM agg;

-- Q5: Welch t test on order values (rupees) --------------------------------------------------------
CREATE OR REPLACE VIEW order_value_by_device AS
SELECT
    s.device,
    count(*) AS orders,
    avg(o.amount_paise / 100) AS mean_inr,
    stddev_samp(o.amount_paise / 100) AS sd_inr,
    var_samp(o.amount_paise / 100) AS var_inr
FROM orders AS o
JOIN sessions AS s USING (session_id)
GROUP BY s.device
ORDER BY s.device;

CREATE OR REPLACE VIEW welch AS
WITH g AS (
    SELECT
        max(mean_inr) FILTER (WHERE device = 'mobile') AS m1,
        max(var_inr) FILTER (WHERE device = 'mobile') / max(orders) FILTER (WHERE device = 'mobile') AS q1,
        max(orders) FILTER (WHERE device = 'mobile') AS n1,
        max(mean_inr) FILTER (WHERE device = 'desktop') AS m2,
        max(var_inr) FILTER (WHERE device = 'desktop') / max(orders) FILTER (WHERE device = 'desktop') AS q2,
        max(orders) FILTER (WHERE device = 'desktop') AS n2
    FROM order_value_by_device
),
t AS (
    SELECT
        m1 - m2 AS difference,
        sqrt(q1 + q2) AS se,
        (q1 + q2) ^ 2 / (q1 ^ 2 / (n1 - 1) + q2 ^ 2 / (n2 - 1)) AS df
    FROM g
)
SELECT
    difference,
    difference / se AS t,
    df,
    t_two_sided_p(difference / se, df) AS p_value,
    difference - t_quantile(0.975, df) * se AS ci_low,
    difference + t_quantile(0.975, df) * se AS ci_high
FROM t;
