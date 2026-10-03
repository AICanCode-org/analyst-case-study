# Phase 4 data test: the full 2026-06 export must reproduce the golden answers that the Python,
# SQL and R tracks agree on (contract/golden/answers-2026-06.json).
# v1.1: that golden is the v1.0 file and stays frozen, so the comparison allows the additive v1.1 fields.
skip_if_pending("test-data-golden.R")

answers <- as_json_lists(analyse(EXPORT_V10))

test_that("the answers match the golden file", {
  golden <- jsonlite::read_json(file.path(CONTRACT_DIR, "golden", "answers-2026-06.json"))
  expect_identical(json_diff(golden, answers, subset = TRUE), NULL)
})

test_that("the headline findings hold", {
  expect_true(answers$funnel$mobile_share_of_sessions > 0.65 && answers$funnel$mobile_share_of_sessions < 0.72)
  pay <- answers$by_channel$cmh$purchase_given_checkout
  expect_true(pay$p_value < 0.001 && pay$ci95[[2]] < 1)  # mobile pays less, even within channels
  expect_true(pay$odds_ratio_mh > pay$crude_odds_ratio)
  expect_true(answers$order_value$p_value > 0.5)  # basket size is not the problem
  expect_identical(answers$decision$recommendation, "run_targeted_experiment")
})
