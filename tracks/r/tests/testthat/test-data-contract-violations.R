# Phase 4 data tests: broken exports must be refused (exit code 3), never silently analysed.
skip_if_pending("test-data-contract-violations.R")

test_that("a new channel value stops the run", {
  data <- export_copy(EXPORT_V10)
  append_line(file.path(data, "sessions.csv"), "S999999,1,mobile,affiliate,2026-06-30 10:00:00")
  expect_error(analyse(data), "sessions.channel.accepted \\(1 rows\\)", class = "contract_error")
})

test_that("a reused order id stops the run", {
  data <- export_copy(EXPORT_V10)
  first <- strsplit(readLines(file.path(data, "orders.csv"), n = 2)[2], ",")[[1]][1]
  append_line(file.path(data, "orders.csv"), paste0(first, ",S000002,999"))
  expect_error(analyse(data), "orders.order_id.unique", class = "contract_error")
})

test_that("an absurd amount stops the run", {
  data <- export_copy(EXPORT_V10)
  append_line(file.path(data, "orders.csv"), "O999999,S000002,\"\u20b91,50,00,000.00\"")
  expect_error(analyse(data), "orders.amount_paise.range", class = "contract_error")
})

test_that("a renamed column stops the run", {
  data <- export_copy(EXPORT_V10)
  replace_first(file.path(data, "events.csv"), "event_name", "event")
  expect_error(analyse(data), "events\\.csv is missing column", class = "contract_error")
})
