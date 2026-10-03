skip_if_pending("test-unit-stats.R")

expect_close <- function(got, want, key) expect_equal(got, nums(want), tolerance = 1e-9, info = key)

test_that("two proportions match the shared reference cases", {
  for (case in STATS_CASES$two_proportion) {
    got <- two_proportion(case$x1, case$n1, case$x2, case$n2, Z)
    for (key in c("difference", "z", "p_value", "ci95")) expect_close(got[[key]], case[[key]], key)
  }
})

test_that("two proportions by hand", {
  # 3/10 vs 7/10: pooled p = 0.5, se0 = sqrt(0.25 * 0.2) = 0.2236..., z = -0.4 / 0.2236 = -1.7889
  got <- two_proportion(3, 10, 7, 10, Z)
  expect_equal(got$z, -1.788854382, tolerance = 1e-9)
  expect_equal(got$difference, -0.4)
  expect_true(got$ci95[1] < -0.4 && -0.4 < got$ci95[2])
})

test_that("CMH matches the shared reference cases", {
  for (case in STATS_CASES$cmh) {
    got <- cmh_test(lapply(case$tables, nums), Z)
    for (key in c("statistic", "p_value", "odds_ratio_mh", "ci95", "crude_odds_ratio")) {
      expect_close(got[[key]], case[[key]], key)
    }
    expect_identical(got$strata, length(case$tables))
  }
})

test_that("CMH with identical strata equals the single-table odds ratio", {
  got <- cmh_test(list(c(20, 80, 10, 90), c(20, 80, 10, 90)), Z)
  expect_equal(got$odds_ratio_mh, (20 * 90) / (80 * 10))
  expect_equal(got$crude_odds_ratio, got$odds_ratio_mh)
})

test_that("Welch matches the shared reference cases", {
  for (case in STATS_CASES$welch) {
    got <- welch_test(nums(case$x), nums(case$y))
    for (key in c("difference", "t", "df", "p_value", "ci95")) expect_close(got[[key]], case[[key]], key)
  }
})

test_that("Welch with no difference", {
  got <- welch_test(c(1, 2, 3), c(1, 2, 3))
  expect_identical(got$t, 0)
  expect_equal(got$p_value, 1)
})
