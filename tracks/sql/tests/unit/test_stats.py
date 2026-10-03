"""The SQL statistics in sql/04_stats.sql, fed with the shared reference cases through stub tables."""

import math

import pytest

from funnellens_sql import mathfn, runner
from tests.conftest import STATS_CASES

REL = 1e-9
STEPS = ("view", "cart", "checkout", "purchase")


def approx(value):
    return pytest.approx(value, rel=REL, abs=1e-12)


def stats_con(grid=(), funnel=(), orders=()):
    """Stub the M3 tables that 04_stats.sql reads, then run it."""
    con = runner.connect()
    con.execute("SET VARIABLE z_975 = 1.959963984540054")
    con.execute(
        "CREATE TABLE channel_device_grid (channel VARCHAR, device VARCHAR, view BIGINT, cart BIGINT, "
        "checkout BIGINT, purchase BIGINT)"
    )
    if grid:
        con.executemany("INSERT INTO channel_device_grid VALUES (?, ?, ?, ?, ?, ?)", list(grid))
    con.execute("CREATE TABLE funnel_by_device (device VARCHAR, checkout DOUBLE, purchase DOUBLE, rate_cart DOUBLE)")
    if funnel:
        con.executemany("INSERT INTO funnel_by_device VALUES (?, ?, ?, ?)", list(funnel))
    con.execute("CREATE TABLE sessions (session_id VARCHAR, device VARCHAR)")
    con.execute("CREATE TABLE orders (session_id VARCHAR, amount_paise DOUBLE)")
    for i, (device, value) in enumerate(orders):
        con.execute("INSERT INTO sessions VALUES (?, ?)", [f"S{i}", device])
        con.execute("INSERT INTO orders VALUES (?, ?)", [f"S{i}", value * 100])
    runner.run_script(con, "04_stats.sql")
    return con


def one(con, view):
    cur = con.execute(f"SELECT * FROM {view}")
    return dict(zip([d[0] for d in cur.description], cur.fetchone(), strict=True))


@pytest.mark.parametrize("case", STATS_CASES["two_proportion"])
def test_two_proportion(case):
    funnel = [("mobile", case["n1"], case["x1"], 0.5), ("desktop", case["n2"], case["x2"], 0.5)]
    got = one(stats_con(funnel=funnel), "payment_step_test")
    assert got["difference"] == approx(case["difference"])
    assert got["z"] == approx(case["z"])
    assert got["p_value"] == approx(case["p_value"])
    assert [got["ci_low"], got["ci_high"]] == [approx(case["ci95"][0]), approx(case["ci95"][1])]


@pytest.mark.parametrize("case", STATS_CASES["cmh"])
def test_cmh(case):
    grid = []
    for i, (a, b, c, d) in enumerate(case["tables"]):
        grid += [(f"c{i}", "mobile", a + b, a + b, a + b, a), (f"c{i}", "desktop", c + d, c + d, c + d, c)]
    got = one(
        stats_con(grid=grid).execute("CREATE VIEW p AS SELECT * FROM cmh WHERE step = 'purchase_given_checkout'"), "p"
    )
    for key in ("statistic", "p_value", "odds_ratio_mh", "crude_odds_ratio"):
        assert got[key] == approx(case[key]), key
    assert [got["ci_low"], got["ci_high"]] == [approx(case["ci95"][0]), approx(case["ci95"][1])]
    assert got["strata"] == len(case["tables"])


def test_cmh_skips_a_channel_missing_a_device():
    grid = [("a", "mobile", 50, 40, 30, 10), ("a", "desktop", 50, 40, 30, 20), ("b", "mobile", 9, 5, 3, 1)]
    got = one(
        stats_con(grid=grid).execute("CREATE VIEW p AS SELECT * FROM cmh WHERE step = 'purchase_given_checkout'"), "p"
    )
    assert got["strata"] == 1


@pytest.mark.parametrize("case", STATS_CASES["welch"])
def test_welch(case):
    orders = [("mobile", v) for v in case["x"]] + [("desktop", v) for v in case["y"]]
    got = one(stats_con(orders=orders), "welch")
    for key, col in (("difference", "difference"), ("t", "t"), ("df", "df"), ("p_value", "p_value")):
        assert got[col] == approx(case[key]), key
    assert [got["ci_low"], got["ci_high"]] == [approx(case["ci95"][0]), approx(case["ci95"][1])]


@pytest.mark.parametrize(
    ("t", "df", "p"), [(0.0, 5.0, 1.0), (2.0, 10.0, 0.07338803477074), (-2.0, 10.0, 0.07338803477074)]
)
def test_t_two_sided_p(t, df, p):
    assert mathfn.t_two_sided_p(t, df) == pytest.approx(p, rel=1e-9)


def test_t_quantile_inverts_the_cdf():
    for df in (1.5, 7.77, 30.0, 2114.0):
        q = mathfn.t_quantile(0.975, df)
        assert mathfn.t_two_sided_p(q, df) == pytest.approx(0.05, rel=1e-9)
    assert mathfn.erfc(0.0) == 1.0 and math.isclose(mathfn.erfc(10.0), 0.0, abs_tol=1e-40)
