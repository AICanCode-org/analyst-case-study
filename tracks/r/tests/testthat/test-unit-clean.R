skip_if_pending("test-unit-clean.R")

test_that("timestamps: two formats, day first, impossible dates are NA", {
  cases <- list(
    list("2026-01-05 14:03:00", "2026-01-05 14:03:00"),
    list("05/01/2026 14:03", "2026-01-05 14:03:00"),  # day first, never month first
    list(" 2026-01-05 14:03:00 ", "2026-01-05 14:03:00"),
    list("2026-02-30 10:00:00", NA),  # impossible date
    list("31/04/2026 10:00", NA),
    list("2026-01-05", NA),  # neither of the two formats
    list("01/05/2026 14:03:00", NA),
    list("", NA)
  )
  for (case in cases) {
    got <- parse_timestamp(case[[1]])
    if (is.na(case[[2]])) {
      expect_true(is.na(got), info = case[[1]])
    } else {
      expect_identical(format(got, "%Y-%m-%d %H:%M:%S"), case[[2]], info = case[[1]])
    }
  }
})

test_that("amounts become whole paise or NA", {
  text <- c("\u20b91,299.00", "1299", "Rs. 1,299", "-\u20b9499.00", "1,299.5", " 0 ", "N/A", "", "1,2O0.00",
            "12.345", "\u20b9")
  expected <- c(129900, 129900, 129900, -49900, 129950, 0, NA, NA, NA, NA, NA)
  expect_identical(parse_amount_paise(text), expected)
})

test_that("issue counts match the hand-checked fixture, in the shared order", {
  clean <- tiny()$clean
  expect_identical(names(clean$issues), names(EXPECTED$issues))
  expect_equal(lapply(clean$issues, as.integer), lapply(EXPECTED$issues, as.integer))
})

test_that("clean rows and keys", {
  clean <- tiny()$clean
  rows <- lapply(names(EXPECTED$clean_rows), function(t) nrow(clean[[t]]))
  expect_equal(stats::setNames(rows, names(EXPECTED$clean_rows)), EXPECTED$clean_rows)
  expect_identical(clean$sessions$session_id, unlist(EXPECTED$clean_session_ids))
  expect_equal(as.list(stats::setNames(clean$orders$amount_paise, clean$orders$order_id)), EXPECTED$clean_order_paise)
})

test_that("labels are normalised", {
  clean <- tiny()$clean
  expect_setequal(clean$sessions$device, c("desktop", "mobile"))
  expect_setequal(clean$sessions$channel, c("email", "organic", "paid_social", "unknown"))
  expect_identical(sort(unique(clean$users$city)), c("bengaluru", "pune"))
  expect_identical(sum(is.na(clean$users$signup_channel)), 1L)
})

test_that("ISO week and month", {
  s <- tiny()$clean$sessions
  week <- stats::setNames(s$week, s$session_id)
  expect_identical(unname(week[c("S1", "S6")]), c("2026-W10", "2026-W11"))  # Monday 2 March 2026
  expect_identical(format(s$started_at[s$session_id == "S11"], "%Y-%m-%d %H:%M"), "2026-03-10 18:45")
  expect_identical(unique(s$month), "2026-03")
})

test_that("events keep the first timestamp per step", {
  e <- tiny()$clean$events
  first <- e$first_at[e$session_id == "S2" & e$event_name == "view"]
  expect_identical(format(first, "%Y-%m-%d %H:%M:%S"), "2026-03-02 11:00:05")
  expect_false(any(duplicated(e[, c("session_id", "event_name")])))
})
