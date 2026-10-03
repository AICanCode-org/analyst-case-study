# M3: the funnel, per device, per channel and per ISO week (contract/questions.md section 3).

STEPS <- c("view", "cart", "checkout", "purchase")
DEVICES <- c("desktop", "mobile")

session_funnel <- function(clean) {
  has <- function(step) clean$sessions$session_id %in% clean$events$session_id[clean$events$event_name == step]
  f <- clean$sessions[, c("session_id", "device", "channel", "week", "month")]
  f$view <- has("view")
  f$cart <- f$view & has("cart")
  f$checkout <- f$cart & has("checkout")
  f$purchase <- f$checkout & (f$session_id %in% clean$orders$session_id)
  f
}

ratio <- function(a, b) if (b > 0) a / b else NULL

funnel_counts <- function(df) {
  list(sessions = nrow(df), view = sum(df$view), cart = sum(df$cart),
       checkout = sum(df$checkout), purchase = sum(df$purchase))
}

with_rates <- function(c) {
  c$conversion <- ratio(c$purchase, c$sessions)
  c$step_rates <- list(view = ratio(c$view, c$sessions), cart = ratio(c$cart, c$view),
                       checkout = ratio(c$checkout, c$cart), purchase = ratio(c$purchase, c$checkout))
  c
}

funnel_by_device <- function(f, clean) {
  revenue <- dplyr::inner_join(clean$orders, clean$sessions[, c("session_id", "device")], by = "session_id")
  out <- list()
  for (device in c("all", DEVICES)) {
    part <- if (device == "all") f else f[f$device == device, ]
    paise <- if (device == "all") revenue$amount_paise else revenue$amount_paise[revenue$device == device]
    c <- funnel_counts(part)
    c$revenue_paise <- sum(paise)
    out[[device]] <- with_rates(c)
  }
  list(
    steps = I(c("sessions", STEPS)),
    by_device = out,
    mobile_share_of_sessions = out$mobile$sessions / out$all$sessions,
    mobile_share_of_revenue = out$mobile$revenue_paise / out$all$revenue_paise
  )
}

by_channel <- function(f) {
  lapply(sort(unique(f$channel)), function(ch) {
    part <- f[f$channel == ch, ]
    list(channel = ch,
         desktop = funnel_counts(part[part$device == "desktop", ]),
         mobile = funnel_counts(part[part$device == "mobile", ]))
  })
}

weekly <- function(f) {
  lapply(sort(unique(f$week)), function(w) {
    part <- f[f$week == w, ]
    sessions <- lapply(stats::setNames(DEVICES, DEVICES), function(d) sum(part$device == d))
    purchases <- lapply(stats::setNames(DEVICES, DEVICES), function(d) sum(part$purchase[part$device == d]))
    conversion <- lapply(stats::setNames(DEVICES, DEVICES), function(d) {
      if (sessions[[d]] > 0) purchases[[d]] / sessions[[d]] else NA
    })
    list(week = w, sessions = sessions, purchases = purchases, conversion = conversion)
  })
}
