skip_if_pending("test-unit-cli.R")

test_that("run writes answers.json", {
  out <- tempfile("out")
  expect_output(code <- main(c("run", "--data", EXPORT_V10, "--out", out)), "recommendation run_targeted_experiment")
  expect_identical(code, 0L)
  answers <- jsonlite::read_json(file.path(out, "answers.json"))
  expect_identical(answers$schema, "funnellens-answers")
  expect_identical(answers$generator$track, "r")
  expect_identical(answers$decision$recommendation, "run_targeted_experiment")
})

test_that("a contract violation exits 3 and writes nothing", {
  out <- tempfile("out")
  expect_message(code <- main(c("run", "--data", TINY, "--out", out)), "sessions.row_count")  # 8 sessions < min
  expect_identical(code, 3L)
  expect_false(file.exists(file.path(out, "answers.json")))
})

test_that("a folder without export.json exits 3", {
  expect_message(code <- main(c("run", "--data", tempdir(), "--out", tempfile())))
  expect_identical(code, 3L)
})

test_that("an unwritable output exits 2", {
  blocker <- tempfile("file")
  writeLines("not a folder", blocker)
  expect_message(code <- suppressWarnings(main(c("run", "--data", EXPORT_V10, "--out", blocker))))
  expect_identical(code, 2L)
})

test_that("usage errors exit 2", {
  expect_message(expect_identical(main(c("run")), 2L), "usage")
  expect_message(expect_identical(main(character()), 2L), "usage")
  expect_message(expect_identical(main(c("run", "--bogus", "x")), 2L), "usage")
})
