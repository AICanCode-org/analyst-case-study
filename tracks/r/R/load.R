# M1: load the raw CSVs exactly as text. Types are decided in clean.R, never guessed by the reader.

TABLES <- c("users", "sessions", "events", "orders")

load_raw <- function(data_dir, contract) {
  raw <- list()
  for (table in TABLES) {
    path <- file.path(data_dir, paste0(table, ".csv"))
    if (!file.exists(path)) stop(contract_error(sprintf("missing file %s", path)))
    df <- readr::read_csv(path, col_types = readr::cols(.default = readr::col_character()),
                          na = character(), trim_ws = FALSE, progress = FALSE)
    missing <- setdiff(unlist(contract$raw[[table]]), names(df))
    if (length(missing) > 0) {
      stop(contract_error(sprintf("%s.csv is missing column(s) %s", table, paste(missing, collapse = ", "))))
    }
    raw[[table]] <- df
  }
  raw
}
