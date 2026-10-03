-- M1 · Clean: the rules of contract/questions.md §2, in order, each step a view you can query.
-- Variables set by the runner: period_start, period_end (DATE); contract lists are loaded into
-- the tables cfg_devices, cfg_channels, cfg_unknown_channels, cfg_steps, cfg_city_aliases.

-- users ---------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE users AS
-- TODO(M1) users: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

-- sessions ------------------------------------------------------------------------------------
CREATE OR REPLACE VIEW s1_normalised AS
-- TODO(M1) s1_normalised: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW s2_parsed AS
-- TODO(M1) s2_parsed: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW s3_deduplicated AS
-- TODO(M1) s3_deduplicated: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW s4_consistent AS
-- TODO(M1) s4_consistent: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW s5_in_period AS
-- TODO(M1) s5_in_period: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE TABLE sessions AS
-- TODO(M1) sessions: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

-- events --------------------------------------------------------------------------------------
CREATE OR REPLACE VIEW e1_known AS
-- TODO(M1) e1_known: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW e2_attached AS
-- TODO(M1) e2_attached: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE TABLE events AS
-- TODO(M1) events: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

-- orders --------------------------------------------------------------------------------------
CREATE OR REPLACE VIEW o1_distinct AS
-- TODO(M1) o1_distinct: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW o2_parsed AS
-- TODO(M1) o2_parsed: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW o3_positive AS
-- TODO(M1) o3_positive: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

CREATE OR REPLACE TABLE orders AS
-- TODO(M1) orders: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;

-- issue counts (contract/questions.md §2), one row per issue --------------------------------------
CREATE OR REPLACE TABLE issues AS
-- TODO(M1) issues: contract/questions.md §2; tests: tests/unit/test_clean.py
SELECT NULL AS todo;
