"""M4: the three hypothesis tests of contract/questions.md §4, with SciPy and statsmodels.

The formulas are written out in the contract so the SQL and R tracks can reproduce every number;
these functions use the libraries and the tests in tests/unit/test_stats.py pin them to the
hand-computed cases in contract/fixtures/stats-cases.json.
"""

from __future__ import annotations


def two_proportion(x1: int, n1: int, x2: int, n2: int, z_975: float) -> dict:
    """Group 1 vs group 2: pooled z test (two-sided) and an unpooled Wald 95 % interval of p1 - p2."""
    # TODO(M4) two_proportion: pooled z test for the difference of two proportions + an unpooled 95% CI. Check
    # every value against stats-cases.json. Spec: contract/questions.md §4 (+
    # contract/fixtures/stats-cases.json); tests: stats.
    raise NotImplementedError("TODO(M4) two_proportion: see the comment above")


def cmh(strata: list[tuple[int, int, int, int]], z_975: float) -> dict:
    """Cochran-Mantel-Haenszel test (no continuity correction) over 2x2 tables (a, b, c, d) =
    (group-1 successes, group-1 failures, group-2 successes, group-2 failures), one per stratum.
    Returns the statistic (chi-square, 1 df), its p-value, the Mantel-Haenszel common odds ratio with
    the Robins-Breslow-Greenland 95 % interval, and the crude (pooled-table) odds ratio."""
    # TODO(M4) cmh: Cochran-Mantel-Haenszel over the channel strata: the Mantel-Haenszel odds ratio, its
    # Robins-Breslow-Greenland CI and the CMH chi-square p value (no continuity correction). Spec:
    # contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: stats.
    raise NotImplementedError("TODO(M4) cmh: see the comment above")


def welch(x: list[float], y: list[float]) -> dict:
    """Welch's unequal-variance t test (two-sided) and the 95 % interval of mean(x) - mean(y)."""
    # TODO(M4) welch: Welch's t test (unequal variances) with the Welch-Satterthwaite df and a 95% CI of the
    # difference. Spec: contract/questions.md §4 (+ contract/fixtures/stats-cases.json); tests: stats.
    raise NotImplementedError("TODO(M4) welch: see the comment above")
