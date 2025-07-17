.PHONY: help install test lint format clean build publish docs

help:  ## Display this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	poetry install

test:  ## Run tests
	poetry run pytest --cov=sage_imap --cov-report=term-missing --cov-report=html

test-fast:  ## Run tests without coverage
	poetry run pytest -v

lint:  ## Run linting
	poetry run black --check .
	poetry run isort --check-only .
	poetry run mypy .
	poetry run ruff check .
	poetry run bandit -r sage_imap/

format:  ## Format code
	poetry run black .
	poetry run isort .
	poetry run ruff check --fix .

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

build:  ## Build package
	poetry build

publish:  ## Publish to PyPI
	poetry publish

docs:  ## Build documentation
	cd docs && make html

docs-serve:  ## Serve documentation locally
	cd docs && make livehtml

pre-commit:  ## Run pre-commit hooks
	poetry run pre-commit run --all-files

setup-dev:  ## Setup development environment
	poetry install
	poetry run pre-commit install

bump-patch:  ## Bump patch version
	poetry run cz bump --increment PATCH

bump-minor:  ## Bump minor version
	poetry run cz bump --increment MINOR

bump-major:  ## Bump major version
	poetry run cz bump --increment MAJOR
