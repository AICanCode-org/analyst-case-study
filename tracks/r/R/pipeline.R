# The whole run: load -> clean -> checks (stop on error) -> answers.json; and the command line.

analyse <- function(data_dir, contract_file = NULL) {
  contract <- load_contract(contract_file)
  export <- load_export(data_dir)
  clean <- clean_tables(load_raw(data_dir, contract), export, contract)
  checks <- run_checks(clean, export, contract)
  raise_on_errors(checks)
  build_answers(clean, checks, export, contract)
}

write_answers <- function(answers, out_dir) {
  dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
  path <- file.path(out_dir, "answers.json")
  json <- jsonlite::toJSON(answers, auto_unbox = TRUE, digits = NA, null = "null", na = "null", pretty = TRUE)
  writeLines(json, path, useBytes = TRUE)
  path
}

#' Command line (see run.R): run --data DIR [--out DIR] [--contract FILE]. Returns the exit code.
main <- function(args = commandArgs(trailingOnly = TRUE)) {
  usage <- "usage: Rscript run.R run --data DIR [--out DIR] [--contract FILE]"
  if (length(args) < 1 || args[1] != "run") {
    message(usage)
    return(2L)
  }
  opt <- list(data = NULL, out = "out", contract = NULL)
  i <- 2
  while (i <= length(args)) {
    key <- sub("^--", "", args[i])
    if (!(key %in% names(opt)) || i == length(args)) {
      message(usage)
      return(2L)
    }
    opt[[key]] <- args[i + 1]
    i <- i + 2
  }
  if (is.null(opt$data)) {
    message(usage)
    return(2L)
  }
  tryCatch({
    answers <- analyse(opt$data, opt$contract)
    path <- write_answers(answers, opt$out)
    cat(sprintf("wrote %s: export %s, recommendation %s\n", path, answers$dataset$export,
                answers$decision$recommendation))
    0L
  }, contract_error = function(e) {
    message("funnellens (R): ", conditionMessage(e))
    3L
  }, error = function(e) {
    message("funnellens (R): ", conditionMessage(e))
    2L
  })
}
