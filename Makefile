PYTHON=python

dev:
	$(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

lint:
	ruff check app tests
	cd frontend && npm run lint

format:
	black app tests

test:
	pytest

.PHONY: dev lint format test
