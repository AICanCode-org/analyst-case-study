# M1: load the raw CSVs exactly as text. Types are decided in clean.R, never guessed by the reader.

TABLES <- c("users", "sessions", "events", "orders")

load_raw <- function(data_dir, contract) {
  # TODO(M1) load_raw: read every CSV as TEXT (no type guessing, empty strings stay empty strings); a missing
  # file or column is a ContractError. Spec: contract/questions.md §1-2; tests: load.
  stop("TODO(M1) load_raw: see the comment above")
}
