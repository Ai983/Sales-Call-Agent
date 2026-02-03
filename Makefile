VENV := .venv
PY := $(VENV)/bin/python

.PHONY: venv install-api run-api verify-openai verify-faster

venv:
	python -m venv $(VENV)

install-api:
	$(PY) -m pip install -r requirements-api.txt

run-api:
	$(PY) -m uvicorn web_api.main:app --reload --port 8000

verify-openai:
	$(PY) scripts/verify_api.py --backend openai

verify-faster:
	$(PY) scripts/verify_api.py --backend faster
