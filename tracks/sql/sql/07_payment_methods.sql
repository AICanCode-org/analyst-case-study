-- v1.1 · Clean orders per payment method and device. The runner runs this file only when the export
-- has a payment_method column (exports from 2026-08); otherwise answers.payment_methods is null.
CREATE OR REPLACE VIEW payment_methods AS
SELECT
    s.device,
    coalesce(nullif(lower(trim(o.payment_method)), ''), 'unknown') AS method,
    count(*) AS orders
FROM orders AS o
INNER JOIN sessions AS s ON o.session_id = s.session_id
GROUP BY ALL
ORDER BY s.device, method;
