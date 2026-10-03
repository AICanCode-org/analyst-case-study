"""The three distribution functions SQL does not have, registered in DuckDB by the runner.

Standard library only. t_two_sided_p uses the regularized incomplete beta function
I_x(a, b) (continued fraction, Numerical Recipes 6.4); t_quantile inverts the CDF by bisection.
Accurate to ~1e-13, which the golden test (1e-9 relative) checks against SciPy and R.
"""

from __future__ import annotations

import math


def erfc(x: float) -> float:
    return math.erfc(x)


def _betacf(a: float, b: float, x: float) -> float:
    tiny, eps = 1e-300, 1e-16
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 10_000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b) for 0 <= x <= 1."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_front = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(log_front) * _betacf(a, b, x) / a
    return 1.0 - math.exp(log_front) * _betacf(b, a, 1.0 - x) / b


def t_two_sided_p(t: float, df: float) -> float:
    """P(|T| >= |t|) for Student's t with df degrees of freedom (df may be fractional)."""
    return betainc(df / 2.0, 0.5, df / (df + t * t))


def t_cdf(t: float, df: float) -> float:
    tail = 0.5 * t_two_sided_p(t, df)
    return 1.0 - tail if t > 0 else tail


def t_quantile(p: float, df: float) -> float:
    """The t such that P(T <= t) = p (0 < p < 1), by bisection to machine precision."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    lo, hi = -1.0, 1.0
    while t_cdf(lo, df) > p:
        lo *= 2.0
    while t_cdf(hi, df) < p:
        hi *= 2.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo <= 1e-15 * max(1.0, abs(mid)):
            break
    return (lo + hi) / 2.0
