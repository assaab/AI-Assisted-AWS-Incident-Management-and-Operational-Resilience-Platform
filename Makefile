PYTHON ?= python

.PHONY: lint test typecheck replay

lint:
	ruff check .

test:
	pytest

typecheck:
	mypy src apps eval

replay:
	$(PYTHON) eval/replay/replay_runner.py
