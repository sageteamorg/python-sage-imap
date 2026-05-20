.PHONY: help install test lint format clean build publish docs

help:  ## Display this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	poetry install

test:  ## Run tests
	poetry run pytest --cov=sage_imap --cov-report=term-missing --cov-report=html

test-fast:  ## Run tests without coverage
	poetry run pytest -v -m "not integration"

integration-up:  ## Start Mailcow-compatible IMAP test stack
	docker compose -f docker/mailcow/docker-compose.yml up -d

integration-down:  ## Stop IMAP test stack
	docker compose -f docker/mailcow/docker-compose.yml down

integration-test:  ## Run integration tests against local IMAP stack
	IMAP_HOST=127.0.0.1 IMAP_PORT=993 IMAP_USER=imaptest@test.local IMAP_PASSWORD=testpassword IMAP_USE_SSL=true poetry run pytest -m integration -v

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

publish:  ## Publish to PyPI (requires PyPI token: poetry config pypi-token.pypi ...)
	poetry publish --build

publish-test:  ## Publish to TestPyPI
	poetry publish --build -r testpypi

export-requirements:  ## Export runtime requirements (empty if stdlib-only)
	poetry export -f requirements.txt --output requirements/requirements.txt --without-hashes --only main

docs:  ## Build documentation (requires: poetry install)
	$(MAKE) -C docs html

docs-serve:  ## Serve documentation locally (requires: poetry install)
	$(MAKE) -C docs livehtml

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
