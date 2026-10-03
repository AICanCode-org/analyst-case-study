skip_if_pending("test-unit-load.R")

test_that("every table is read as text and empty cells are kept", {
  raw <- load_raw(TINY, CONTRACT)
  expect_equal(lapply(raw, nrow), EXPECTED$raw_rows[names(raw)])
  expect_true(all(vapply(raw$orders, is.character, TRUE)))
  expect_identical(raw$users$signup_channel[2], "")  # empty, not NA
  expect_identical(raw$users$city[2], " pune ")  # whitespace kept for clean.R to decide
  expect_identical(raw$orders$amount[1], "\u20b91,299.00")  # text, not a guessed number
})

test_that("a missing column is a contract error", {
  data <- export_copy()
  replace_first(file.path(data, "orders.csv"), "amount", "amt")
  expect_error(load_raw(data, CONTRACT), "orders.csv is missing column\\(s\\) amount", class = "contract_error")
})

test_that("extra columns are allowed", {
  data <- export_copy()
  path <- file.path(data, "orders.csv")
  lines <- readLines(path, encoding = "UTF-8")
  writeLines(c(paste0(lines[1], ",payment_method"), paste0(lines[-1], ",upi")), path, useBytes = TRUE)
  expect_true("payment_method" %in% names(load_raw(data, CONTRACT)$orders))
})

test_that("a missing file is a contract error", {
  data <- export_copy()
  file.remove(file.path(data, "events.csv"))
  expect_error(load_raw(data, CONTRACT), "missing file", class = "contract_error")
})

test_that("the export manifest is read", {
  e <- load_export(TINY)
  expect_identical(list(e$name, format(e$period_start), format(e$period_end), e$sample_rate, e$months),
                   list("2026-03", "2026-03-01", "2026-03-31", 1, 1))
  expect_error(load_export(tempdir()), "export\\.json not found", class = "contract_error")
})
