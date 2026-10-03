# Phase 4 data tests: properties that must hold for ANY export, whatever the numbers are.
skip_if_pending("test-data-invariants.R")

a <- as_json_lists(analyse(EXPORT_V10))
KEYS <- c("sessions", "view", "cart", "checkout", "purchase")

test_that("the funnel never grows", {
  for (d in names(a$funnel$by_device)) {
    counts <- nums(a$funnel$by_device[[d]][KEYS])
    expect_identical(counts, sort(counts, decreasing = TRUE), info = d)
  }
})

test_that("devices add up to all", {
  by <- a$funnel$by_device
  for (k in c(KEYS, "revenue_paise")) expect_equal(by$desktop[[k]] + by$mobile[[k]], by$all[[k]], info = k)
})

test_that("channels and weeks add up to devices", {
  by <- a$funnel$by_device
  for (d in c("desktop", "mobile")) {
    for (k in KEYS) expect_equal(sum(vapply(a$by_channel$channels, function(c) c[[d]][[k]], 0)), by[[d]][[k]])
    expect_equal(sum(vapply(a$weekly, function(w) w$sessions[[d]], 0)), by[[d]]$sessions)
    expect_equal(sum(vapply(a$weekly, function(w) w$purchases[[d]], 0)), by[[d]]$purchase)
  }
})

test_that("rows removed plus rows kept equals rows read", {
  dq <- a$data_quality
  i <- dq$issues
  expect_equal(dq$raw_rows$orders - i$orders_exact_duplicates - i$orders_unparseable_amount -
                 i$orders_non_positive_amount - i$orders_orphan_session, dq$clean_rows$orders)
  expect_equal(dq$raw_rows$events - i$events_unknown_name - i$events_orphan_session - i$events_repeated_steps,
               dq$clean_rows$events)
  expect_equal(dq$raw_rows$users, dq$clean_rows$users)
  removed <- i$sessions_bad_timestamp + i$sessions_exact_duplicates + i$sessions_out_of_period + i$sessions_orphan_user
  expect_gte(dq$raw_rows$sessions - removed - dq$clean_rows$sessions, 2 * i$sessions_conflicting_ids)
})

test_that("no error check fails", {
  errors <- Filter(function(c) c$severity == "error", a$data_quality$checks)
  expect_identical(unique(vapply(errors, function(c) c$status, "")), "pass")
})

test_that("statistics are well formed", {
  tests <- c(list(a$payment_step_test, a$order_value), a$by_channel$cmh)
  for (t in tests) {
    expect_true(t$p_value >= 0 && t$p_value <= 1)
    expect_lt(t$ci95[[1]], t$ci95[[2]])
  }
  pay <- a$payment_step_test
  expect_true(pay$ci95[[1]] < pay$difference && pay$difference < pay$ci95[[2]])
  for (t in a$by_channel$cmh) expect_true(t$ci95[[1]] < t$odds_ratio_mh && t$odds_ratio_mh < t$ci95[[2]])
})
