skip_if_pending("test-unit-answers.R")

CHANNELS <- list(
  list(channel = "email", mobile = list(view = 100, cart = 40, checkout = 20, purchase = 10),
       desktop = list(view = 100, cart = 40, checkout = 20, purchase = 15)),
  list(channel = "organic", mobile = list(view = 50, cart = 10, checkout = 5, purchase = 4),
       desktop = list(view = 80, cart = 30, checkout = 10, purchase = 6)),
  list(channel = "affiliate", mobile = list(view = 9, cart = 3, checkout = 2, purchase = 1),
       desktop = list(view = 0, cart = 0, checkout = 0, purchase = 0))
)
EXPORT <- list(name = "2026-03", period_start = as.Date("2026-01-01"), period_end = as.Date("2026-02-28"),
               sample_rate = 0.5, months = 2)

test_that("strata skip channels missing a device", {
  expect_equal(strata_for(CHANNELS, "purchase", "checkout"), list(email = c(10, 10, 15, 5), organic = c(4, 1, 6, 4)))
})

test_that("opportunity counts only positive gaps and scales the sample", {
  funnel <- list(by_device = list(mobile = list(revenue_paise = 1000000)))
  value <- list(mobile = list(mean_inr = 2000))
  opp <- opportunity(CHANNELS, funnel, value, EXPORT)
  expect_equal(vapply(opp$by_channel, function(r) r$gap, 0), c(0.25, 0))  # organic: mobile is better
  expect_equal(opp$extra_orders_in_sample, 20 * 0.25)
  expect_equal(opp$months, 2)
  expect_equal(opp$extra_orders_per_month, 5 / 2 / 0.5)
  expect_equal(opp$monthly_revenue_uplift_inr, 5 * 2000)
  expect_equal(opp$mobile_monthly_revenue_inr, 10000 / 2 / 0.5)
  expect_equal(opp$uplift_share_of_mobile_revenue, 1)
})

channel <- function(pay_p, cart_p = 0.5, cart_or = 1.1, cart_gap = -0.05) {
  list(cmh = list(purchase_given_checkout = list(p_value = pay_p),
                  cart_given_view = list(p_value = cart_p, odds_ratio_mh = cart_or)),
       simpson = list(aggregate_gap = cart_gap))
}

test_that("decision rules", {
  cases <- list(
    list(0.20, 9e9, "no_checkout_gap_found", "adjusted_payment_gap_not_significant"),
    list(0.05, 9e9, "no_checkout_gap_found", "adjusted_payment_gap_not_significant"),  # p = alpha
    list(0.01, 2500000, "rebuild_checkout", c("adjusted_payment_gap_significant", "uplift_above_rebuild_threshold")),
    list(0.01, 2499999, "run_targeted_experiment",
         c("adjusted_payment_gap_significant", "uplift_below_rebuild_threshold"))
  )
  for (case in cases) {
    d <- decision(channel(case[[1]], cart_gap = 0.01), list(monthly_revenue_uplift_inr = case[[2]]), CONTRACT)
    expect_identical(d$recommendation, case[[3]])
    expect_identical(as.character(d$reasons), case[[4]])
    expect_equal(d$thresholds, list(alpha = 0.05, rebuild_min_monthly_uplift_inr = 2500000))
  }
})

test_that("the channel-mix reason", {
  cases <- list(
    list(0.30, 0.9, -0.05, TRUE),  # not significant within channels
    list(0.01, 1.08, -0.05, TRUE),  # significant, but mobile carts MORE within channels
    list(0.01, 0.9, -0.05, FALSE),  # a real within-channel cart gap
    list(0.30, 1.1, 0.02, FALSE)  # no aggregate gap to explain
  )
  for (case in cases) {
    d <- decision(channel(0.01, case[[1]], case[[2]], case[[3]]), list(monthly_revenue_uplift_inr = 0), CONTRACT)
    expect_identical("aggregate_cart_gap_is_channel_mix" %in% d$reasons, case[[4]])
  }
})
