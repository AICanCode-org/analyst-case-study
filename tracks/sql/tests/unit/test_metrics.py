from tests.conftest import EXPECTED


def by_device(con):
    cur = con.execute("SELECT * FROM funnel_by_device")
    names = [d[0] for d in cur.description]
    return {r[0]: dict(zip(names, r, strict=True)) for r in cur.fetchall()}


def test_funnel_by_device(tiny_metrics):
    f = by_device(tiny_metrics)
    got = {d: {k: f[d][k] for k in EXPECTED["funnel"][d]} for d in EXPECTED["funnel"]}
    assert got == EXPECTED["funnel"]
    assert f["mobile"]["sessions"] / f["all"]["sessions"] == 0.5
    assert f["mobile"]["revenue_paise"] / f["all"]["revenue_paise"] == 209900 / 809950


def test_rates_use_the_previous_step_as_denominator(tiny_metrics):
    m = by_device(tiny_metrics)["mobile"]
    assert m["conversion"] == 1 / 4
    assert [m["rate_view"], m["rate_cart"], m["rate_checkout"], m["rate_purchase"]] == [3 / 4, 3 / 3, 2 / 3, 1 / 2]


def test_funnel_is_monotone_and_needs_every_previous_step(tiny_metrics):
    f = {
        r[0]: r[1:]
        for r in tiny_metrics.execute(
            "SELECT session_id, view, cart, checkout, purchase FROM session_funnel"
        ).fetchall()
    }
    assert not f["S12"][1]  # a cart event without a view does not count
    assert not f["S2"][3]  # an order without checkout is revenue, not a funnel purchase
    assert not f["S6"][3]  # checkout but its only order is unparseable
    bad = tiny_metrics.execute(
        "SELECT count(*) FROM session_funnel WHERE cart > view OR checkout > cart OR purchase > checkout"
    )
    assert bad.fetchone()[0] == 0


def test_by_channel_lists_every_channel_and_both_devices(tiny_metrics):
    keys = ["sessions", "view", "cart", "checkout", "purchase"]
    grid = tiny_metrics.execute(f"SELECT channel, device, {', '.join(keys)} FROM channel_device_grid").fetchall()
    got = {}
    for channel, device, *values in grid:
        got.setdefault(channel, {"channel": channel})[device] = dict(zip(keys, values, strict=True))
    assert [got[c] for c in sorted(got)] == EXPECTED["channels"]


def test_weekly(tiny_metrics):
    rows = tiny_metrics.execute("SELECT * FROM weekly").fetchall()
    got = [
        {
            "week": w,
            "sessions": {"desktop": sd, "mobile": sm},
            "purchases": {"desktop": pd, "mobile": pm},
            "conversion": {"desktop": pd / sd if sd else None, "mobile": pm / sm if sm else None},
        }
        for w, sd, sm, pd, pm in [(r[0], r[1], r[2], r[3], r[4]) for r in rows]
    ]
    assert got == EXPECTED["weekly"]


def test_a_rate_with_no_denominator_is_null(tiny_metrics):
    tiny_metrics.execute("DELETE FROM session_funnel WHERE device = 'desktop'")
    desktop = by_device(tiny_metrics)["desktop"]
    assert (desktop["sessions"], desktop["conversion"], desktop["rate_purchase"]) == (0, None, None)
    week = tiny_metrics.execute("SELECT sessions_desktop, purchases_desktop FROM weekly ORDER BY week").fetchone()
    assert week == (0, 0)  # the runner turns 0 / 0 into null
