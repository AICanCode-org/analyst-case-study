"""The AI insight narrator: a short executive summary of answers.json.

Safe by design:
- optional: AI_PROVIDER=offline (the default) never calls a model; the deterministic template is used;
- the model only sees the numbered facts of facts.py (aggregates), never raw data;
- OpenAI-compatible HTTP API (Ollama, LM Studio, vLLM, any hosted provider); no SDK, no paid key needed;
- every answer passes the guardrails below or is replaced by the template (fallback=true + reason).

Guardrails (validate):
  1. plain text, at most MAX_CHARS characters, at least 2 fact citations, all citations exist;
  2. every number is a correct rounding of a value in the facts (no invented numbers);
  3. no causal over-claims (observational data: "caused", "proves", "guaranteed", ...);
  4. it states the recommendation and the caveat (an experiment is needed to confirm).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field

from .facts import RECOMMENDATION_LABELS, Fact, build_facts, facts_block

MAX_CHARS = 900
BANNED = [
    "caused",
    "causes",
    "causing",
    "proves",
    "proven",
    "proof",
    "guarantee",
    "guaranteed",
    "definitely",
    "certainly",
    "will increase",
    "will grow",
    "will recover",
    "because of the device",
]
CAVEAT = re.compile(r"\b(experiment|a/b test|observational)\b", re.IGNORECASE)
CITATION = re.compile(r"\[F(\d+)\]")
DATE = re.compile(r"\b\d{4}-(?:\d{2}-\d{2}|\d{2}|W\d{2})\b")
NUMBER = re.compile(r"(?<![\w.])[-+−]?\d[\d,]*(?:\.\d+)?")
SYSTEM_PROMPT = (
    "You write a 3-5 sentence executive summary of a product analytics case study for a Head of Product. "
    "Use ONLY the numbered facts you are given; cite each fact you use as [F1], [F2]. Never introduce a number "
    "that is not in the facts. The data is observational: do not claim causes or guarantees. State the "
    "recommendation and that an experiment is needed to confirm the effect. Plain text only, no markdown, "
    f"at most {MAX_CHARS} characters."
)


@dataclass
class Narrative:
    text: str
    source: str  # "template" or "llm"
    fallback: bool
    reason: str | None
    model: str | None
    facts: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Settings:
    provider: str = "offline"
    base_url: str = "http://localhost:11434/v1"
    model: str = "llama3.2"
    api_key: str = field(default="", repr=False)  # never printed or logged
    timeout_ms: int = 8000

    @classmethod
    def from_env(cls, env: dict | None = None) -> Settings:
        env = os.environ if env is None else env
        provider = env.get("AI_PROVIDER", "offline").strip().lower() or "offline"
        if provider not in ("offline", "llm"):
            provider = "offline"
        try:
            timeout = max(100, min(60_000, int(env.get("LLM_TIMEOUT_MS", "8000"))))
        except ValueError:
            timeout = 8000
        return cls(
            provider=provider,
            base_url=env.get("LLM_BASE_URL", cls.base_url).rstrip("/"),
            model=env.get("LLM_MODEL", cls.model),
            api_key=env.get("LLM_API_KEY", ""),
            timeout_ms=timeout,
        )


def template_text(facts: list[Fact]) -> str:
    """The deterministic narrative: same answers, same text, always passes validate()."""
    by_id = {f.id: f.text for f in facts}
    return (
        f"{by_id['F2']} [F2] The gap is at the payment step: {lower_first(by_id['F3'])} [F3] "
        f"{by_id['F4']} [F4] {by_id['F6']} [F6] {by_id['F7']} [F7] {by_id['F8']} [F8] "
        f"{by_id['F9']} [F9] This is observational data, so an experiment should confirm the effect first."
    )


def lower_first(text: str) -> str:
    return text[0].lower() + text[1:]


def sanitise(text: str) -> str:
    """Plain text only: drop control characters and markup, collapse whitespace."""
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text)
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"[*_`#>|]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def allowed(token: str, values: list[float]) -> bool:
    """A number is allowed when it is a correct rounding of a fact value (sign ignored)."""
    clean = token.replace(",", "").replace("−", "-").lstrip("+-")
    try:
        number = float(clean)
    except ValueError:
        return False
    decimals = len(clean.split(".")[1]) if "." in clean else 0
    tolerance = 0.5 * 10 ** (-decimals) + 1e-9
    return any(abs(number - abs(v)) <= tolerance for v in values)


def validate(text: str, facts: list[Fact], recommendation: str) -> str | None:
    """None when the text passes every guardrail, else the reason it fails."""
    if not text:
        return "empty answer"
    if len(text) > MAX_CHARS:
        return f"too long ({len(text)} > {MAX_CHARS} characters)"
    cited = [int(n) for n in CITATION.findall(text)]
    if len(set(cited)) < 2:
        return "fewer than 2 fact citations"
    if any(n < 1 or n > len(facts) for n in cited):
        return "cites a fact that does not exist"
    lower = text.lower()
    for word in BANNED:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            return f"causal over-claim: {word!r}"
    fact_text = " ".join(f.text for f in facts)
    body = CITATION.sub(" ", text)
    for date in DATE.findall(body):
        if date not in fact_text:
            return f"date not in the facts: {date}"
    body = DATE.sub(" ", body)
    values = [v for f in facts for v in f.values]
    for token in NUMBER.findall(body):
        if not allowed(token, values):
            return f"number not in the facts: {token}"
    label = RECOMMENDATION_LABELS[recommendation]
    key = {
        "run_targeted_experiment": "experiment",
        "rebuild_checkout": "rebuild",
        "no_checkout_gap_found": "not rebuild",
    }[recommendation]
    if key not in lower and label.lower() not in lower:
        return "does not state the recommendation"
    if not CAVEAT.search(text):
        return "missing the caveat (observational data / experiment)"
    return None


def call_llm(settings: Settings, facts: list[Fact]) -> str:
    body = json.dumps(
        {
            "model": settings.model,
            "temperature": 0,
            "max_tokens": 400,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Facts:\n" + facts_block(facts)},
            ],
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    req = urllib.request.Request(f"{settings.base_url}/chat/completions", data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=settings.timeout_ms / 1000) as resp:
        data = json.loads(resp.read(200_000).decode("utf-8"))
    return str(data["choices"][0]["message"]["content"])


def narrate(answers: dict, settings: Settings | None = None) -> Narrative:
    settings = settings or Settings.from_env()
    facts = build_facts(answers)
    recommendation = answers["decision"]["recommendation"]
    fact_dicts = [{"id": f.id, "text": f.text} for f in facts]

    def template(reason: str | None) -> Narrative:
        return Narrative(template_text(facts), "template", reason is not None, reason, None, fact_dicts)

    if settings.provider != "llm":
        return template(None)
    try:
        text = sanitise(call_llm(settings, facts))
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        return template(f"provider unreachable: {type(exc).__name__}")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        return template(f"unexpected provider response: {type(exc).__name__}")
    problem = validate(text, facts, recommendation)
    if problem:
        return template(f"guardrail: {problem}")
    return Narrative(text, "llm", False, None, settings.model, fact_dicts)
