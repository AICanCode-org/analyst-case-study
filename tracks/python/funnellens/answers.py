"""M5: answer the business questions and write answers.json (contract/answers.schema.json)."""

from __future__ import annotations

from .clean import Clean
from .contract import Export

SCHEMA_VERSION = "1.0"
CMH_STEPS = {"cart_given_view": ("cart", "view"), "purchase_given_checkout": ("purchase", "checkout")}


def payment_step_test(funnel: dict, z_975: float) -> dict:
    # TODO(M5) payment_step_test: mobile vs desktop purchase given checkout, unadjusted (the number the Head of
    # Product quotes). Spec: contract/questions.md §5 and contract/answers.schema.json; tests: answers.
    raise NotImplementedError("TODO(M5) payment_step_test: see the comment above")


def strata(channels: list[dict], success: str, base: str) -> list[tuple[str, tuple[int, int, int, int]]]:
    """2x2 tables (mobile successes, mobile failures, desktop successes, desktop failures) per channel,
    keeping only channels where both devices have at least one session at the `base` step."""
    # TODO(M5) strata: 2x2 tables per channel, only where BOTH devices reached the base step. Spec:
    # contract/questions.md §5 and contract/answers.schema.json; tests: answers.
    raise NotImplementedError("TODO(M5) strata: see the comment above")


def channel_section(channels: list[dict], funnel: dict, z_975: float) -> dict:
    # TODO(M5) channel_section: CMH for cart|view and purchase|checkout, and the Simpson check: does the
    # aggregate cart gap survive within channels? Spec: contract/questions.md §5 and
    # contract/answers.schema.json; tests: answers.
    raise NotImplementedError("TODO(M5) channel_section: see the comment above")


def order_value(clean: Clean) -> dict:
    # TODO(M5) order_value: Welch test of mobile vs desktop order values in rupees. Spec: contract/questions.md
    # §5 and contract/answers.schema.json; tests: answers.
    raise NotImplementedError("TODO(M5) order_value: see the comment above")


def opportunity(channels: list[dict], funnel: dict, value: dict, export: Export) -> dict:
    # TODO(M5) opportunity: extra orders if mobile paid like desktop within each channel, scaled by months and
    # the sample rate, times the mobile AOV. Spec: contract/questions.md §5 and contract/answers.schema.json;
    # tests: answers.
    raise NotImplementedError("TODO(M5) opportunity: see the comment above")


def decision(channel: dict, opp: dict, contract: dict) -> dict:
    # TODO(M5) decision: the three-way rule of §5: not significant -> no_checkout_gap_found; uplift >= threshold
    # -> rebuild_checkout; else run_targeted_experiment. Spec: contract/questions.md §5 and
    # contract/answers.schema.json; tests: answers.
    raise NotImplementedError("TODO(M5) decision: see the comment above")


def build_answers(clean: Clean, checks: list[dict], export: Export, contract: dict, track: str = "python") -> dict:
    # TODO(M5) build_answers: assemble answers.json exactly as contract/answers.schema.json describes; the
    # parity script compares it with the other tracks to 1e-9. Spec: contract/questions.md §5 and
    # contract/answers.schema.json; tests: answers.
    raise NotImplementedError("TODO(M5) build_answers: see the comment above")
