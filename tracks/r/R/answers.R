# M5: answer the business questions and build answers.json (contract/answers.schema.json).

SCHEMA_VERSION <- "1.0"
CMH_STEPS <- list(cart_given_view = c("cart", "view"), purchase_given_checkout = c("purchase", "checkout"))

track_version <- function() {
  as.character(read.dcf(file.path(track_root(), "DESCRIPTION"), fields = "Version")[1, 1])
}

payment_step_test <- function(funnel, z_975) {
  m <- funnel$by_device$mobile
  d <- funnel$by_device$desktop
  res <- two_proportion(m$purchase, m$checkout, d$purchase, d$checkout, z_975)
  c(list(metric = "purchase_given_checkout",
         mobile = list(n = m$checkout, successes = m$purchase, rate = m$purchase / m$checkout),
         desktop = list(n = d$checkout, successes = d$purchase, rate = d$purchase / d$checkout)),
    res)
}

#' 2x2 tables per channel, only for channels where both devices reached the `base` step.
strata_for <- function(channels, success, base) {
  keep <- Filter(function(r) r$mobile[[base]] > 0 && r$desktop[[base]] > 0, channels)
  stats::setNames(
    lapply(keep, function(r) {
      c(r$mobile[[success]], r$mobile[[base]] - r$mobile[[success]],
        r$desktop[[success]], r$desktop[[base]] - r$desktop[[success]])
    }),
    vapply(keep, function(r) r$channel, "")
  )
}

channel_section <- function(channels, funnel, z_975) {
  tests <- lapply(CMH_STEPS, function(s) cmh_test(unname(strata_for(channels, s[1], s[2])), z_975))
  agg <- funnel$by_device
  aggregate_gap <- agg$mobile$step_rates$cart - agg$desktop$step_rates$cart
  within <- lapply(strata_for(channels, "cart", "view"), function(t) t[1] / (t[1] + t[2]) - t[3] / (t[3] + t[4]))
  gaps <- unlist(within)
  reversal <- (aggregate_gap < 0 && all(gaps > 0)) || (aggregate_gap > 0 && all(gaps < 0))
  list(channels = channels, cmh = tests,
       simpson = list(step = "cart_given_view", aggregate_gap = aggregate_gap,
                      within_channel_gaps = within, reversal = reversal))
}

order_value <- function(clean) {
  o <- dplyr::inner_join(clean$orders, clean$sessions[, c("session_id", "device")], by = "session_id")
  values <- lapply(stats::setNames(DEVICES, DEVICES), function(d) o$amount_paise[o$device == d] / 100)
  summary <- lapply(values, function(v) list(orders = length(v), mean_inr = mean(v), sd_inr = stats::sd(v)))
  res <- welch_test(values$mobile, values$desktop)
  list(mobile = summary$mobile, desktop = summary$desktop, difference_inr = res$difference,
       welch_t = res$t, df = res$df, p_value = res$p_value, ci95 = res$ci95)
}

opportunity <- function(channels, funnel, value, export) {
  strata <- strata_for(channels, "purchase", "checkout")
  rows <- lapply(names(strata), function(ch) {
    t <- strata[[ch]]
    gap <- max(0, t[3] / (t[3] + t[4]) - t[1] / (t[1] + t[2]))
    list(channel = ch, gap = gap, extra_orders = (t[1] + t[2]) * gap)
  })
  total <- sum(vapply(rows, function(r) r$extra_orders, 0))
  scale <- 1 / export$sample_rate
  per_month <- total / export$months * scale
  aov <- value$mobile$mean_inr
  uplift <- per_month * aov
  mobile_monthly <- funnel$by_device$mobile$revenue_paise / 100 / export$months * scale
  list(by_channel = rows, extra_orders_in_sample = total, months = export$months,
       sample_rate = export$sample_rate, extra_orders_per_month = per_month, mobile_aov_inr = aov,
       monthly_revenue_uplift_inr = uplift, mobile_monthly_revenue_inr = mobile_monthly,
       uplift_share_of_mobile_revenue = uplift / mobile_monthly)
}

decision <- function(channel, opp, contract) {
  a <- contract$analysis
  pay <- channel$cmh$purchase_given_checkout
  cart <- channel$cmh$cart_given_view
  if (pay$p_value >= a$alpha) {
    rec <- "no_checkout_gap_found"
    reasons <- "adjusted_payment_gap_not_significant"
  } else if (opp$monthly_revenue_uplift_inr >= a$rebuild_min_monthly_uplift_inr) {
    rec <- "rebuild_checkout"
    reasons <- c("adjusted_payment_gap_significant", "uplift_above_rebuild_threshold")
  } else {
    rec <- "run_targeted_experiment"
    reasons <- c("adjusted_payment_gap_significant", "uplift_below_rebuild_threshold")
  }
  # Mobile carts less overall, but not within channels: the aggregate gap is the channel mix.
  if (channel$simpson$aggregate_gap < 0 && (cart$p_value >= a$alpha || cart$odds_ratio_mh >= 1)) {
    reasons <- c(reasons, "aggregate_cart_gap_is_channel_mix")
  }
  list(recommendation = rec, reasons = I(reasons),
       thresholds = list(alpha = a$alpha, rebuild_min_monthly_uplift_inr = a$rebuild_min_monthly_uplift_inr))
}

build_answers <- function(clean, checks, export, contract) {
  z <- contract$analysis$z_975
  f <- session_funnel(clean)
  funnel <- funnel_by_device(f, clean)
  channels <- by_channel(f)
  channel <- channel_section(channels, funnel, z)
  value <- order_value(clean)
  opp <- opportunity(channels, funnel, value, export)
  list(
    schema = "funnellens-answers",
    schema_version = SCHEMA_VERSION,
    generator = list(track = "r", version = track_version()),
    dataset = list(export = export$name, period_start = format(export$period_start),
                   period_end = format(export$period_end), months = export$months,
                   sample_rate = export$sample_rate, contract_version = contract$version),
    data_quality = list(
      raw_rows = clean$raw_rows,
      clean_rows = lapply(clean[TABLES], nrow),
      issues = clean$issues,
      checks = checks
    ),
    funnel = funnel,
    payment_step_test = payment_step_test(funnel, z),
    by_channel = channel,
    order_value = value,
    weekly = weekly(f),
    opportunity = opp,
    decision = decision(channel, opp, contract)
  )
}
