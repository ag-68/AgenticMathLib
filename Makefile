.PHONY: test lint dryrun

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

dryrun:
	uv run eval run --project toy --conditions A,B --dry-run
	uv run eval analyze --project toy
