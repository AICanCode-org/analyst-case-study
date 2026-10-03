# M5: answer the business questions and build answers.json (contract/answers.schema.json).

SCHEMA_VERSION <- "1.0"
CMH_STEPS <- list(cart_given_view = c("cart", "view"), purchase_given_checkout = c("purchase", "checkout"))

track_version <- function() {
  as.character(read.dcf(file.path(track_root(), "DESCRIPTION"), fields = "Version")[1, 1])
}

payment_step_test <- function(funnel, z_975) {
  # TODO(M5) payment_step_test: mobile vs desktop purchase given checkout, unadjusted (the number the Head of
  # Product quotes). Spec: contract/questions.md §5 and contract/answers.schema.json; tests: answers.
  stop("TODO(M5) payment_step_test: see the comment above")
}

#' 2x2 tables per channel, only for channels where both devices reached the `base` step.
strata_for <- function(channels, success, base) {
  # TODO(M5) strata_for: 2x2 tables per channel, only where BOTH devices reached the base step. Spec:
  # contract/questions.md §5 and contract/answers.schema.json; tests: answers.
  stop("TODO(M5) strata_for: see the comment above")
}

channel_section <- function(channels, funnel, z_975) {
  # TODO(M5) channel_section: CMH for cart|view and purchase|checkout, and the Simpson check: does the aggregate
  # cart gap survive within channels? Spec: contract/questions.md §5 and contract/answers.schema.json; tests:
  # answers.
  stop("TODO(M5) channel_section: see the comment above")
}

order_value <- function(clean) {
  # TODO(M5) order_value: Welch test of mobile vs desktop order values in rupees. Spec: contract/questions.md §5
  # and contract/answers.schema.json; tests: answers.
  stop("TODO(M5) order_value: see the comment above")
}

opportunity <- function(channels, funnel, value, export) {
  # TODO(M5) opportunity: extra orders if mobile paid like desktop within each channel, scaled by months and the
  # sample rate, times the mobile AOV. Spec: contract/questions.md §5 and contract/answers.schema.json; tests:
  # answers.
  stop("TODO(M5) opportunity: see the comment above")
}

decision <- function(channel, opp, contract) {
  # TODO(M5) decision: the three-way rule of §5: not significant -> no_checkout_gap_found; uplift >= threshold
  # -> rebuild_checkout; else run_targeted_experiment. Spec: contract/questions.md §5 and
  # contract/answers.schema.json; tests: answers.
  stop("TODO(M5) decision: see the comment above")
}

build_answers <- function(clean, checks, export, contract) {
  # TODO(M5) build_answers: assemble answers.json exactly as contract/answers.schema.json describes; the parity
  # script compares it with the other tracks to 1e-9. Spec: contract/questions.md §5 and
  # contract/answers.schema.json; tests: answers.
  stop("TODO(M5) build_answers: see the comment above")
}
