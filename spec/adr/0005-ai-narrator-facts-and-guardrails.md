# ADR-0005: The AI narrator sees numbered facts, is checked by guardrails and falls back to a template

* **Status:** accepted
* **Date:** 2026-07-05
* **Deciders:** analytics team

## Context
The Head of Product wants a plain-language summary on the dashboard. A language model writes fluent
summaries and also invents numbers, rounds wrongly, claims causation and leaks what it is given.

## Options considered
1. **No AI** — safe; misses a useful, common product feature that learners should learn to build safely.
2. **Give the model answers.json (or the data) and display what it writes** — easy; unverifiable,
   and row-level data would leave the system.
3. **Numbered aggregate facts in, guardrails out, deterministic template as fallback.**

## Decision
Option 3. `facts.py` turns answers.json into facts `[F1]..[Fn]` (aggregates only). The model must cite
facts; guardrails reject the text if it is too long, cites an unknown fact, contains a number that is
not a correct rounding of a fact value, mentions a date not in the facts, uses causal words, or omits
the recommendation or the caveat. On any rejection, timeout or error, the template is shown, with the reason.
Offline (`AI_PROVIDER=offline`) is the default; any OpenAI-compatible endpoint can be configured.

## Consequences
The summary can be wrong only in ways a human reviewer can still catch (emphasis, tone); it cannot
introduce a number the analysis did not produce. The template guarantees the dashboard works with no
key. Guardrails are code and are unit-tested against a fake LLM server.

## AI assistance
Guardrail cases were brainstormed with an assistant ("ways a summary can mislead"); each kept case
became a test.
