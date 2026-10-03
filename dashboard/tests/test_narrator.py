import pytest

from funnellens_dashboard.facts import build_facts
from funnellens_dashboard.narrator import Settings, allowed, narrate, sanitise, template_text, validate

GOOD = (
    "Mobile is 69.2% of sessions but 60.6% of revenue [F2]. The gap is at payment: 54.4% of mobile checkouts "
    "purchase vs 65.6% on desktop [F3], and it remains within channels (odds ratio 0.71) [F4]. Closing it is worth "
    "about ₹16.3 lakh a month [F7], below the ₹25 lakh rebuild threshold [F8]. We recommend a targeted experiment "
    "on the mobile payment step [F9]; the data is observational."
)


def llm(url, **kw):
    return Settings(provider="llm", base_url=url, model="fake", timeout_ms=kw.pop("timeout_ms", 2000), **kw)


def test_offline_by_default_uses_the_template(answers):
    n = narrate(answers, Settings())
    assert (n.source, n.fallback, n.reason) == ("template", False, None)
    assert n.text == template_text(build_facts(answers))
    assert narrate(answers, Settings()).text == n.text  # deterministic


def test_the_template_passes_its_own_guardrails(answers):
    facts = build_facts(answers)
    assert validate(template_text(facts), facts, "run_targeted_experiment") is None


def test_a_good_model_answer_is_used(answers, fake_llm):
    fake_llm.reply = GOOD
    n = narrate(answers, llm(fake_llm.url))
    assert (n.source, n.fallback, n.model) == ("llm", False, "fake")
    assert n.text == GOOD


def test_the_model_only_sees_numbered_facts(answers, fake_llm):
    fake_llm.reply = GOOD
    narrate(answers, llm(fake_llm.url, api_key="sk-test-not-real"))
    request = fake_llm.requests[0]
    assert request["auth"] == "Bearer sk-test-not-real"
    user = request["body"]["messages"][1]["content"]
    assert user.startswith("Facts:\n[F1] ") and "S000" not in user and "O000" not in user
    assert request["body"]["temperature"] == 0


@pytest.mark.parametrize(
    ("reply", "reason"),
    [
        (GOOD.replace("69.2%", "72.5%"), "number not in the facts: 72.5"),
        (GOOD.replace("₹16.3 lakh", "₹40 lakh"), "number not in the facts: 40"),
        (GOOD.replace("the data is observational", "this proves the device is the problem"), "causal over-claim"),
        (GOOD.replace("The gap is at payment", "The slow page caused the gap"), "causal over-claim: 'caused'"),
        (
            GOOD.replace("We recommend a targeted experiment on", "Focus on").replace(
                "; the data is observational", ""
            ),
            "does not state the recommendation",
        ),
        ("Mobile converts worse [F2] [F3]. Run an experiment.", None),
        ("Mobile converts worse [F2]. Run an experiment.", "fewer than 2 fact citations"),
        (GOOD + " [F42]", "cites a fact that does not exist"),
        (GOOD * 3, "too long"),
        ("", "empty answer"),
        (GOOD.replace("[F9]", "[F9] (export 2025-12)"), "date not in the facts: 2025-12"),
    ],
)
def test_guardrails(answers, reply, reason):
    facts = build_facts(answers)
    problem = validate(sanitise(reply), facts, "run_targeted_experiment")
    if reason is None:
        assert problem is None
    else:
        assert problem is not None and problem.startswith(reason), problem


def test_a_rejected_answer_falls_back_to_the_template(answers, fake_llm):
    fake_llm.reply = GOOD.replace("69.2%", "80%")
    n = narrate(answers, llm(fake_llm.url))
    assert (n.source, n.fallback) == ("template", True)
    assert n.reason == "guardrail: number not in the facts: 80"


def test_markup_is_stripped(answers, fake_llm):
    fake_llm.reply = "<script>alert(1)</script>**" + GOOD + "**"
    n = narrate(answers, llm(fake_llm.url))
    assert n.source == "llm" and "<" not in n.text and "*" not in n.text


@pytest.mark.parametrize(
    ("status", "raw", "reason"),
    [
        (500, None, "provider unreachable: HTTPError"),
        (200, "not json", "unexpected provider response: JSONDecodeError"),
        (200, '{"choices": []}', "unexpected provider response: IndexError"),
    ],
)
def test_provider_errors_fall_back(answers, fake_llm, status, raw, reason):
    fake_llm.status, fake_llm.raw = status, raw
    n = narrate(answers, llm(fake_llm.url))
    assert (n.source, n.fallback, n.reason) == ("template", True, reason)


def test_unreachable_provider_falls_back_quickly(answers):
    n = narrate(answers, llm("http://127.0.0.1:9/v1", timeout_ms=500))  # port 9: discard, nothing listens
    assert (n.source, n.fallback) == ("template", True)
    assert n.reason.startswith("provider unreachable")


def test_settings_from_env_never_expose_the_key():
    s = Settings.from_env(
        {"AI_PROVIDER": "LLM", "LLM_API_KEY": "sk-secret", "LLM_TIMEOUT_MS": "abc", "LLM_BASE_URL": "http://x/v1/"}
    )
    assert (s.provider, s.timeout_ms, s.base_url) == ("llm", 8000, "http://x/v1")
    assert "sk-secret" not in repr(s)
    assert Settings.from_env({"AI_PROVIDER": "openai"}).provider == "offline"  # unknown -> safe default
    assert Settings.from_env({"LLM_TIMEOUT_MS": "5"}).timeout_ms == 100


@pytest.mark.parametrize(
    ("token", "values", "ok"),
    [
        ("69.2", [69.23], True),
        ("69", [69.23], True),
        ("70", [69.23], False),
        ("-11.1", [-11.13], True),
        ("2,001", [2001.02], True),
        ("0.71", [0.7062], True),
        ("0.7", [0.7062], True),
        ("0.8", [0.7062], False),
    ],
)
def test_numbers_must_be_a_correct_rounding(token, values, ok):
    assert allowed(token, values) is ok


def test_the_template_passes_its_guardrails_on_v1_1_answers(answers_v11):
    facts = build_facts(answers_v11)
    text = template_text(facts)
    assert validate(text, facts, answers_v11["decision"]["recommendation"]) is None
    assert "₹14.3 lakh" in text
