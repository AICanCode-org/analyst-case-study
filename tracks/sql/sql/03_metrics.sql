-- M3 · Metrics: the session funnel and its aggregates (contract/questions.md §3).

CREATE OR REPLACE TABLE session_funnel AS
-- TODO(M3) session_funnel: contract/questions.md §3; tests: tests/unit/test_metrics.py
SELECT NULL AS todo;

-- counts per device (and 'all'), with revenue from every clean order of those sessions
CREATE OR REPLACE VIEW funnel_by_device AS
-- TODO(M3) funnel_by_device: contract/questions.md §3; tests: tests/unit/test_metrics.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW funnel_by_channel AS
-- TODO(M3) funnel_by_channel: contract/questions.md §3; tests: tests/unit/test_metrics.py
SELECT NULL AS todo;

-- every channel x device pair, also the empty ones (a channel seen on one device only)
CREATE OR REPLACE VIEW channel_device_grid AS
-- TODO(M3) channel_device_grid: contract/questions.md §3; tests: tests/unit/test_metrics.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW weekly AS
-- TODO(M3) weekly: contract/questions.md §3; tests: tests/unit/test_metrics.py
SELECT NULL AS todo;
