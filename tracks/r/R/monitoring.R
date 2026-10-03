# v1.1: data-quality monitoring (contract/questions.md section 6) and the payment-method breakdown.
# Monitoring reports; it never stops the run. It answers "can I compare this week with the others?"
# before anyone reads a trend: freshness of the export, and full ISO weeks whose volume or mobile
# checkout rate is far from the median week (a tracking break looks exactly like that).

METRICS <- c("sessions", "mobile_checkout_given_cart")
DEFAULT_MONITORING <- list(max_relative_deviation = 0.30, max_days_behind = 2)

#' The Monday of each date's ISO week.
monday_of <- function(d) d - (as.POSIXlt(d)$wday + 6) %% 7

full_weeks <- function(f, clean, export) {
  day <- as.Date(clean$sessions$started_at[match(f$session_id, clean$sessions$session_id)], tz = "UTC")
  monday <- monday_of(day)
  full <- f[monday >= export$period_start & monday + 6 <= export$period_end, ]
  lapply(sort(unique(full$week)), function(w) {
    part <- full[full$week == w, ]
    mobile <- part[part$device == "mobile", ]
    carts <- sum(mobile$cart)
    list(week = w, sessions = nrow(part),
         mobile_checkout_given_cart = if (carts > 0) sum(mobile$checkout) / carts else NA_real_)
  })
}

monitoring <- function(f, clean, export, contract) {
  cfg <- if (is.null(contract$monitoring)) DEFAULT_MONITORING else contract$monitoring # a 1.0 contract has none
  last <- max(as.Date(clean$sessions$started_at, tz = "UTC"))
  behind <- as.numeric(export$period_end - last)
  weeks <- full_weeks(f, clean, export)
  medians <- lapply(stats::setNames(METRICS, METRICS), function(m) {
    values <- vapply(weeks, function(w) as.numeric(w[[m]]), 0)
    values <- values[!is.na(values)]
    if (length(values) > 0) stats::median(values) else NA_real_
  })
  anomalies <- list()
  for (w in weeks) {
    for (m in METRICS) {
      value <- w[[m]]
      mid <- medians[[m]]
      if (is.na(value) || is.na(mid) || mid == 0) next
      deviation <- (value - mid) / mid
      if (abs(deviation) > cfg$max_relative_deviation) {
        anomalies[[length(anomalies) + 1]] <- list(week = w$week, metric = m, value = value, median = mid,
                                                   deviation = deviation)
      }
    }
  }
  list(
    freshness = list(period_end = format(export$period_end), last_session_date = format(last),
                     days_behind = behind, stale = behind > cfg$max_days_behind),
    excluded_weeks = I(as.character(unlist(contract$cleaning$exclude_weeks))),
    max_relative_deviation = cfg$max_relative_deviation,
    weeks = weeks,
    medians = medians,
    anomalies = anomalies
  )
}

payment_methods <- function(clean) {
  if (!("payment_method" %in% names(clean$orders))) return(NULL)
  o <- dplyr::inner_join(clean$orders, clean$sessions[, c("session_id", "device")], by = "session_id")
  method <- normalise_label(dplyr::coalesce(o$payment_method, ""))
  method[method == ""] <- "unknown"
  by_device <- lapply(stats::setNames(DEVICES, DEVICES), function(d) {
    counts <- table(method[o$device == d])
    counts <- counts[order(names(counts))]
    stats::setNames(lapply(as.integer(counts), identity), names(counts))
  })
  list(by_device = by_device)
}
