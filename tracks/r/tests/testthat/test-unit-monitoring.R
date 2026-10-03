# v1.1: monitoring and payment methods (contract/questions.md section 6) on the tiny export.
skip_if_pending("test-unit-monitoring.R")

run_monitoring <- function(contract = CONTRACT, keep = NULL) {
  t <- tiny()
  if (!is.null(keep)) t$clean$sessions <- t$clean$sessions[keep(t$clean$sessions), ]
  as_json_lists(monitoring(session_funnel(t$clean), t$clean, t$export, contract))
}

test_that("freshness and full weeks only", {
  m <- run_monitoring()
  expect_identical(m$freshness, list(period_end = "2026-03-31", last_session_date = "2026-03-11",
                                     days_behind = 20L, stale = TRUE))
  expect_identical(vapply(m$weeks, function(w) w$week, ""), c("2026-W10", "2026-W11")) # 1 March is a Sunday
  expect_identical(m$excluded_weeks, list("2026-W31"))
  expect_equal(m$max_relative_deviation, 0.30)
})

test_that("weekly values and medians", {
  m <- run_monitoring()
  expect_equal(m$weeks, list(
    list(week = "2026-W10", sessions = 5L, mobile_checkout_given_cart = 0.5), # S1 checks out, S2 does not
    list(week = "2026-W11", sessions = 3L, mobile_checkout_given_cart = 1.0)  # S6 (S12 never carts)
  ))
  expect_equal(m$medians, list(sessions = 4, mobile_checkout_given_cart = 0.75)) # even count: middle two
})

test_that("anomalies beyond the threshold", {
  m <- run_monitoring()
  expect_identical(vapply(m$anomalies, function(a) a$metric, ""), rep("mobile_checkout_given_cart", 2))
  expect_equal(vapply(m$anomalies, function(a) a$deviation, 0), c(-1 / 3, 1 / 3)) # sessions: 25 %, not flagged
  loose <- CONTRACT
  loose$monitoring$max_relative_deviation <- 1.0
  expect_length(run_monitoring(loose)$anomalies, 0) # |deviation| must EXCEED it
})

test_that("a 1.0 contract without a monitoring section uses the defaults", {
  old <- CONTRACT
  old$monitoring <- NULL
  expect_equal(run_monitoring(old)$max_relative_deviation, 0.30)
})

test_that("excluded weeks are dropped and counted", {
  c <- CONTRACT
  c$cleaning$exclude_weeks <- list("2026-W11")
  cleaned <- clean_tables(load_raw(TINY, c), load_export(TINY), c)
  expect_identical(cleaned$issues$sessions_excluded_week, 3L)
  expect_identical(utils::tail(names(cleaned$issues), 1), "sessions_excluded_week")
  expect_identical(unique(cleaned$sessions$week), "2026-W10")
})

test_that("payment methods only when the column exists", {
  t <- tiny()
  expect_null(payment_methods(t$clean))
  t$clean$orders$payment_method <- c("UPI ", "card", "", "upi", "Card")
  got <- payment_methods(t$clean)$by_device
  expect_identical(names(got), c("desktop", "mobile"))
  for (d in got) expect_identical(names(d), sort(names(d)))
  total <- unlist(got)
  sums <- tapply(total, sub("^[a-z]+\\.", "", names(total)), sum)
  expect_identical(as.list(sums), list(card = 2L, unknown = 1L, upi = 2L))
})

test_that("a week without mobile carts has a null rate", {
  m <- run_monitoring(keep = function(s) s$device == "desktop")
  expect_identical(lapply(m$weeks, function(w) w$mobile_checkout_given_cart), list(NULL, NULL))
  expect_null(m$medians$mobile_checkout_given_cart)
  expect_identical(vapply(m$anomalies, function(a) a$metric, ""), c("sessions", "sessions")) # 3 vs 1 around 2
})
