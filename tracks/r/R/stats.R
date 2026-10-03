# M4: the three hypothesis tests of contract/questions.md section 4, with base R's stats package.
# The tests in tests/testthat/test-stats.R pin them to contract/fixtures/stats-cases.json.

#' Group 1 vs group 2: pooled z test (two-sided) and the unpooled Wald 95 % interval of p1 - p2.
two_proportion <- function(x1, n1, x2, n2, z_975) {
  # TODO(M4) two_proportion: pooled z test for the difference of two proportions + an unpooled 95% CI. Check
  # every value against stats-cases.json. Spec: contract/questions.md §4 (+ contract/fixtures/stats-cases.json);
  # tests: stats.
  stop("TODO(M4) two_proportion: see the comment above")
}

#' Cochran-Mantel-Haenszel test without continuity correction. `strata` is a list of
#' c(a, b, c, d) = (group-1 successes, group-1 failures, group-2 successes, group-2 failures).
cmh_test <- function(strata, z_975) {
  # TODO(M4) cmh_test: Cochran-Mantel-Haenszel over the channel strata: the Mantel-Haenszel odds ratio, its
  # Robins-Breslow-Greenland CI and the CMH chi-square p value (no continuity correction). Spec:
  # contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: stats.
  stop("TODO(M4) cmh_test: see the comment above")
}

#' Welch's unequal-variance t test (two-sided) and the 95 % interval of mean(x) - mean(y).
welch_test <- function(x, y) {
  # TODO(M4) welch_test: Welch's t test (unequal variances) with the Welch-Satterthwaite df and a 95% CI of the
  # difference. Spec: contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: stats.
  stop("TODO(M4) welch_test: see the comment above")
}
