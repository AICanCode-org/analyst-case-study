-- M1 · Clean: the rules of contract/questions.md §2, in order, each step a view you can query.
-- Variables set by the runner: period_start, period_end (DATE); contract lists are loaded into
-- the tables cfg_devices, cfg_channels, cfg_unknown_channels, cfg_steps, cfg_city_aliases.

-- users ---------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE users AS
SELECT
    CAST(trim(u.user_id) AS BIGINT) AS user_id,
    nullif(trim(u.signup_channel), '') AS signup_channel,
    coalesce(a.canonical, lower(trim(u.city))) AS city
FROM raw_users AS u
LEFT JOIN cfg_city_aliases AS a ON a.alias = lower(trim(u.city));

-- sessions ------------------------------------------------------------------------------------
CREATE OR REPLACE VIEW s1_normalised AS
SELECT
    trim(session_id) AS session_id,
    trim(user_id) AS user_id,
    lower(trim(device)) AS device,
    CASE
        WHEN lower(trim(channel)) IN (SELECT value FROM cfg_unknown_channels) THEN 'unknown'
        ELSE lower(trim(channel))
    END AS channel,
    CASE
        WHEN regexp_full_match(trim(started_at), '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
            THEN try_strptime(trim(started_at), '%Y-%m-%d %H:%M:%S')
        WHEN regexp_full_match(trim(started_at), '\d{2}/\d{2}/\d{4} \d{2}:\d{2}')
            THEN try_strptime(trim(started_at), '%d/%m/%Y %H:%M')
    END AS started_at
FROM raw_sessions;

CREATE OR REPLACE VIEW s2_parsed AS
SELECT * FROM s1_normalised WHERE started_at IS NOT NULL;

CREATE OR REPLACE VIEW s3_deduplicated AS
SELECT DISTINCT * FROM s2_parsed;

CREATE OR REPLACE VIEW s4_consistent AS
SELECT * FROM s3_deduplicated
WHERE session_id IN (SELECT session_id FROM s3_deduplicated GROUP BY session_id HAVING count(*) = 1);

CREATE OR REPLACE VIEW s5_in_period AS
SELECT * FROM s4_consistent
WHERE CAST(started_at AS DATE) BETWEEN getvariable('period_start') AND getvariable('period_end');

CREATE OR REPLACE VIEW s6_known_user AS
SELECT
    s.session_id,
    CAST(s.user_id AS BIGINT) AS user_id,
    s.device,
    s.channel,
    s.started_at,
    isoyear(s.started_at) || '-W' || lpad(CAST(week(s.started_at) AS VARCHAR), 2, '0') AS week,
    strftime(s.started_at, '%Y-%m') AS month
FROM s5_in_period AS s
WHERE CAST(s.user_id AS BIGINT) IN (SELECT user_id FROM users);

-- v1.1: weeks with known-broken tracking are not analysed (contract cleaning.exclude_weeks)
CREATE OR REPLACE TABLE sessions AS
SELECT * FROM s6_known_user
WHERE week NOT IN (SELECT value FROM cfg_exclude_weeks)
ORDER BY session_id;

-- events --------------------------------------------------------------------------------------
CREATE OR REPLACE VIEW e1_known AS
SELECT
    trim(session_id) AS session_id,
    lower(trim(event_name)) AS event_name,
    try_strptime(trim(event_at), '%Y-%m-%d %H:%M:%S') AS event_at
FROM raw_events
WHERE lower(trim(event_name)) IN (SELECT value FROM cfg_steps);

CREATE OR REPLACE VIEW e2_attached AS
SELECT * FROM e1_known WHERE session_id IN (SELECT session_id FROM sessions);

CREATE OR REPLACE TABLE events AS
SELECT session_id, event_name, min(event_at) AS first_at
FROM e2_attached
GROUP BY session_id, event_name
ORDER BY session_id, event_name;

-- orders --------------------------------------------------------------------------------------
CREATE OR REPLACE VIEW o1_distinct AS
SELECT DISTINCT * FROM raw_orders;

CREATE OR REPLACE VIEW o2_parsed AS
WITH stripped AS (
    SELECT
        *,
        replace(replace(replace(replace(trim(amount), '₹', ''), 'Rs.', ''), ',', ''), ' ', '') AS amount_text
    FROM o1_distinct
)
SELECT
    * EXCLUDE (amount_text),
    CASE
        WHEN regexp_full_match(amount_text, '-?\d+(\.\d{1,2})?')
            THEN (CASE WHEN starts_with(amount_text, '-') THEN -1 ELSE 1 END)
            * (
                CAST(regexp_extract(amount_text, '(\d+)', 1) AS BIGINT) * 100
                + CAST(rpad(coalesce(nullif(regexp_extract(amount_text, '\.(\d{1,2})$', 1), ''), '0'), 2, '0') AS BIGINT)
            )
    END AS amount_paise
FROM stripped;

CREATE OR REPLACE VIEW o3_positive AS
SELECT * FROM o2_parsed WHERE amount_paise > 0;

CREATE OR REPLACE TABLE orders AS
SELECT
    trim(order_id) AS order_id,
    trim(session_id) AS session_id,
    amount_paise,
    * EXCLUDE (order_id, session_id, amount, amount_paise)
FROM o3_positive
WHERE trim(session_id) IN (SELECT session_id FROM sessions)
ORDER BY order_id;

-- issue counts (contract/questions.md §2), one row per issue --------------------------------------
CREATE OR REPLACE TABLE issues AS
WITH steps AS (
    SELECT session_id, event_name, first_at FROM events
),
out_of_order AS (
    SELECT count(DISTINCT v.session_id) AS n
    FROM steps AS v
    JOIN steps AS c ON c.session_id = v.session_id
    WHERE (v.event_name = 'view' AND c.event_name = 'cart' AND c.first_at < v.first_at)
       OR (v.event_name = 'cart' AND c.event_name = 'checkout' AND c.first_at < v.first_at)
)
SELECT * FROM (VALUES
    (1, 'sessions_bad_timestamp', (SELECT count(*) FROM s1_normalised) - (SELECT count(*) FROM s2_parsed)),
    (2, 'sessions_exact_duplicates', (SELECT count(*) FROM s2_parsed) - (SELECT count(*) FROM s3_deduplicated)),
    (3, 'sessions_conflicting_ids', (SELECT count(DISTINCT session_id) FROM s3_deduplicated)
        - (SELECT count(*) FROM s4_consistent)),
    (4, 'sessions_out_of_period', (SELECT count(*) FROM s4_consistent) - (SELECT count(*) FROM s5_in_period)),
    (5, 'sessions_orphan_user', (SELECT count(*) FROM s5_in_period) - (SELECT count(*) FROM s6_known_user)),
    (6, 'sessions_unknown_channel', (SELECT count(*) FROM sessions WHERE channel = 'unknown')),
    (7, 'users_missing_signup_channel', (SELECT count(*) FROM users WHERE signup_channel IS NULL)),
    (8, 'users_city_variants_merged', (SELECT count(DISTINCT city) FROM raw_users) - (SELECT count(DISTINCT city) FROM users)),
    (9, 'events_unknown_name', (SELECT count(*) FROM raw_events) - (SELECT count(*) FROM e1_known)),
    (10, 'events_orphan_session', (SELECT count(*) FROM e1_known) - (SELECT count(*) FROM e2_attached)),
    (11, 'events_repeated_steps', (SELECT count(*) FROM e2_attached) - (SELECT count(*) FROM events)),
    (12, 'sessions_out_of_order', (SELECT n FROM out_of_order)),
    (13, 'orders_exact_duplicates', (SELECT count(*) FROM raw_orders) - (SELECT count(*) FROM o1_distinct)),
    (14, 'orders_unparseable_amount', (SELECT count(*) FROM o2_parsed WHERE amount_paise IS NULL)),
    (15, 'orders_non_positive_amount', (SELECT count(*) FROM o2_parsed WHERE amount_paise <= 0)),
    (16, 'orders_orphan_session', (SELECT count(*) FROM o3_positive) - (SELECT count(*) FROM orders)),
    (17, 'orders_without_checkout', (
        SELECT count(*) FROM orders
        WHERE session_id NOT IN (SELECT session_id FROM events WHERE event_name = 'checkout')
    )),
    (18, 'sessions_excluded_week', (SELECT count(*) FROM s6_known_user) - (SELECT count(*) FROM sessions))
) AS t (position, issue, n)
ORDER BY position;
