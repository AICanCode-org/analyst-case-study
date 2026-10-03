-- v1.1 · Data-quality monitoring (contract/questions.md §6). It reports; it never stops the run.
-- Variables: period_start, period_end, max_relative_deviation, max_days_behind.

CREATE OR REPLACE VIEW freshness AS
SELECT
    getvariable('period_end') AS period_end,
    max(CAST(started_at AS DATE)) AS last_session_date,
    datediff('day', max(CAST(started_at AS DATE)), getvariable('period_end')) AS days_behind,
    datediff('day', max(CAST(started_at AS DATE)), getvariable('period_end')) > getvariable('max_days_behind') AS stale
FROM sessions;

-- full ISO weeks only: Monday on or after period_start, Sunday on or before period_end
CREATE OR REPLACE VIEW monitoring_weeks AS
WITH f AS (
    SELECT
        sf.week,
        sf.device,
        sf.cart,
        sf.checkout,
        CAST(date_trunc('week', s.started_at) AS DATE) AS monday
    FROM session_funnel AS sf
    INNER JOIN sessions AS s ON sf.session_id = s.session_id
)
SELECT
    week,
    count(*) AS sessions,
    count(*) FILTER (WHERE device = 'mobile' AND checkout)
    / nullif(count(*) FILTER (WHERE device = 'mobile' AND cart), 0) AS mobile_checkout_given_cart
FROM f
WHERE monday >= getvariable('period_start') AND monday + INTERVAL 6 DAY <= getvariable('period_end')
GROUP BY week
ORDER BY week;

-- median() interpolates for an even count (the mean of the two middle values) and ignores NULLs
CREATE OR REPLACE VIEW monitoring_medians AS
SELECT
    CAST(median(sessions) AS DOUBLE) AS sessions,
    median(mobile_checkout_given_cart) AS mobile_checkout_given_cart
FROM monitoring_weeks;

CREATE OR REPLACE VIEW monitoring_anomalies AS
WITH long AS (
    SELECT w.week, 1 AS metric_order, 'sessions' AS metric, CAST(w.sessions AS DOUBLE) AS value, m.sessions AS median
    FROM monitoring_weeks AS w CROSS JOIN monitoring_medians AS m
    UNION ALL
    SELECT
        w.week,
        2 AS metric_order,
        'mobile_checkout_given_cart' AS metric,
        w.mobile_checkout_given_cart AS value,
        m.mobile_checkout_given_cart AS median
    FROM monitoring_weeks AS w CROSS JOIN monitoring_medians AS m
)
SELECT week, metric, value, median, (value - median) / median AS deviation
FROM long
WHERE
    value IS NOT NULL AND median IS NOT NULL AND median <> 0
    AND abs((value - median) / median) > getvariable('max_relative_deviation')
ORDER BY week, metric_order;
