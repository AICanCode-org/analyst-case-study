-- M4 · Statistics (contract/questions.md §4), mobile = group 1, desktop = group 2.
-- SQL has no normal or Student-t distribution, so the runner registers three scalar functions:
--   erfc(x), t_two_sided_p(t, df), t_quantile(p, df)   (funnellens_sql/mathfn.py, standard library)
-- Everything else (sums, variances, test statistics, intervals) is computed here.

-- Q3: payment step, two proportions ------------------------------------------------------------
CREATE OR REPLACE VIEW payment_step_test AS
-- TODO(M4) payment_step_test: contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: tests/unit/test_stats.py
SELECT NULL AS todo;

-- Q4: Cochran-Mantel-Haenszel per step -----------------------------------------------------------
CREATE OR REPLACE VIEW cmh_strata AS
-- TODO(M4) cmh_strata: contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: tests/unit/test_stats.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW cmh AS
-- TODO(M4) cmh: contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: tests/unit/test_stats.py
SELECT NULL AS todo;

-- Q4: Simpson check on the cart step -------------------------------------------------------------
CREATE OR REPLACE VIEW simpson_gaps AS
-- TODO(M4) simpson_gaps: contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: tests/unit/test_stats.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW simpson AS
-- TODO(M4) simpson: contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: tests/unit/test_stats.py
SELECT NULL AS todo;

-- Q5: Welch t test on order values (rupees) --------------------------------------------------------
CREATE OR REPLACE VIEW order_value_by_device AS
-- TODO(M4) order_value_by_device: contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: tests/unit/test_stats.py
SELECT NULL AS todo;

CREATE OR REPLACE VIEW welch AS
-- TODO(M4) welch: contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: tests/unit/test_stats.py
SELECT NULL AS todo;
