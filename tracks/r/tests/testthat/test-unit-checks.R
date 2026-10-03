skip_if_pending("test-unit-checks.R")

statuses <- function(results) {
  stats::setNames(lapply(results, function(r) list(r$status, r$failing_rows)), vapply(results, function(r) r$id, ""))
}

expected_checks <- function() lapply(EXPECTED$checks, function(x) list(x[[1]], as.integer(x[[2]])))

test_that("every contract check on the tiny export", {
  t <- tiny()
  results <- run_checks(t$clean, t$export, CONTRACT)
  expect_identical(vapply(results, function(r) r$id, ""), vapply(CONTRACT$checks, function(c) c$id, ""))
  expect_identical(statuses(results), expected_checks())
})

test_that("ratio checks report the observed ratio", {
  t <- tiny()
  by_id <- stats::setNames(run_checks(t$clean, t$export, CONTRACT), vapply(CONTRACT$checks, function(c) c$id, ""))
  expect_equal(by_id[["sessions.unknown_channel.ratio"]]$observed, 2 / 8)
  expect_equal(by_id[["sessions.duplicate_rows.ratio"]]$observed, 1 / 14)
  expect_null(by_id[["users.user_id.unique"]]$observed)
})

test_that("a new channel value fails the accepted values check", {
  t <- tiny()
  t$clean$sessions$channel[1] <- "referral"
  expect_identical(statuses(run_checks(t$clean, t$export, CONTRACT))[["sessions.channel.accepted"]], list("fail", 1L))
})

test_that("duplicate keys and broken relationships fail", {
  t <- tiny()
  t$clean$orders <- rbind(t$clean$orders, t$clean$orders[1, ])
  t$clean$events$session_id[1] <- "S404"
  s <- statuses(run_checks(t$clean, t$export, CONTRACT))
  expect_identical(s[["orders.order_id.unique"]], list("fail", 2L))  # both rows of the duplicated id
  expect_identical(s[["events.session_id.relationship"]], list("fail", 1L))
})

test_that("out of range amounts and dates fail", {
  t <- tiny()
  t$clean$orders$amount_paise[1] <- 50
  t$clean$sessions$started_at[1] <- as.POSIXct("2026-04-01 00:00:00", tz = "UTC")
  s <- statuses(run_checks(t$clean, t$export, CONTRACT))
  expect_identical(s[["orders.amount_paise.range"]], list("fail", 1L))
  expect_identical(s[["sessions.started_at.in_period"]], list("fail", 1L))
})

test_that("not null check", {
  t <- tiny()
  check <- list(id = "users.signup_channel.not_null", type = "not_null", table = "users", column = "signup_channel",
                severity = "warn")
  result <- run_checks(t$clean, t$export, with_checks(list(check)))
  expect_identical(statuses(result), list(users.signup_channel.not_null = list("warn", 1L)))
})

test_that("an unknown check type is a contract error", {
  t <- tiny()
  bad <- list(id = "x", type = "regex", table = "users", column = "city", severity = "warn")
  expect_error(run_checks(t$clean, t$export, with_checks(list(bad))),
               "unknown check type", class = "contract_error")
})

test_that("only failed error checks stop the pipeline", {
  t <- tiny()
  results <- run_checks(t$clean, t$export, CONTRACT)
  expect_error(raise_on_errors(results), "sessions.row_count \\(1 rows\\)", class = "contract_error")
  expect_silent(raise_on_errors(Filter(function(r) r$id != "sessions.row_count", results)))
})
