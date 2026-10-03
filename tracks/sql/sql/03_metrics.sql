-- M3 · Metrics: the session funnel and its aggregates (contract/questions.md §3).

CREATE OR REPLACE TABLE session_funnel AS
WITH has AS (
    SELECT
        session_id,
        bool_or(event_name = 'view') AS has_view,
        bool_or(event_name = 'cart') AS has_cart,
        bool_or(event_name = 'checkout') AS has_checkout
    FROM events
    GROUP BY session_id
),
flags AS (
    SELECT
        s.session_id, s.device, s.channel, s.week, s.month,
        coalesce(h.has_view, false) AS view,
        coalesce(h.has_view AND h.has_cart, false) AS cart,
        coalesce(h.has_view AND h.has_cart AND h.has_checkout, false) AS checkout
    FROM sessions AS s
    LEFT JOIN has AS h USING (session_id)
)
SELECT
    f.*,
    f.checkout AND f.session_id IN (SELECT session_id FROM orders) AS purchase
FROM flags AS f
ORDER BY f.session_id;

-- counts per device (and 'all'), with revenue from every clean order of those sessions
CREATE OR REPLACE VIEW funnel_by_device AS
WITH per_device AS (
    SELECT
        coalesce(device, 'all') AS device,
        count(*) AS sessions,
        count(*) FILTER (WHERE view) AS view,
        count(*) FILTER (WHERE cart) AS cart,
        count(*) FILTER (WHERE checkout) AS checkout,
        count(*) FILTER (WHERE purchase) AS purchase
    FROM session_funnel
    GROUP BY ROLLUP (device)
),
revenue AS (
    SELECT coalesce(s.device, 'all') AS device, sum(o.amount_paise) AS revenue_paise
    FROM orders AS o JOIN sessions AS s USING (session_id)
    GROUP BY ROLLUP (s.device)
),
devices AS (  -- every contract device appears, even with no sessions (its rates are then NULL)
    SELECT value AS device FROM cfg_devices
    UNION ALL
    SELECT 'all'
),
filled AS (
    SELECT
        v.device,
        coalesce(d.sessions, 0) AS sessions,
        coalesce(d.view, 0) AS view,
        coalesce(d.cart, 0) AS cart,
        coalesce(d.checkout, 0) AS checkout,
        coalesce(d.purchase, 0) AS purchase
    FROM devices AS v
    LEFT JOIN per_device AS d USING (device)
)
SELECT
    d.*,
    coalesce(r.revenue_paise, 0) AS revenue_paise,
    d.purchase / nullif(d.sessions, 0) AS conversion,
    d.view / nullif(d.sessions, 0) AS rate_view,
    d.cart / nullif(d.view, 0) AS rate_cart,
    d.checkout / nullif(d.cart, 0) AS rate_checkout,
    d.purchase / nullif(d.checkout, 0) AS rate_purchase
FROM filled AS d
LEFT JOIN revenue AS r USING (device)
ORDER BY d.device;

CREATE OR REPLACE VIEW funnel_by_channel AS
SELECT
    channel,
    device,
    count(*) AS sessions,
    count(*) FILTER (WHERE view) AS view,
    count(*) FILTER (WHERE cart) AS cart,
    count(*) FILTER (WHERE checkout) AS checkout,
    count(*) FILTER (WHERE purchase) AS purchase
FROM session_funnel
GROUP BY channel, device
ORDER BY channel, device;

-- every channel x device pair, also the empty ones (a channel seen on one device only)
CREATE OR REPLACE VIEW channel_device_grid AS
SELECT
    c.channel,
    d.device,
    coalesce(f.sessions, 0) AS sessions,
    coalesce(f.view, 0) AS view,
    coalesce(f.cart, 0) AS cart,
    coalesce(f.checkout, 0) AS checkout,
    coalesce(f.purchase, 0) AS purchase
FROM (SELECT DISTINCT channel FROM session_funnel) AS c
CROSS JOIN (SELECT value AS device FROM cfg_devices) AS d
LEFT JOIN funnel_by_channel AS f USING (channel, device)
ORDER BY c.channel, d.device;

CREATE OR REPLACE VIEW weekly AS
SELECT
    week,
    count(*) FILTER (WHERE device = 'desktop') AS sessions_desktop,
    count(*) FILTER (WHERE device = 'mobile') AS sessions_mobile,
    count(*) FILTER (WHERE device = 'desktop' AND purchase) AS purchases_desktop,
    count(*) FILTER (WHERE device = 'mobile' AND purchase) AS purchases_mobile
FROM session_funnel
GROUP BY week
ORDER BY week;
