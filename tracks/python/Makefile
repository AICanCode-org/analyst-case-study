# Python track. Same targets in every track: install, lint, test, coverage, run (+ report).
PY ?= .venv/bin/python
DATA ?= ../../data/raw/2026-08
OUT ?= out

.PHONY: install lint test coverage run report clean
install:
	python3 -m venv .venv
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r requirements-dev.txt

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

test:            ## unit tests (fast, tiny fixtures)
	$(PY) -m pytest tests/unit

coverage:        ## unit + data tests on the real export, 85 % line coverage gate
	$(PY) -m pytest tests --cov --cov-report=term --cov-report=xml --cov-fail-under=85

run:             ## answers.json for one export
	$(PY) -m funnellens run --data $(DATA) --out $(OUT)

report:          ## execute the notebook top to bottom (fails on any error)
	PYTHONPATH=$(CURDIR) $(PY) -m jupyter nbconvert --to notebook --execute notebooks/analysis.ipynb \
	  --output-dir $(OUT) --ExecutePreprocessor.timeout=300

clean:
	rm -rf $(OUT) .pytest_cache .ruff_cache .coverage coverage.xml htmlcov
