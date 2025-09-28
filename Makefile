# Makefile for wxmeow weather application
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev test test-unit test-integration test-functional
.PHONY: lint format coverage clean docker-build docker-run docker-compose-up
.PHONY: docker-compose-down deploy-local serve dev
.DEFAULT_GOAL := help

# Python and virtual environment settings
PYTHON := python3
VENV_DIR := venv
PIP := $(VENV_DIR)/bin/pip
PYTEST := $(VENV_DIR)/bin/pytest
FLASK := $(VENV_DIR)/bin/flask
PYTHON_VENV := $(VENV_DIR)/bin/python

# Docker settings
DOCKER_IMAGE := wxmeow
DOCKER_TAG := latest
COMPOSE_FILE := docker-compose.yml

# Test settings
TEST_DIR := tests
COVERAGE_DIR := htmlcov
TEST_REPORT := test-report.html

help: ## Show this help message
	@echo "wxmeow - Weather Application"
	@echo "============================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation and setup
install: ## Install production dependencies
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

install-dev: ## Install development and testing dependencies
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev,security]"

venv: ## Create virtual environment
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip
	$(PIP) install -e .

venv-dev: venv ## Create virtual environment with dev dependencies
	$(PIP) install -e ".[dev,security]"

# Testing
test: ## Run all tests
	$(PYTHON) run_tests.py --all

test-unit: ## Run unit tests only
	$(PYTHON) run_tests.py --unit

test-integration: ## Run integration tests only
	$(PYTHON) run_tests.py --integration

test-functional: ## Run functional tests only
	$(PYTHON) run_tests.py --functional

test-fast: ## Run tests excluding slow ones
	$(PYTHON) run_tests.py --all --fast

test-verbose: ## Run tests with verbose output
	$(PYTHON) run_tests.py --all --verbose

coverage: ## Run tests with coverage report
	$(PYTHON) run_tests.py --all --coverage
	@echo "Coverage report generated in $(COVERAGE_DIR)/index.html"

test-report: ## Generate comprehensive test report
	$(PYTHON) run_tests.py --report
	@echo "Test report generated: $(TEST_REPORT)"

# Code quality
lint: ## Run linting checks
	$(PYTHON) run_tests.py --lint

format: ## Format code with black and isort
	black wxmeow/
	isort wxmeow/

format-check: ## Check code formatting without making changes
	black --check --diff wxmeow/
	isort --check-only --diff wxmeow/

type-check: ## Run type checking with mypy
	mypy wxmeow/ --ignore-missing-imports

security-scan: ## Run security scans
	safety check
	bandit -r wxmeow/ -f json -o bandit-report.json || true
	@echo "Security scan complete. Check bandit-report.json for details."

# Development server
serve: ## Run Flask development server
	export FLASK_APP=wxmeow && export FLASK_ENV=development && flask run

dev: ## Run development server with auto-reload
	export FLASK_APP=wxmeow && export FLASK_ENV=development && flask run --reload

deploy-local: ## Deploy locally using deploy.py script
	$(PYTHON) deploy.py

# Docker commands
docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run: ## Run Docker container
	docker run --name wxmeow-container -d -p 8000:5000 --rm $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-logs: ## Show Docker container logs
	docker logs wxmeow-container -f

docker-stop: ## Stop Docker container
	docker stop wxmeow-container

docker-compose-up: ## Start services with docker-compose
	docker-compose -f $(COMPOSE_FILE) up -d

docker-compose-down: ## Stop services with docker-compose
	docker-compose -f $(COMPOSE_FILE) down

docker-compose-logs: ## Show docker-compose logs
	docker-compose -f $(COMPOSE_FILE) logs -f

docker-compose-rebuild: ## Rebuild and restart with docker-compose
	docker-compose -f $(COMPOSE_FILE) up -d --build

docker-clean: ## Clean up Docker images and containers
	docker system prune -f
	docker image prune -f

# Cleanup
clean: ## Clean up temporary files and caches
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.orig" -delete
	find . -type f -name "*~" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf $(COVERAGE_DIR)/
	rm -f .coverage
	rm -f coverage.xml
	rm -f $(TEST_REPORT)
	rm -f test-results.xml
	rm -f bandit-report.json
	rm -f flask.log

clean-all: clean ## Clean everything including virtual environment
	rm -rf $(VENV_DIR)/

# Database and data management
clean-data: ## Remove cached weather data files
	rm -f *.pkl

backup-data: ## Backup weather data files
	mkdir -p backups
	cp *.pkl backups/ 2>/dev/null || true
	@echo "Weather data backed up to backups/ directory"

# CI/CD helpers
ci-install: ## Install dependencies for CI environment
	pip install --upgrade pip
	pip install -e ".[dev,security]"

ci-test: ## Run tests in CI environment
	pytest $(TEST_DIR)/ -v --cov=wxmeow --cov-report=xml --junitxml=test-results.xml

ci-build: ## Build for CI/CD pipeline
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Utility commands
deps-upgrade: ## Upgrade all dependencies
	pip install --upgrade pip
	pip install --upgrade -e ".[dev,security]"

deps-tree: ## Show dependency tree
	pip install pipdeptree
	pipdeptree

check-health: ## Check application health
	curl -f http://localhost:8000/health || curl -f http://localhost:5000/

logs: ## Show application logs
	tail -f log_wxmeow.log

# Documentation
docs: ## Generate documentation (if sphinx is set up)
	@echo "Documentation generation not implemented yet"

# Quick development workflow
quick-test: install-dev lint test-unit ## Quick development test (install, lint, unit tests)

full-test: install-dev lint test coverage ## Full test suite with coverage

deploy-check: lint test docker-build ## Pre-deployment check

# Database operations (if needed in future)
db-init: ## Initialize database
	@echo "Database initialization not implemented yet"

db-migrate: ## Run database migrations
	@echo "Database migrations not implemented yet"

# Performance testing
perf-test: ## Run performance tests
	@echo "Performance testing not implemented yet"

# Release management
version: ## Show current version
	$(PYTHON) -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || \
	$(PYTHON) -c "import toml; print(toml.load('pyproject.toml')['project']['version'])" 2>/dev/null || \
	echo "0.3.0"

tag-release: ## Tag a new release (requires VERSION variable)
ifndef VERSION
	@echo "Please specify VERSION: make tag-release VERSION=v1.0.0"
else
	git tag -a $(VERSION) -m "Release $(VERSION)"
	git push origin $(VERSION)
endif
