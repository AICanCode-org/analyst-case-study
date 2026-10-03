-- M1 · Load: every raw CSV as text, exactly as exported (empty cells become '' rather than NULL).
-- The runner sets the variable data_dir (SET VARIABLE data_dir = '.../data/raw/2026-06').

CREATE OR REPLACE TABLE raw_users AS
SELECT
    * REPLACE (
        coalesce(user_id, '') AS user_id, coalesce(signup_date, '') AS signup_date,
        coalesce(signup_channel, '') AS signup_channel, coalesce(city, '') AS city
    )
FROM read_csv(getvariable('data_dir') || '/users.csv', header = true, all_varchar = true, delim = ',', quote = '"');

CREATE OR REPLACE TABLE raw_sessions AS
SELECT
    * REPLACE (
        coalesce(session_id, '') AS session_id, coalesce(user_id, '') AS user_id, coalesce(device, '') AS device,
        coalesce(channel, '') AS channel, coalesce(started_at, '') AS started_at
    )
FROM read_csv(getvariable('data_dir') || '/sessions.csv', header = true, all_varchar = true, delim = ',', quote = '"');

CREATE OR REPLACE TABLE raw_events AS
SELECT
    * REPLACE (
        coalesce(session_id, '') AS session_id, coalesce(event_name, '') AS event_name, coalesce(event_at, '') AS event_at
    )
FROM read_csv(getvariable('data_dir') || '/events.csv', header = true, all_varchar = true, delim = ',', quote = '"');

CREATE OR REPLACE TABLE raw_orders AS
SELECT
    * REPLACE (
        coalesce(order_id, '') AS order_id, coalesce(session_id, '') AS session_id, coalesce(amount, '') AS amount
    )
FROM read_csv(getvariable('data_dir') || '/orders.csv', header = true, all_varchar = true, delim = ',', quote = '"');
