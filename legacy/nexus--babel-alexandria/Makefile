# Development task runner for the nexus-babel-alexandria snapshot.
# Targets mirror docs/OPERATOR_RUNBOOK.md. Run from this directory.

.PHONY: db-upgrade test lint openapi-snapshot certainty certainty-check evolution-contract-test verify run-api run-worker

db-upgrade:
	alembic upgrade head

test:
	pytest -q

lint:
	ruff check .

openapi-snapshot:
	python scripts/generate_openapi_contract_snapshot.py

certainty:
	python scripts/repo_certainty_audit.py

certainty-check:
	python scripts/repo_certainty_audit.py --check

evolution-contract-test:
	pytest -q -k evolution

verify:
	$(MAKE) lint
	$(MAKE) certainty-check
	$(MAKE) test

run-api:
	uvicorn nexus_babel.main:app --host 0.0.0.0 --port 8000 --reload

run-worker:
	python -m nexus_babel.worker
