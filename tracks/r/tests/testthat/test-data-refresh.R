# Phase 7 (v1.1) data tests: the refreshed 2026-08 export, the incident it caused, and compatibility.
skip_if_pending("test-data-refresh.R")

answers <- as_json_lists(analyse(EXPORT_V11))
golden <- function(name) jsonlite::read_json(file.path(CONTRACT_DIR, "golden", name))

test_that("the v1.0 contract refuses the new channel", {
  # The incident: v1.0 stopped (exit 3) instead of silently dropping or mislabelling referral traffic.
  expect_error(analyse(EXPORT_V11, CONTRACT_V10), "sessions.channel.accepted \\(\\d+ rows\\)", class = "contract_error")
})

test_that("the answers match the 2026-08 golden", {
  expect_identical(json_diff(golden("answers-2026-08.json"), answers), NULL)
})

test_that("monitoring flags the tracking break when the week is not excluded", {
  contract <- yaml::read_yaml(file.path(CONTRACT_DIR, "data-contract.yaml"))
  contract$cleaning$exclude_weeks <- list()
  path <- tempfile(fileext = ".yaml")
  yaml::write_yaml(contract, path)
  a <- as_json_lists(analyse(EXPORT_V11, path))
  anomalies <- a$monitoring$anomalies
  expect_identical(lapply(anomalies, function(x) c(x$week, x$metric)),
                   list(c("2026-W31", "mobile_checkout_given_cart")))
  expect_lt(anomalies[[1]]$deviation, -0.5)
  status <- stats::setNames(vapply(a$data_quality$checks, function(c) c$status, ""),
                            vapply(a$data_quality$checks, function(c) c$id, ""))
  expect_identical(status[["orders.without_checkout.ratio"]], "warn") # the second symptom
})

test_that("with the week excluded the data is clean", {
  m <- answers$monitoring
  expect_identical(m$excluded_weeks, list("2026-W31"))
  expect_length(m$anomalies, 0)
  expect_false(m$freshness$stale)
  expect_false("2026-W31" %in% vapply(answers$weekly, function(w) w$week, ""))
  expect_gt(answers$data_quality$issues$sessions_excluded_week, 0)
  expect_identical(unique(vapply(answers$data_quality$checks, function(c) c$status, "")), "pass")
})

test_that("payment methods and the recommendation", {
  pm <- answers$payment_methods$by_device
  expect_setequal(names(pm$mobile), c("card", "cod", "netbanking", "upi"))
  expect_equal(sum(unlist(pm)), answers$data_quality$clean_rows$orders)
  expect_identical(answers$decision$recommendation, "run_targeted_experiment") # the refresh confirms v1.0
})

test_that("backward compatible on the v1.0 export", {
  a <- as_json_lists(analyse(EXPORT_V10))
  expect_identical(json_diff(golden("answers-2026-06.json"), a, subset = TRUE), NULL)
  expect_null(a$payment_methods)
  expect_identical(a$schema_version, "1.1")
})
