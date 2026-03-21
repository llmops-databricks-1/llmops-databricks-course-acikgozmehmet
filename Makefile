# Mehmet Acikgoz <acikgozmehmet@users.noreply.github.com>
# Final streamlined Makefile integrating with pre-commit configuration.
# Provides commands for environment setup, dependency syncing, testing, coverage, building, and cleanup.

################################################################################
## Environment Setup
################################################################################

# Check if .env exists
# ifeq (,$(wildcard .env))
# $(error .env file is missing at .env. Please create one based on .env.example)
# endif

# Load environment variables from .env
# include .env

# Default variables
PACKAGE_IMPORT_NAME ?= "arxiv_curator"
PYTHON_VERSION ?= "3.12.10"
VENV_DIR ?= .venv
TEST_REPORTS_DIR ?= test-reports

.DEFAULT_GOAL := help


################################################################################
## Virtual Environment and Dependencies
################################################################################

.PHONY: create-venv sync-dev
create-venv: ## Create virtual environment
	@echo "Creating virtual environment with Python $(PYTHON_VERSION)..."
	uv venv -p $(PYTHON_VERSION) $(VENV_DIR)
	@echo "Virtual environment created at $(VENV_DIR)."

sync-dev: ## Sync and install development dependencies
	@echo "Syncing development dependencies..."
	rm -rf $(VENV_DIR)
	$(MAKE) create-venv
	uv sync --extra dev
	@echo "Development environment ready."


################################################################################
## Linting & Pre-commit Hooks
################################################################################

.PHONY: lint

lint: ## Run all pre-commit checks (auto-fixes included)
	@echo "Running all pre-commit hooks..."
	uv run pre-commit run --all-files
	@echo "Pre-commit checks complete."


################################################################################
## Testing and Coverage
################################################################################

.PHONY: run-unit-tests tests serve-coverage-report

run-unit-tests: ## Run unit tests with coverage reports
	rm -rf $(TEST_REPORTS_DIR) || true
	uv run pytest -m "not ci_exclude" ./tests --cov "src/$(PACKAGE_IMPORT_NAME)" \
		--cov-report html --cov-report term --cov-report xml \
		--junit-xml "$(TEST_REPORTS_DIR)/report.xml" --cov-fail-under=60 \
		--cov-report=xml:"$(TEST_REPORTS_DIR)/coverage.xml"
	mv htmlcov "$(TEST_REPORTS_DIR)/" || true
	rm -rf htmlcov || true
	@echo "Unit test reports generated in $(TEST_REPORTS_DIR)."

tests: ## Run all tests
	@echo "Running all tests..."
	uv run pytest
	@echo "All tests completed."

serve-coverage-report: ## Serve coverage report at http://localhost:8000
	@echo "Serving coverage report at http://localhost:8000/"
	@python -m http.server --directory "$(TEST_REPORTS_DIR)/htmlcov/" 8000



################################################################################
## Build & Cleanup
################################################################################

.PHONY: build clean

build: ## Build the Python package
	@echo "Building package..."
	uv build
	@echo "Build complete."

clean: ## Clean build artifacts and cache files
	@echo "Cleaning up environment..."
	rm -rf .coverage dist build coverage.xml $(TEST_REPORTS_DIR)
	find . -type d \( -name "*cache*" -o -name "*.dist-info" -o -name "*.egg-info" -o -name "*htmlcov" \) \
		-not -path "*$(VENV_DIR)/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -not -path "*$(VENV_DIR)/*" -delete
	@echo "Cleanup complete."


################################################################################
## Help
################################################################################

help: ## Display this help message
	@echo "-----------------------------------------------------------------"
	@echo " Python Project Makefile — Unified Management for Dev & CI"
	@echo "-----------------------------------------------------------------"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / \
	{printf "\033[36m%-35s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
