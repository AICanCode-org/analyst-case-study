# Read the shared data contract (contract/data-contract.yaml) and an export's manifest (export.json).

contract_error <- function(message) {
  structure(class = c("contract_error", "error", "condition"),
            list(message = message, call = NULL))
}

default_contract <- function() {
  env <- Sys.getenv("CONTRACT_PATH", "")
  if (nzchar(env)) {
    return(env)
  }
  file.path(track_root(), "..", "..", "contract", "data-contract.yaml")
}

track_root <- function() {
  # the folder with DESCRIPTION: works from the package source, tests and run.R
  root <- getOption("funnellens.root", NULL)
  if (!is.null(root)) {
    return(root)
  }
  dir <- normalizePath(".")
  while (!file.exists(file.path(dir, "DESCRIPTION")) && dirname(dir) != dir) dir <- dirname(dir)
  dir
}

load_contract <- function(path = NULL) {
  yaml::read_yaml(if (is.null(path)) default_contract() else path)
}

load_export <- function(data_dir) {
  meta_path <- file.path(data_dir, "export.json")
  if (!file.exists(meta_path)) {
    stop(contract_error(sprintf("%s not found: is --data an export folder like data/raw/2026-06?", meta_path)))
  }
  meta <- jsonlite::read_json(meta_path)
  start <- as.Date(meta$period_start)
  end <- as.Date(meta$period_end)
  months <- (as.integer(format(end, "%Y")) - as.integer(format(start, "%Y"))) * 12 +
    as.integer(format(end, "%m")) - as.integer(format(start, "%m")) + 1
  list(name = meta$export, period_start = start, period_end = end,
       sample_rate = as.numeric(meta$sample_rate), months = months)
}
