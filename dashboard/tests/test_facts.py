from funnellens_dashboard.facts import build_facts, facts_block


def test_facts_are_numbered_aggregates(answers):
    facts = build_facts(answers)
    assert [f.id for f in facts] == [f"F{i}" for i in range(1, 10)]
    text = facts_block(facts)
    assert "Mobile is 69.2% of sessions but 60.6% of revenue." in text
    assert "₹16.3 lakh a month" in text and "₹25.0 lakh a month" in text
    assert "odds ratio 0.71 (95% CI 0.62 to 0.81, p < 0.001)" in text
    assert facts[-1].text == "Recommendation: run a targeted experiment on the mobile payment step."


def test_facts_never_contain_row_level_identifiers(answers):
    text = facts_block(build_facts(answers))
    for marker in ("S0", "O0", "user_id", "session_id", "order_id"):
        assert marker not in text


def test_small_p_values_are_reported_as_a_bound(answers):
    answers["order_value"]["p_value"] = 0.0004
    assert "(p < 0.001)" in build_facts(answers)[5].text


def test_v1_1_answers_add_monitoring_and_payment_facts(answers_v11):
    facts = build_facts(answers_v11)
    assert [f.id for f in facts] == [f"F{i}" for i in range(1, 12)]
    assert facts[9].text == (
        f"Monitoring checked {len(answers_v11['monitoring']['weeks'])} full weeks: 0 deviate from the median week "
        "by more than 30%. Excluded for broken tracking: 2026-W31 (1,218 sessions)."
    )
    assert facts[10].text.startswith("The most used mobile payment method is upi (")


def test_monitoring_without_excluded_weeks(answers_v11):
    answers_v11["monitoring"]["excluded_weeks"] = []
    answers_v11["payment_methods"] = None
    facts = build_facts(answers_v11)
    assert len(facts) == 10 and "Excluded" not in facts[-1].text
