# Dashboard (v1.0 release app) + AI insight narrator. Shared by every track: it reads answers.json.
PY ?= .venv/bin/python
ANSWERS ?= ../tracks/python/out/answers.json
PORT ?= 18120

.PHONY: install lint test coverage prepare run clean
install:
	python3 -m venv .venv
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r requirements-dev.txt

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

test:
	$(PY) -m pytest tests

coverage:
	$(PY) -m pytest tests --cov --cov-report=term --cov-report=xml --cov-fail-under=85

prepare:         ## validate ANSWERS and write static/ (AI_PROVIDER=offline unless you set it)
	$(PY) -m funnellens_dashboard prepare --answers $(ANSWERS) --out static

run: prepare     ## http://localhost:$(PORT)
	$(PY) -m streamlit run app.py --server.port $(PORT) --server.address 127.0.0.1

clean:
	rm -rf static/*.json static/*.md .pytest_cache .ruff_cache .coverage coverage.xml
