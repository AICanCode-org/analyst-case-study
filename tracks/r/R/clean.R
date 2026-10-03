# M1: the cleaning rules of contract/questions.md section 2, in the order they are written there.
# Every rule that removes or changes rows also counts what it did (the `issues` list).

ISSUE_ORDER <- c(
  "sessions_bad_timestamp", "sessions_exact_duplicates", "sessions_conflicting_ids", "sessions_out_of_period",
  "sessions_orphan_user", "sessions_unknown_channel", "users_missing_signup_channel", "users_city_variants_merged",
  "events_unknown_name", "events_orphan_session", "events_repeated_steps", "sessions_out_of_order",
  "orders_exact_duplicates", "orders_unparseable_amount", "orders_non_positive_amount", "orders_orphan_session",
  "orders_without_checkout"
)

normalise_label <- function(x) {
  # TODO(M1) normalise_label: trim + lower-case. Used for device, channel, event name and city before anything
  # is compared. Spec: contract/questions.md §2; tests: clean.
  stop("TODO(M1) normalise_label: see the comment above")
}

#' '2026-01-05 14:03:00' or '05/01/2026 14:03' (day first); anything else, or an impossible date, is NA.
parse_timestamp <- function(text) {
  # TODO(M1) parse_timestamp: exactly two formats: 'YYYY-MM-DD HH:MM:SS' and 'DD/MM/YYYY HH:MM' (day first!).
  # Anything else, or an impossible date such as 31/02, is missing, never a guess. Spec: contract/questions.md
  # §2; tests: clean.
  stop("TODO(M1) parse_timestamp: see the comment above")
}

#' '₹1,299.00' / '1299' / 'Rs. 1,299' / '-₹499.00' -> paise (a whole number); NA if it is not a number.
parse_amount_paise <- function(text) {
  # TODO(M1) parse_amount_paise: strip the rupee sign, 'Rs.', thousands separators and spaces; keep the sign; at
  # most 2 decimals; return whole paise (integers: no float rounding in money). Spec: contract/questions.md §2;
  # tests: clean.
  stop("TODO(M1) parse_amount_paise: see the comment above")
}

clean_users <- function(raw, contract, issues) {
  # TODO(M1) clean_users: city aliases from the contract, empty signup_channel -> missing. Count what you merged
  # and what is missing (the issues dict). Spec: contract/questions.md §2; tests: clean.
  stop("TODO(M1) clean_users: see the comment above")
}

clean_sessions <- function(raw, users, export, contract, issues) {
  # TODO(M1) clean_sessions: the session rules of §2 in the written order; every rule that drops rows counts
  # them. Conflicting duplicate ids are dropped completely: you cannot tell which row is true. Spec:
  # contract/questions.md §2; tests: clean.
  stop("TODO(M1) clean_sessions: see the comment above")
}

clean_events <- function(raw, sessions, contract, issues) {
  # TODO(M1) clean_events: unknown event names and orphan events go; keep the FIRST time of each step per
  # session; count out-of-order sessions but keep them. Spec: contract/questions.md §2; tests: clean.
  stop("TODO(M1) clean_events: see the comment above")
}

clean_orders <- function(raw, sessions, events, issues) {
  # TODO(M1) clean_orders: trap: merging orders onto sessions when session_id is not unique multiplies revenue.
  # Check uniqueness and count before and after every join. Spec: contract/questions.md §2; tests: clean.
  stop("TODO(M1) clean_orders: see the comment above")
}

clean_tables <- function(raw, export, contract) {
  # TODO(M1) clean_tables: call the four cleaners in order and return the tables, the issues (in ISSUE_ORDER)
  # and the raw row counts. Spec: contract/questions.md §2; tests: clean.
  stop("TODO(M1) clean_tables: see the comment above")
}
