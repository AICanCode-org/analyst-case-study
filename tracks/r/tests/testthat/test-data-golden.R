# Phase 4 data test: the full 2026-06 export must reproduce the golden answers that the Python,
# SQL and R tracks agree on (contract/golden/answers-2026-06.json).
skip_if_pending("test-data-golden.R")

answers <- as_json_lists(analyse(EXPORT_V10))

#' The same comparison as scripts/parity.py: numbers to 1e-9 relative, everything else exactly.
json_diff <- function(a, b, path = "$") {
  if (is.list(a) && is.list(b)) {
    if (!identical(sort(names(a)), sort(names(b))) || length(a) != length(b)) return(path)
    keys <- if (is.null(names(a))) seq_along(a) else setdiff(names(a), "generator")
    return(unlist(lapply(keys, function(k) json_diff(a[[k]], b[[k]], paste0(path, "/", k)))))
  }
  if (is.numeric(a) && is.numeric(b)) {
    if (abs(a - b) <= max(1e-12, 1e-9 * abs(a))) return(NULL) else return(path)
  }
  if (identical(a, b)) NULL else path
}

test_that("the answers match the golden file", {
  golden <- jsonlite::read_json(file.path(CONTRACT_DIR, "golden", "answers-2026-06.json"))
  expect_identical(json_diff(golden, answers), NULL)
})

test_that("the headline findings hold", {
  expect_true(answers$funnel$mobile_share_of_sessions > 0.65 && answers$funnel$mobile_share_of_sessions < 0.72)
  pay <- answers$by_channel$cmh$purchase_given_checkout
  expect_true(pay$p_value < 0.001 && pay$ci95[[2]] < 1)  # mobile pays less, even within channels
  expect_true(pay$odds_ratio_mh > pay$crude_odds_ratio)
  expect_true(answers$order_value$p_value > 0.5)  # basket size is not the problem
  expect_identical(answers$decision$recommendation, "run_targeted_experiment")
})
