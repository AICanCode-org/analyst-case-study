import pytest

from funnellens.stats import cmh, two_proportion, welch
from tests.conftest import STATS_CASES, Z

REL = 1e-9


def approx(value):
    return pytest.approx(value, rel=REL, abs=1e-12)


@pytest.mark.parametrize("case", STATS_CASES["two_proportion"])
def test_two_proportion(case):
    got = two_proportion(case["x1"], case["n1"], case["x2"], case["n2"], Z)
    for key in ("difference", "z", "p_value", "ci95"):
        assert got[key] == approx(case[key]), key


def test_two_proportion_by_hand():
    # 3/10 vs 7/10: pooled p = 0.5, se0 = sqrt(0.25 * 0.2) = 0.2236..., z = -0.4 / 0.2236 = -1.7889
    got = two_proportion(3, 10, 7, 10, Z)
    assert got["z"] == pytest.approx(-1.788854382, rel=1e-9)
    assert got["difference"] == pytest.approx(-0.4)
    assert got["ci95"][0] < -0.4 < got["ci95"][1]


@pytest.mark.parametrize("case", STATS_CASES["cmh"])
def test_cmh(case):
    got = cmh([tuple(t) for t in case["tables"]], Z)
    for key in ("statistic", "p_value", "odds_ratio_mh", "ci95", "crude_odds_ratio"):
        assert got[key] == approx(case[key]), key
    assert got["strata"] == len(case["tables"])


def test_cmh_with_identical_strata_equals_the_single_table_odds_ratio():
    got = cmh([(20, 80, 10, 90), (20, 80, 10, 90)], Z)
    assert got["odds_ratio_mh"] == pytest.approx((20 * 90) / (80 * 10))
    assert got["crude_odds_ratio"] == pytest.approx(got["odds_ratio_mh"])


@pytest.mark.parametrize("case", STATS_CASES["welch"])
def test_welch(case):
    got = welch(case["x"], case["y"])
    for key in ("difference", "t", "df", "p_value", "ci95"):
        assert got[key] == approx(case[key]), key


def test_welch_no_difference():
    got = welch([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert got["t"] == 0 and got["p_value"] == pytest.approx(1.0)
