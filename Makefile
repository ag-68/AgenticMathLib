.PHONY: test lint dryrun docs

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

dryrun:
	@echo not run

docs:
	@echo not run
