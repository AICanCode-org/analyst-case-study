"""FunnelLens v1.0 dashboard. Run: streamlit run app.py (after `make prepare`).

Reads static/answers.json (any track's output, validated by `prepare`) and static/narrative.json.
Everything shown is an aggregate from answers.json; there is no raw data in this app.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from funnellens_dashboard import __version__
from funnellens_dashboard.facts import RECOMMENDATION_LABELS

STATIC = Path(os.environ.get("STATIC_DIR", Path(__file__).resolve().parent / "static"))
DEVICES = ["desktop", "mobile"]


def read(name: str) -> dict | None:
    path = STATIC / name
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def escape_md(text: str) -> str:
    """Show model text literally: escape every Markdown control character."""
    return "".join("\\" + c if c in "\\`*_{}[]()#+-.!|<>$~" else c for c in text)


def main() -> None:
    st.set_page_config(page_title="FunnelLens", page_icon="🔎", layout="wide")
    answers = read("answers.json")
    if answers is None:
        st.error("No answers yet. Run a track pipeline, then `make prepare` (see README).")
        st.stop()
    narrative = read("narrative.json")
    ds = answers["dataset"]
    st.title("FunnelLens · mobile checkout decision")
    st.caption(
        f"Export {ds['export']} · {ds['period_start']} to {ds['period_end']} · contract {ds['contract_version']}"
        f" · {answers['generator']['track']} track · dashboard v{__version__}"
    )

    rec = answers["decision"]["recommendation"]
    f = answers["funnel"]
    opp = answers["opportunity"]
    pay = answers["by_channel"]["cmh"]["purchase_given_checkout"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mobile share of sessions", f"{f['mobile_share_of_sessions']:.1%}")
    c2.metric("Mobile share of revenue", f"{f['mobile_share_of_revenue']:.1%}")
    c3.metric("Payment odds ratio (within channels)", f"{pay['odds_ratio_mh']:.2f}")
    c4.metric("Monthly uplift if closed", f"₹{opp['monthly_revenue_uplift_inr'] / 1e5:.1f} lakh")
    st.subheader(f"Recommendation: {RECOMMENDATION_LABELS[rec]}")
    st.write("Reasons: " + ", ".join(f"`{r}`" for r in answers["decision"]["reasons"]))

    if narrative:
        label = "AI summary" if narrative["source"] == "llm" else "Summary (template)"
        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.markdown(escape_md(narrative["text"]))
            if narrative["fallback"]:
                st.caption(f"The AI narrator was not used: {narrative['reason']}. Showing the deterministic template.")

    tabs = st.tabs(["Funnel", "Payment step", "Channels", "Order value", "Weekly", "Data quality"])
    with tabs[0]:
        rates = pd.DataFrame({d: f["by_device"][d]["step_rates"] for d in DEVICES})
        st.bar_chart(rates, stack=False)
        st.dataframe(pd.DataFrame({d: {s: f["by_device"][d][s] for s in f["steps"]} for d in DEVICES}))
    with tabs[1]:
        p = answers["payment_step_test"]
        st.write(
            f"Mobile {p['mobile']['rate']:.1%} vs desktop {p['desktop']['rate']:.1%} of checkouts purchase: "
            f"{100 * p['difference']:+.1f} pp (95% CI {100 * p['ci95'][0]:.1f} to {100 * p['ci95'][1]:.1f}), "
            f"z = {p['z']:.2f}."
        )
        st.dataframe(pd.DataFrame(answers["by_channel"]["cmh"]).T)
    with tabs[2]:
        rows = [
            {"channel": c["channel"], "device": d, **c[d]} for c in answers["by_channel"]["channels"] for d in DEVICES
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.dataframe(pd.DataFrame(opp["by_channel"]), hide_index=True)
    with tabs[3]:
        v = answers["order_value"]
        st.write(
            f"Mobile ₹{v['mobile']['mean_inr']:,.0f} vs desktop ₹{v['desktop']['mean_inr']:,.0f} per order "
            f"(Welch p = {v['p_value']:.2f})."
        )
    with tabs[4]:
        weekly = pd.DataFrame([{"week": w["week"], **w["conversion"]} for w in answers["weekly"]]).set_index("week")
        st.line_chart(weekly)
    with tabs[5]:
        dq = answers["data_quality"]
        st.dataframe(
            pd.DataFrame(dq["checks"])[["id", "severity", "status", "failing_rows", "observed"]], hide_index=True
        )
        st.dataframe(pd.Series(dq["issues"], name="rows"))
    st.download_button(
        "Download the decision memo (Markdown)",
        (STATIC / "onepager.md").read_bytes() if (STATIC / "onepager.md").is_file() else b"",
        file_name="funnellens-memo.md",
    )


main()
