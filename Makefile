PYTHON ?= python
COMPOSE ?= docker compose

.PHONY: lint test typecheck replay demo down reset logs verify scenario-checkout-failure e2e

lint:
	ruff check .

test:
	pytest

typecheck:
	mypy src apps eval

replay:
	$(PYTHON) eval/replay/replay_runner.py

demo:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v
	$(COMPOSE) up --build -d

logs:
	$(COMPOSE) logs -f --tail=200

verify:
	$(PYTHON) scripts/wait_for_stack.py

scenario-checkout-failure:
	$(COMPOSE) run --rm scenario

e2e: verify scenario-checkout-failure
