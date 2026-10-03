#!/usr/bin/env python3
"""Generate FunnelLens' synthetic e-commerce exports (standard library only, fully deterministic).

    python3 scripts/generate_data.py            # (re)write every export under data/raw/
    python3 scripts/generate_data.py --check    # exit 1 if a committed file differs from a fresh run

The data is synthetic but realistic: a 1-in-20 sample of the sessions of a mid-sized Indian online
store, with the defects real exports have (duplicate rows, two date formats, out-of-order and
repeated events, unknown channels, rupee amounts stored as text, refunds, orphan rows). The world
is simulated once (seed below); each export is a view of it on its export date. Nothing here is
real customer data. See data/README.md for the data dictionary and contract/questions.md for the
cleaning rules.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SEED = 20260701
WORLD_START, WORLD_END = date(2026, 1, 1), date(2026, 8, 31)
SAMPLE_RATE = 0.05
EXPORTS = {  # export name -> (period end, extra columns/features present in that export)
    "2026-06": {"period_end": date(2026, 6, 30), "payment_method": False},
    "2026-08": {"period_end": date(2026, 8, 31), "payment_method": True},  # v1.1 refresh
}
CITIES = ["pune", "mumbai", "delhi", "bengaluru", "hyderabad", "chennai", "kolkata", "ahmedabad", "jaipur", "lucknow"]
CITY_W = [14, 18, 16, 15, 10, 8, 6, 5, 4, 4]
ALIASES = {"bengaluru": "Bangalore", "mumbai": "Bombay"}
CHANNELS = ["paid_social", "organic", "email", "unknown", "referral"]
CHANNEL_W = {  # share of sessions per device; 'referral' only exists from July (new programme)
    "mobile": [44, 28, 14, 9, 0],
    "desktop": [14, 46, 30, 10, 0],
}
REFERRAL_FROM = date(2026, 7, 1)
REFERRAL_SHARE = {"mobile": 0.10, "desktop": 0.06}
P_CART = {"paid_social": 0.18, "organic": 0.34, "email": 0.40, "unknown": 0.28, "referral": 0.36}
P_CHECKOUT = {"paid_social": 0.45, "organic": 0.55, "email": 0.60, "unknown": 0.50, "referral": 0.55}
P_PAY = {"paid_social": 0.50, "organic": 0.66, "email": 0.70, "unknown": 0.60, "referral": 0.66}
MOBILE_CART_X, MOBILE_PAY_X = 1.03, 0.90  # within a channel mobile carts slightly MORE but pays less
AOV_MEDIAN = {"paid_social": 1500, "organic": 1650, "email": 1800, "unknown": 1600, "referral": 1700}
PAY_METHODS = {
    "mobile": (["upi", "card", "cod", "netbanking"], [62, 18, 14, 6]),
    "desktop": (["upi", "card", "cod", "netbanking"], [38, 38, 10, 14]),
}
BUG_WEEK = (date(2026, 7, 27), date(2026, 8, 2))  # 2026-W31: app release drops mobile checkout events


def daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


def simulate(rng: random.Random) -> dict:
    users = []
    for uid in range(1, 7001):
        signup = WORLD_START - timedelta(days=200) + timedelta(days=rng.randrange(0, 200 + 243))
        channel = rng.choices(
            ["paid_social", "organic", "email", "referral" if signup >= REFERRAL_FROM else "organic"], [35, 35, 22, 8]
        )[0]
        if rng.random() < 0.08:
            channel = None
        city = rng.choices(CITIES, CITY_W)[0]
        users.append({"user_id": uid, "signup_date": signup, "signup_channel": channel, "city": city})
    by_signup = sorted(users, key=lambda u: (u["signup_date"], u["user_id"]))

    sessions, events, orders = [], [], []
    sid = 0
    oid = 0
    for d in daterange(WORLD_START, WORLD_END):
        eligible = [u for u in by_signup if u["signup_date"] <= d]
        weekday_boost = 1.15 if d.weekday() >= 5 else 1.0
        growth = 1.0 + 0.04 * ((d - WORLD_START).days / 30)
        n = max(60, round(rng.gauss(128 * weekday_boost * growth, 9)))
        mobile_share = 0.655 + 0.0004 * (d - WORLD_START).days
        for _ in range(n):
            sid += 1
            u = rng.choice(eligible)
            device = "mobile" if rng.random() < mobile_share else "desktop"
            ch = rng.choices(CHANNELS, CHANNEL_W[device])[0]
            if d >= REFERRAL_FROM and rng.random() < REFERRAL_SHARE[device]:
                ch = "referral"
            start = datetime(d.year, d.month, d.day) + timedelta(
                minutes=rng.randrange(6 * 60, 24 * 60 - 10)
            )  # export has minutes
            s = {"session_id": f"S{sid:06d}", "user_id": u["user_id"], "device": device, "channel": ch, "start": start}
            sessions.append(s)
            t = start
            steps = []
            if rng.random() < 0.97:
                steps.append("view")
                if rng.random() < P_CART[ch] * (MOBILE_CART_X if device == "mobile" else 1.0):
                    steps.append("cart")
                    if rng.random() < P_CHECKOUT[ch]:
                        steps.append("checkout")
            for step in steps:
                t += timedelta(seconds=rng.randrange(8, 240))
                events.append({"session_id": s["session_id"], "event_name": step, "event_at": t})
            paid = "checkout" in steps and rng.random() < P_PAY[ch] * (MOBILE_PAY_X if device == "mobile" else 1.0)
            # A few orders whose checkout event never reached the tracker (cart reached, order exists).
            ghost = steps == ["view", "cart"] and rng.random() < 0.012
            if paid or ghost:
                oid += 1
                rupees = max(149, round(math.exp(rng.gauss(math.log(AOV_MEDIAN[ch]), 0.6))))
                methods, weights = PAY_METHODS[device]
                orders.append(
                    {
                        "order_id": f"O{oid:06d}",
                        "session_id": s["session_id"],
                        "rupees": rupees,
                        "payment_method": rng.choices(methods, weights)[0],
                        "day": d,
                        "ghost": ghost,
                    }
                )
    return {"users": users, "sessions": sessions, "events": events, "orders": orders}


def fmt_iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%d %H:%M:%S")


def fmt_dmy(t: datetime) -> str:
    return t.strftime("%d/%m/%Y %H:%M")


def messy_case(rng: random.Random, value: str) -> str:
    r = rng.random()
    if r < 0.70:
        return value
    if r < 0.82:
        return value.capitalize()
    if r < 0.92:
        return value.upper()
    return f" {value} "


def money(rng: random.Random, rupees: int) -> str:
    r = rng.random()
    if r < 0.78:
        return f"₹{rupees:,}.00"
    if r < 0.93:
        return str(rupees)
    return f"Rs. {rupees:,}"


def export(world: dict, name: str, spec: dict, seed: int) -> dict[str, list[list[str]]]:
    # One random stream per table, and every row draws the same numbers whether or not it is in this
    # export, so the months two exports share are byte-identical (a refresh only appends).
    ru, rs, re_, ro = (random.Random(seed + i) for i in range(4))
    end = spec["period_end"]
    pm = spec["payment_method"]
    in_bug = lambda t: pm and BUG_WEEK[0] <= t.date() <= BUG_WEEK[1]  # noqa: E731  (only the refreshed export)

    users = [["user_id", "signup_date", "signup_channel", "city"]]
    for u in world["users"]:
        city = u["city"]
        if city in ALIASES and ru.random() < 0.25:
            city = ALIASES[city]
        row = [str(u["user_id"]), u["signup_date"].isoformat(), u["signup_channel"] or "", messy_case(ru, city)]
        if u["signup_date"] <= end:
            users.append(row)

    sessions = [["session_id", "user_id", "device", "channel", "started_at"]]
    kept = set()
    conflicting = 0
    for s in world["sessions"]:
        if s["start"].date() > end:
            continue
        kept.add(s["session_id"])
        ts = fmt_iso(s["start"]) if rs.random() < 0.6 else fmt_dmy(s["start"])
        r = rs.random()
        if r < 0.0015:
            ts = s["start"].strftime("%Y-02-30 %H:%M:%S")  # impossible date from a broken export job
        elif r < 0.0025:
            ts = ""
        elif r < 0.0035:
            ts = fmt_iso(s["start"].replace(year=2062))  # typo'd year, out of the period
        channel = "" if s["channel"] == "unknown" and rs.random() < 0.7 else s["channel"]
        if s["channel"] == "unknown" and channel:
            channel = "(not set)" if rs.random() < 0.5 else "unknown"
        row = [
            s["session_id"],
            str(s["user_id"]),
            messy_case(rs, s["device"]),
            messy_case(rs, channel) if channel and channel not in ("(not set)",) else channel,
            ts,
        ]
        if rs.random() < 0.006:  # orphan: user id from a deleted test account
            row[1] = str(90000 + rs.randrange(1000))
        sessions.append(row)
        r = rs.random()
        if r < 0.010:
            sessions.append(list(row))  # exact duplicate export row
        elif r < 0.016 and ts and "/" not in ts and "2062" not in ts and "-02-30" not in ts:
            dup = list(row)
            dup[4] = fmt_dmy(s["start"])  # same row, other date format: a duplicate only after parsing
            sessions.append(dup)
        elif r < 0.0168 and conflicting < 6:
            dup = list(row)
            dup[2] = "desktop" if s["device"] == "mobile" else "mobile"  # two exports disagree on the device
            sessions.append(dup)
            conflicting += 1

    events = [["session_id", "event_name", "event_at"]]
    last_view: dict[str, list[str]] = {}
    for e in world["events"]:
        if e["session_id"] not in kept:
            continue
        sess = world_sessions[e["session_id"]]
        if (
            e["event_name"] == "checkout"
            and sess["device"] == "mobile"
            and in_bug(e["event_at"])
            and re_.random() < 0.7
        ):
            continue  # tracking bug: event lost
        name = e["event_name"]
        r = re_.random()
        if r < 0.10:
            name = name.capitalize()
        elif r < 0.12:
            name = f"{name} "
        row = [e["session_id"], name, fmt_iso(e["event_at"])]
        events.append(row)
        if e["event_name"] == "view":
            last_view[e["session_id"]] = row
        if e["event_name"] in ("view", "cart") and re_.random() < 0.05:  # repeated step (refresh)
            events.append(
                [e["session_id"], e["event_name"], fmt_iso(e["event_at"] + timedelta(seconds=re_.randrange(3, 90)))]
            )
        if e["event_name"] == "cart" and re_.random() < 0.02 and e["session_id"] in last_view:
            # clock skew between app and server: the cart event is stamped before the view
            events[-1 if events[-1][1].strip().lower() == "cart" else -2][2] = fmt_iso(
                datetime.fromisoformat(last_view[e["session_id"]][2]) - timedelta(seconds=re_.randrange(1, 30))
            )
        if re_.random() < 0.003:
            events.append([e["session_id"], re_.choice(["scroll", "page_ping", "wishlist"]), fmt_iso(e["event_at"])])
    for _ in range(25):
        events.append(
            [
                f"S9{re_.randrange(10**5):05d}",
                "view",
                fmt_iso(datetime(2026, 3, 1, 12) + timedelta(minutes=re_.randrange(10**5))),
            ]
        )

    header = ["order_id", "session_id", "amount"] + (["payment_method"] if pm else [])
    orders = [header]
    for o in world["orders"]:
        if o["session_id"] not in kept:
            continue
        r = ro.random()
        amount = money(ro, o["rupees"])
        if r < 0.004:
            amount = ro.choice(["", "N/A", "1,2O0.00"])
        elif r < 0.014:
            amount = "-" + amount  # refund rows share the export
        elif r < 0.016:
            amount = "0"
        row = [o["order_id"], o["session_id"], amount] + ([o["payment_method"]] if pm else [])
        orders.append(row)
        if ro.random() < 0.005:
            orders.append(list(row))
        if ro.random() < 0.002:
            orders.append(
                [o["order_id"] + "X", f"S8{ro.randrange(10**5):05d}", money(ro, o["rupees"])]
                + ([o["payment_method"]] if pm else [])
            )
    return {"users": users, "sessions": sessions, "events": events, "orders": orders}


def to_csv(rows: list[list[str]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


world_sessions: dict[str, dict] = {}


def build() -> dict[str, dict[str, bytes]]:
    world = simulate(random.Random(SEED))
    world_sessions.update({s["session_id"]: s for s in world["sessions"]})
    out = {}
    for name, spec in sorted(EXPORTS.items()):
        tables = export(world, name, spec, SEED + 1)  # same defect stream for the shared months
        files = {f"{t}.csv": to_csv(rows) for t, rows in tables.items()}
        meta = {
            "export": name,
            "period_start": WORLD_START.isoformat(),
            "period_end": spec["period_end"].isoformat(),
            "sample_rate": SAMPLE_RATE,
            "generator": "scripts/generate_data.py",
            "seed": SEED,
            "files": {f: hashlib.sha256(b).hexdigest() for f, b in sorted(files.items())},
        }
        files["export.json"] = (json.dumps(meta, indent=2) + "\n").encode()
        out[name] = files
    return out


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for name, files in build().items():
        d = RAW / name
        for fname, data in files.items():
            p = d / fname
            if check:
                if not p.exists() or p.read_bytes() != data:
                    stale.append(str(p.relative_to(ROOT)))
            else:
                d.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
        if not check:
            rows = {f: data.count(b"\n") - 1 for f, data in files.items() if f.endswith(".csv")}
            print(f"wrote data/raw/{name}: {rows}")
    if check:
        if stale:
            print("stale (run python3 scripts/generate_data.py):", *stale, sep="\n  ", file=sys.stderr)
            return 1
        print("data/raw is identical to a fresh generation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
