from funnellens.metrics import by_channel, funnel_by_device, session_funnel, weekly
from tests.conftest import EXPECTED


def test_funnel_by_device(tiny):
    clean, _ = tiny
    f = funnel_by_device(session_funnel(clean), clean)
    got = {d: {k: v[k] for k in EXPECTED["funnel"][d]} for d, v in f["by_device"].items()}
    assert got == EXPECTED["funnel"]
    assert f["steps"] == ["sessions", "view", "cart", "checkout", "purchase"]
    assert f["mobile_share_of_sessions"] == 0.5
    assert f["mobile_share_of_revenue"] == 209900 / 809950


def test_rates_use_the_previous_step_as_denominator(tiny):
    clean, _ = tiny
    mobile = funnel_by_device(session_funnel(clean), clean)["by_device"]["mobile"]
    assert mobile["conversion"] == 1 / 4
    assert mobile["step_rates"] == {"view": 3 / 4, "cart": 3 / 3, "checkout": 2 / 3, "purchase": 1 / 2}


def test_funnel_is_monotone_and_needs_every_previous_step(tiny):
    clean, _ = tiny
    f = session_funnel(clean).set_index("session_id")
    assert not f.loc["S12", "cart"]  # a cart event without a view does not count
    assert not f.loc["S2", "purchase"]  # an order without checkout is revenue, not a funnel purchase
    assert not f.loc["S6", "purchase"]  # checkout but its only order is unparseable
    assert (f["cart"] <= f["view"]).all()
    assert (f["checkout"] <= f["cart"]).all()
    assert (f["purchase"] <= f["checkout"]).all()


def test_by_channel_lists_every_channel_and_both_devices(tiny):
    clean, _ = tiny
    assert by_channel(session_funnel(clean)) == EXPECTED["channels"]


def test_weekly(tiny):
    clean, _ = tiny
    assert weekly(session_funnel(clean)) == EXPECTED["weekly"]


def test_a_rate_with_no_denominator_is_none(tiny):
    clean, _ = tiny
    only_mobile = clean.sessions[clean.sessions["device"] == "mobile"]
    clean.sessions = only_mobile
    f = funnel_by_device(session_funnel(clean), clean)
    assert f["by_device"]["desktop"]["conversion"] is None
    assert f["by_device"]["desktop"]["step_rates"]["purchase"] is None
    w = weekly(session_funnel(clean))
    assert w[0]["conversion"]["desktop"] is None
