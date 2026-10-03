"""M3: the funnel, per device, per channel and per ISO week (contract/questions.md §3)."""

from __future__ import annotations

import pandas as pd

from .clean import Clean

STEPS = ["view", "cart", "checkout", "purchase"]
DEVICES = ["desktop", "mobile"]


def session_funnel(clean: Clean) -> pd.DataFrame:
    """One row per clean session with booleans view/cart/checkout/purchase (each implies the previous)."""
    # TODO(M3) session_funnel: one row per clean session with view/cart/checkout/purchase flags; each step
    # requires the previous one (a purchase needs a checkout). Spec: contract/questions.md §3; tests: metrics.
    raise NotImplementedError("TODO(M3) session_funnel: see the comment above")


def counts(df: pd.DataFrame) -> dict:
    # TODO(M3) counts: sessions and the four step counts of a group of sessions. Spec: contract/questions.md §3;
    # tests: metrics.
    raise NotImplementedError("TODO(M3) counts: see the comment above")


def rates(c: dict) -> dict:
    # TODO(M3) rates: conversion = purchase / sessions; step rates are step / previous step; 0/0 is missing
    # (null), never 0. Spec: contract/questions.md §3; tests: metrics.
    raise NotImplementedError("TODO(M3) rates: see the comment above")


def funnel_by_device(funnel: pd.DataFrame, clean: Clean) -> dict:
    # TODO(M3) funnel_by_device: desktop, mobile and all, with revenue in paise; mobile shares of sessions and
    # revenue. Spec: contract/questions.md §3; tests: metrics.
    raise NotImplementedError("TODO(M3) funnel_by_device: see the comment above")


def by_channel(funnel: pd.DataFrame) -> list[dict]:
    # TODO(M3) by_channel: the funnel per acquisition channel and device, channels in contract order. Spec:
    # contract/questions.md §3; tests: metrics.
    raise NotImplementedError("TODO(M3) by_channel: see the comment above")


def weekly(funnel: pd.DataFrame) -> list[dict]:
    # TODO(M3) weekly: sessions, purchases and conversion per ISO week and device (week = ISO year + '-W' +
    # 2-digit week). Spec: contract/questions.md §3; tests: metrics.
    raise NotImplementedError("TODO(M3) weekly: see the comment above")
