# SQL track (DuckDB). Same targets in every track: install, lint, test, coverage, run (+ report).
# The analysis lives in sql/*.sql; funnellens_sql/ is only a thin runner (variables, checks, JSON).
PY ?= .venv/bin/python
DATA ?= ../../data/raw/2026-06
OUT ?= out

.PHONY: install lint test coverage run report clean
install:
	python3 -m venv .venv
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r requirements-dev.txt

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .
	$(PY) -m sqlfluff lint sql/*.sql
	$(PY) -m sqlfluff lint --config .sqlfluff-checks sql/checks

test:            ## unit tests (fast, tiny fixtures)
	$(PY) -m pytest tests/unit

coverage:        ## unit + data tests on the real export, 85 % line coverage gate
	$(PY) -m pytest tests --cov --cov-report=term --cov-report=xml --cov-fail-under=85

run:             ## answers.json for one export
	$(PY) -m funnellens_sql run --data $(DATA) --out $(OUT)

report:          ## the SQL report: every view of the run as a Markdown table (out/report.md)
	$(PY) -m funnellens_sql report --data $(DATA) --out $(OUT)

clean:
	rm -rf $(OUT) .pytest_cache .ruff_cache .coverage coverage.xml htmlcov
