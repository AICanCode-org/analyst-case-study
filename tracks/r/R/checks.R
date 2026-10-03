# M2: run the contract checks (contract/data-contract.yaml `checks`) on the clean tables.
# Each check counts failing rows; it passes when that count is 0 (or the ratio is at most `max`).

failing_rows <- function(check, clean, export, contract) {
  kind <- check$type
  if (kind == "max_ratio") {
    parts <- strsplit(check$of, ".", fixed = TRUE)[[1]]
    denominator <- if (parts[1] == "raw") clean$raw_rows[[parts[2]]] else nrow(clean[[parts[2]]])
    count <- clean$issues[[check$issue]]
    ratio <- if (denominator > 0) count / denominator else 0
    return(list(count = if (ratio > check$max) count else 0, observed = ratio))
  }
  df <- clean[[check$table]]
  if (kind == "row_count_min") {
    return(list(count = if (nrow(df) >= check$min) 0 else 1, observed = NULL))
  }
  col <- df[[check$column]]
  count <- switch(kind,
    unique = sum(duplicated(col) | duplicated(col, fromLast = TRUE)),
    not_null = sum(is.na(col)),
    accepted_values = sum(!(col %in% unlist(contract$cleaning[[check$values_from]]))),
    range = sum(!is.na(col) & (col < check$min | col > check$max)),
    in_period = {
      day <- as.Date(col, tz = "UTC")
      sum(day < export$period_start | day > export$period_end)
    },
    relationship = {
      to <- strsplit(check$to, ".", fixed = TRUE)[[1]]
      sum(!(col %in% clean[[to[1]]][[to[2]]]))
    },
    stop(contract_error(sprintf("unknown check type '%s' in %s", kind, check$id)))
  )
  list(count = count, observed = NULL)
}

run_checks <- function(clean, export, contract) {
  lapply(contract$checks, function(check) {
    r <- failing_rows(check, clean, export, contract)
    status <- if (r$count == 0) "pass" else if (check$severity == "error") "fail" else "warn"
    list(id = check$id, type = check$type, severity = check$severity, status = status,
         failing_rows = as.integer(r$count), observed = r$observed)
  })
}

raise_on_errors <- function(results) {
  failed <- Filter(function(r) r$status == "fail", results)
  if (length(failed) > 0) {
    detail <- paste(vapply(failed, function(r) sprintf("%s (%d rows)", r$id, r$failing_rows), ""), collapse = ", ")
    stop(contract_error(paste("data contract violated:", detail)))
  }
  invisible(results)
}
