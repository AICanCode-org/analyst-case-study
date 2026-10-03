# M4: the three hypothesis tests of contract/questions.md section 4, with base R's stats package.
# The tests in tests/testthat/test-stats.R pin them to contract/fixtures/stats-cases.json.

#' Group 1 vs group 2: pooled z test (two-sided) and the unpooled Wald 95 % interval of p1 - p2.
two_proportion <- function(x1, n1, x2, n2, z_975) {
  res <- stats::prop.test(c(x1, x2), c(n1, n2), correct = FALSE)
  p1 <- x1 / n1
  p2 <- x2 / n2
  diff <- p1 - p2
  se <- sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
  # prop.test reports chi-square = z^2; the sign of z is the sign of the difference
  list(difference = diff, ci95 = c(diff - z_975 * se, diff + z_975 * se),
       z = sign(diff) * sqrt(unname(res$statistic)), p_value = res$p.value)
}

#' Cochran-Mantel-Haenszel test without continuity correction. `strata` is a list of
#' c(a, b, c, d) = (group-1 successes, group-1 failures, group-2 successes, group-2 failures).
cmh_test <- function(strata, z_975) {
  k <- length(strata)
  tables <- array(as.numeric(unlist(lapply(strata, function(t) c(t[1], t[3], t[2], t[4])))), dim = c(2, 2, k))
  res <- stats::mantelhaen.test(tables, correct = FALSE)
  # mantelhaen.test's interval uses qnorm(0.975); recompute with the contract's z so every track agrees
  r <- vapply(strata, function(t) t[1] * t[4] / sum(t), 0)
  s <- vapply(strata, function(t) t[2] * t[3] / sum(t), 0)
  p <- vapply(strata, function(t) (t[1] + t[4]) / sum(t), 0)
  q <- vapply(strata, function(t) (t[2] + t[3]) / sum(t), 0)
  v <- sum(p * r) / (2 * sum(r)^2) + sum(p * s + q * r) / (2 * sum(r) * sum(s)) + sum(q * s) / (2 * sum(s)^2)
  or <- unname(res$estimate)
  totals <- Reduce(`+`, strata)
  list(statistic = unname(res$statistic), p_value = res$p.value, odds_ratio_mh = or,
       ci95 = exp(log(or) + c(-1, 1) * z_975 * sqrt(v)),
       crude_odds_ratio = totals[1] * totals[4] / (totals[2] * totals[3]), strata = k)
}

#' Welch's unequal-variance t test (two-sided) and the 95 % interval of mean(x) - mean(y).
welch_test <- function(x, y) {
  res <- stats::t.test(x, y, var.equal = FALSE, conf.level = 0.95)
  list(difference = mean(x) - mean(y), t = unname(res$statistic), df = unname(res$parameter),
       p_value = res$p.value, ci95 = as.numeric(res$conf.int))
}
