# M1: the cleaning rules of contract/questions.md section 2, in the order they are written there.
# Every rule that removes or changes rows also counts what it did (the `issues` list).

ISSUE_ORDER <- c(
  "sessions_bad_timestamp", "sessions_exact_duplicates", "sessions_conflicting_ids", "sessions_out_of_period",
  "sessions_orphan_user", "sessions_unknown_channel", "users_missing_signup_channel", "users_city_variants_merged",
  "events_unknown_name", "events_orphan_session", "events_repeated_steps", "sessions_out_of_order",
  "orders_exact_duplicates", "orders_unparseable_amount", "orders_non_positive_amount", "orders_orphan_session",
  "orders_without_checkout"
)

normalise_label <- function(x) tolower(stringr::str_trim(x))

#' '2026-01-05 14:03:00' or '05/01/2026 14:03' (day first); anything else, or an impossible date, is NA.
parse_timestamp <- function(text) {
  text <- stringr::str_trim(text)
  out <- as.POSIXct(rep(NA_real_), origin = "1970-01-01", tz = "UTC")
  iso <- grepl("^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}$", text, perl = TRUE)
  dmy <- grepl("^\\d{2}/\\d{2}/\\d{4} \\d{2}:\\d{2}$", text, perl = TRUE)
  out[iso] <- as.POSIXct(text[iso], format = "%Y-%m-%d %H:%M:%S", tz = "UTC")
  out[dmy] <- as.POSIXct(text[dmy], format = "%d/%m/%Y %H:%M", tz = "UTC")
  out
}

#' '₹1,299.00' / '1299' / 'Rs. 1,299' / '-₹499.00' -> paise (a whole number); NA if it is not a number.
parse_amount_paise <- function(text) {
  t <- stringr::str_trim(text)
  for (noise in c("\u20b9", "Rs.", ",", " ")) t <- gsub(noise, "", t, fixed = TRUE)
  m <- stringr::str_match(t, "^(-?)(\\d+)(?:\\.(\\d{1,2}))?$")
  frac <- ifelse(is.na(m[, 4]), "0", m[, 4])
  frac <- stringr::str_pad(frac, 2, side = "right", pad = "0")
  paise <- as.numeric(m[, 3]) * 100 + as.numeric(frac)
  ifelse(is.na(m[, 1]), NA_real_, ifelse(m[, 2] == "-", -paise, paise))
}

clean_users <- function(raw, contract, issues) {
  aliases <- unlist(contract$cleaning$city_aliases)
  city <- normalise_label(raw$city)
  city <- ifelse(city %in% names(aliases), aliases[city], city)
  users <- tibble::tibble(
    user_id = as.numeric(stringr::str_trim(raw$user_id)),
    signup_channel = dplyr::na_if(stringr::str_trim(raw$signup_channel), ""),
    city = unname(city)
  )
  issues$users_missing_signup_channel <- sum(is.na(users$signup_channel))
  issues$users_city_variants_merged <- length(unique(raw$city)) - length(unique(users$city))
  list(users = users, issues = issues)
}

clean_sessions <- function(raw, users, export, contract, issues) {
  unknown <- unlist(contract$cleaning$unknown_channel_values)
  s <- tibble::tibble(
    session_id = stringr::str_trim(raw$session_id),
    user_id = stringr::str_trim(raw$user_id),
    device = normalise_label(raw$device),
    channel = normalise_label(raw$channel),
    started_at = parse_timestamp(raw$started_at)
  )
  s$channel[s$channel %in% unknown] <- "unknown"

  bad <- is.na(s$started_at)
  issues$sessions_bad_timestamp <- sum(bad)
  s <- s[!bad, ]

  before <- nrow(s)
  s <- dplyr::distinct(s)
  issues$sessions_exact_duplicates <- before - nrow(s)

  counts <- table(s$session_id)
  conflicting <- names(counts)[counts > 1]
  issues$sessions_conflicting_ids <- length(conflicting)
  s <- s[!(s$session_id %in% conflicting), ]

  day <- as.Date(s$started_at, tz = "UTC")
  outside <- day < export$period_start | day > export$period_end
  issues$sessions_out_of_period <- sum(outside)
  s <- s[!outside, ]

  s$user_id <- as.numeric(s$user_id)
  orphan <- !(s$user_id %in% users$user_id)
  issues$sessions_orphan_user <- sum(orphan)
  s <- s[!orphan, ]

  issues$sessions_unknown_channel <- sum(s$channel == "unknown")
  s$week <- format(s$started_at, "%G-W%V")
  s$month <- format(s$started_at, "%Y-%m")
  list(sessions = dplyr::arrange(s, .data$session_id), issues = issues)
}

clean_events <- function(raw, sessions, contract, issues) {
  steps <- unlist(contract$cleaning$steps)
  e <- tibble::tibble(
    session_id = stringr::str_trim(raw$session_id),
    event_name = normalise_label(raw$event_name),
    event_at = parse_timestamp(raw$event_at)
  )
  unknown <- !(e$event_name %in% steps)
  issues$events_unknown_name <- sum(unknown)
  e <- e[!unknown, ]
  orphan <- !(e$session_id %in% sessions$session_id)
  issues$events_orphan_session <- sum(orphan)
  e <- e[!orphan, ]

  first <- e %>%
    dplyr::group_by(.data$session_id, .data$event_name) %>%
    dplyr::summarise(first_at = min(.data$event_at), .groups = "drop") %>%
    dplyr::arrange(.data$session_id, .data$event_name)
  issues$events_repeated_steps <- nrow(e) - nrow(first)

  wide <- tidyr::pivot_wider(first, names_from = "event_name", values_from = "first_at")
  out_of_order <- rep(FALSE, nrow(wide))
  for (i in seq_len(length(steps) - 1)) {
    earlier <- steps[i]
    later <- steps[i + 1]
    if (earlier %in% names(wide) && later %in% names(wide)) {
      later_first <- wide[[later]] < wide[[earlier]]
      out_of_order <- out_of_order | (!is.na(later_first) & later_first)
    }
  }
  issues$sessions_out_of_order <- sum(out_of_order)
  list(events = first, issues = issues)
}

clean_orders <- function(raw, sessions, events, issues) {
  before <- nrow(raw)
  o <- dplyr::distinct(raw)
  issues$orders_exact_duplicates <- before - nrow(o)
  o$order_id <- stringr::str_trim(o$order_id)
  o$session_id <- stringr::str_trim(o$session_id)
  o$amount_paise <- parse_amount_paise(o$amount)
  unparseable <- is.na(o$amount_paise)
  issues$orders_unparseable_amount <- sum(unparseable)
  o <- o[!unparseable, ]
  non_positive <- o$amount_paise <= 0
  issues$orders_non_positive_amount <- sum(non_positive)
  o <- o[!non_positive, ]
  orphan <- !(o$session_id %in% sessions$session_id)
  issues$orders_orphan_session <- sum(orphan)
  o <- o[!orphan, ]
  checkout <- events$session_id[events$event_name == "checkout"]
  issues$orders_without_checkout <- sum(!(o$session_id %in% checkout))
  extra <- setdiff(names(raw), c("order_id", "session_id", "amount"))
  o <- o[, c("order_id", "session_id", "amount_paise", extra)]
  list(orders = dplyr::arrange(o, .data$order_id), issues = issues)
}

clean_tables <- function(raw, export, contract) {
  issues <- list()
  u <- clean_users(raw$users, contract, issues)
  s <- clean_sessions(raw$sessions, u$users, export, contract, u$issues)
  e <- clean_events(raw$events, s$sessions, contract, s$issues)
  o <- clean_orders(raw$orders, s$sessions, e$events, e$issues)
  list(
    users = u$users, sessions = s$sessions, events = e$events, orders = o$orders,
    issues = o$issues[ISSUE_ORDER],
    raw_rows = lapply(raw, nrow)
  )
}
