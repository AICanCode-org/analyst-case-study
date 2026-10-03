# M3: the funnel, per device, per channel and per ISO week (contract/questions.md section 3).

STEPS <- c("view", "cart", "checkout", "purchase")
DEVICES <- c("desktop", "mobile")

session_funnel <- function(clean) {
  # TODO(M3) session_funnel: one row per clean session with view/cart/checkout/purchase flags; each step
  # requires the previous one (a purchase needs a checkout). Spec: contract/questions.md §3; tests: metrics.
  stop("TODO(M3) session_funnel: see the comment above")
}

ratio <- function(a, b) {
  # TODO(M3) ratio: a / b, or missing (NULL) when b is 0. Spec: contract/questions.md §3; tests: metrics.
  stop("TODO(M3) ratio: see the comment above")
}

funnel_counts <- function(df) {
  # TODO(M3) funnel_counts: sessions and the four step counts of a group of sessions. Spec:
  # contract/questions.md §3; tests: metrics.
  stop("TODO(M3) funnel_counts: see the comment above")
}

with_rates <- function(c) {
  # TODO(M3) with_rates: conversion = purchase / sessions; step rates are step / previous step; a rate of 0/0 is
  # missing (null), never 0. Spec: contract/questions.md §3; tests: metrics.
  stop("TODO(M3) with_rates: see the comment above")
}

funnel_by_device <- function(f, clean) {
  # TODO(M3) funnel_by_device: desktop, mobile and all, with revenue in paise; mobile shares of sessions and
  # revenue. Spec: contract/questions.md §3; tests: metrics.
  stop("TODO(M3) funnel_by_device: see the comment above")
}

by_channel <- function(f) {
  # TODO(M3) by_channel: the funnel per acquisition channel and device, channels in contract order. Spec:
  # contract/questions.md §3; tests: metrics.
  stop("TODO(M3) by_channel: see the comment above")
}

weekly <- function(f) {
  # TODO(M3) weekly: sessions, purchases and conversion per ISO week and device (week = ISO year + '-W' +
  # 2-digit week). Spec: contract/questions.md §3; tests: metrics.
  stop("TODO(M3) weekly: see the comment above")
}
