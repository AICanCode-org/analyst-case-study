"""M4: the three hypothesis tests of contract/questions.md §4, with SciPy and statsmodels.

The formulas are written out in the contract so the SQL and R tracks can reproduce every number;
these functions use the libraries and the tests in tests/unit/test_stats.py pin them to the
hand-computed cases in contract/fixtures/stats-cases.json.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.proportion import proportions_ztest


def two_proportion(x1: int, n1: int, x2: int, n2: int, z_975: float) -> dict:
    """Group 1 vs group 2: pooled z test (two-sided) and an unpooled Wald 95 % interval of p1 - p2."""
    p1, p2 = x1 / n1, x2 / n2
    z, p_value = proportions_ztest([x1, x2], [n1, n2], alternative="two-sided", prop_var=False)
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    diff = p1 - p2
    return {
        "difference": diff,
        "ci95": [diff - z_975 * se, diff + z_975 * se],
        "z": float(z),
        "p_value": float(p_value),
    }


def cmh(strata: list[tuple[int, int, int, int]], z_975: float) -> dict:
    """Cochran-Mantel-Haenszel test (no continuity correction) over 2x2 tables (a, b, c, d) =
    (group-1 successes, group-1 failures, group-2 successes, group-2 failures), one per stratum.
    Returns the statistic (chi-square, 1 df), its p-value, the Mantel-Haenszel common odds ratio with
    the Robins-Breslow-Greenland 95 % interval, and the crude (pooled-table) odds ratio."""
    tables = np.array([[[a, b], [c, d]] for a, b, c, d in strata], dtype=float).transpose(1, 2, 0)
    st = StratifiedTable(tables)
    test = st.test_null_odds(correction=False)
    se = st.logodds_pooled_se
    log_or = math.log(st.oddsratio_pooled)
    a, b, c, d = (sum(t[i] for t in strata) for i in range(4))
    return {
        "statistic": float(test.statistic),
        "p_value": float(test.pvalue),
        "odds_ratio_mh": float(st.oddsratio_pooled),
        "ci95": [math.exp(log_or - z_975 * se), math.exp(log_or + z_975 * se)],
        "crude_odds_ratio": (a * d) / (b * c),
        "strata": len(strata),
    }


def welch(x: list[float], y: list[float]) -> dict:
    """Welch's unequal-variance t test (two-sided) and the 95 % interval of mean(x) - mean(y)."""
    res = stats.ttest_ind(x, y, equal_var=False)
    ci = res.confidence_interval(0.95)
    return {
        "difference": float(np.mean(x) - np.mean(y)),
        "t": float(res.statistic),
        "df": float(res.df),
        "p_value": float(res.pvalue),
        "ci95": [float(ci.low), float(ci.high)],
    }
