skip_if_pending("test-unit-metrics.R")

funnel_of <- function(clean) funnel_by_device(session_funnel(clean), clean)

test_that("funnel by device", {
  clean <- tiny()$clean
  f <- funnel_of(clean)
  for (d in names(EXPECTED$funnel)) {
    got <- f$by_device[[d]][names(EXPECTED$funnel[[d]])]
    expect_equal(lapply(got, as.numeric), lapply(EXPECTED$funnel[[d]], as.numeric), info = d)
  }
  expect_identical(as.character(f$steps), c("sessions", "view", "cart", "checkout", "purchase"))
  expect_equal(f$mobile_share_of_sessions, 0.5)
  expect_equal(f$mobile_share_of_revenue, 209900 / 809950)
})

test_that("rates use the previous step as denominator", {
  m <- funnel_of(tiny()$clean)$by_device$mobile
  expect_equal(m$conversion, 1 / 4)
  expect_equal(m$step_rates, list(view = 3 / 4, cart = 3 / 3, checkout = 2 / 3, purchase = 1 / 2))
})

test_that("the funnel is monotone and needs every previous step", {
  f <- session_funnel(tiny()$clean)
  row <- function(id) f[f$session_id == id, ]
  expect_false(row("S12")$cart)  # a cart event without a view does not count
  expect_false(row("S2")$purchase)  # an order without checkout is revenue, not a funnel purchase
  expect_false(row("S6")$purchase)  # checkout but its only order is unparseable
  expect_true(all(f$cart <= f$view & f$checkout <= f$cart & f$purchase <= f$checkout))
})

test_that("by channel lists every channel and both devices", {
  got <- by_channel(session_funnel(tiny()$clean))
  expect_equal(as_json_lists(got), EXPECTED$channels)
})

test_that("weekly", {
  got <- weekly(session_funnel(tiny()$clean))
  expect_equal(as_json_lists(got), EXPECTED$weekly)
})

test_that("a rate with no denominator is null", {
  clean <- tiny()$clean
  clean$sessions <- clean$sessions[clean$sessions$device == "mobile", ]
  f <- funnel_of(clean)
  expect_null(f$by_device$desktop$conversion)
  expect_null(f$by_device$desktop$step_rates$purchase)
  expect_true(is.na(weekly(session_funnel(clean))[[1]]$conversion$desktop))
})
