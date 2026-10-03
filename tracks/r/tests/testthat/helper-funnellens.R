# ---------------------------------------------------------------------------
# PENDING test files describe behaviour you have not built yet, so they are skipped.
# When you start a milestone, delete its line here, watch the tests fail (red),
# implement until they pass (green). See docs/phase-3.
# ---------------------------------------------------------------------------
PENDING <- c(
  "test-data-golden.R" = "Phase 4 - golden answers on the real export",
  "test-data-invariants.R" = "Phase 4 - invariants on the real export",
  "test-data-contract-violations.R" = "Phase 4 - contract violations stop the run"
)

skip_if_pending <- function(file) {
  if (file %in% names(PENDING)) skip(sprintf("PENDING (%s) - see tests/testthat/helper-funnellens.R", PENDING[[file]]))
}

# covr runs the tests from a temporary copy of the package, so it passes the repo path explicitly
REPO <- Sys.getenv("FUNNELLENS_REPO", normalizePath(file.path(track_root(), "..", "..")))
CONTRACT_DIR <- file.path(REPO, "contract")
TINY <- file.path(CONTRACT_DIR, "fixtures", "tiny")
EXPORT_V10 <- file.path(REPO, "data", "raw", "2026-06")
EXPECTED <- jsonlite::read_json(file.path(CONTRACT_DIR, "fixtures", "tiny-expected.json"))
STATS_CASES <- jsonlite::read_json(file.path(CONTRACT_DIR, "fixtures", "stats-cases.json"))
Z <- 1.959963984540054
CONTRACT <- load_contract()

#' The hand-made 14-session export, cleaned (see contract/fixtures/tiny-expected.json).
tiny <- function() {
  export <- load_export(TINY)
  list(clean = clean_tables(load_raw(TINY, CONTRACT), export, CONTRACT), export = export)
}

#' A writable copy of an export folder, to corrupt on purpose.
export_copy <- function(source = TINY) {
  target <- file.path(tempfile("export"), basename(source))
  dir.create(target, recursive = TRUE)
  file.copy(list.files(source, full.names = TRUE), target)
  target
}

append_line <- function(path, line) cat(line, "\n", file = path, sep = "", append = TRUE)

replace_first <- function(path, from, to) {
  text <- readLines(path, encoding = "UTF-8")
  text[1] <- sub(from, to, text[1], fixed = TRUE)
  writeLines(text, path, useBytes = TRUE)
}

#' A list of numbers from JSON (null -> NA) as a plain numeric vector.
nums <- function(x) vapply(x, function(v) if (is.null(v)) NA_real_ else as.numeric(v), 0)

#' answers -> the same JSON text the CLI writes, read back as plain lists.
as_json_lists <- function(answers) {
  jsonlite::fromJSON(jsonlite::toJSON(answers, auto_unbox = TRUE, digits = NA, null = "null", na = "null"),
                     simplifyVector = FALSE)
}

#' The shared contract with its checks replaced (modifyList would merge the unnamed list instead).
with_checks <- function(checks) {
  contract <- CONTRACT
  contract$checks <- checks
  contract
}
