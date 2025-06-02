.PHONY: install install-dev test lint type-check check clean build dist help

# Python interpreter to use
PYTHON := python
# Test command
PYTEST := pytest
# Detect OS for platform-specific commands
ifeq ($(OS),Windows_NT)
	CLEAN_CMD = if exist "$(1)" rmdir /s /q "$(1)"
	CLEAN_FILE_CMD = if exist "$(1)" del /q "$(1)"
	RM = del /q
	RM_RF = rmdir /s /q
	SEP = \\
else
	CLEAN_CMD = rm -rf $(1)
	CLEAN_FILE_CMD = rm -f $(1)
	RM = rm -f
	RM_RF = rm -rf
	SEP = /
endif

# Default target
.DEFAULT_GOAL := help

help:  ## Show this help
	@echo Datash development commands:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	$(PYTHON) -m pip install -r requirements.txt

install-dev:  ## Install development dependencies
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install black mypy pytest pytest-cov responses

test:  ## Run tests
	$(PYTEST) -v

test-cov:  ## Run tests with coverage report
	$(PYTEST) --cov=. --cov-report=term --cov-report=html

lint:  ## Check code style with black
	$(PYTHON) -m black --check .

lint-fix:  ## Fix code style issues with black
	$(PYTHON) -m black .

type-check:  ## Check types with mypy
	$(PYTHON) -m mypy --ignore-missing-imports main.py tests/

check:  ## Run all checks (tests, lint, type-check)
	$(MAKE) test
	$(MAKE) lint
	$(MAKE) type-check

clean:  ## Remove build artifacts and temporary files
	$(call CLEAN_CMD,build)
	$(call CLEAN_CMD,dist)
	$(call CLEAN_CMD,htmlcov)
	$(call CLEAN_CMD,__pycache__)
	$(call CLEAN_CMD,.pytest_cache)
	$(call CLEAN_CMD,.mypy_cache)
	$(call CLEAN_CMD,*.egg-info)
	$(call CLEAN_FILE_CMD,.coverage)
	$(call CLEAN_FILE_CMD,coverage.xml)
	$(call CLEAN_FILE_CMD,datash.log)
	find . -type d -name "__pycache__" -exec $(RM_RF) {} +
	find . -type d -name "*.egg-info" -exec $(RM_RF) {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

build:  ## Build package
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) setup.py build

dist:  ## Create distribution packages
	$(PYTHON) -m pip install --upgrade pip setuptools wheel twine
	$(PYTHON) setup.py sdist bdist_wheel

run:  ## Run Datash
	$(PYTHON) main.py

setup-dev:  ## Set up development environment
	$(MAKE) install-dev
	@echo "\nDevelopment environment setup complete."
	@echo "Don't forget to set up your DATASH_API_KEY environment variable."
	@echo "You can copy .env.example to .env and add your API key there."

# Additional targets for Windows users
windows-setup:  ## Set up development environment on Windows (alternative to make setup-dev)
	@echo Setting up development environment on Windows...
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install black mypy pytest pytest-cov responses
	@echo.
	@echo Development environment setup complete.
	@echo Don't forget to set up your DATASH_API_KEY environment variable:
	@echo $$ set DATASH_API_KEY=your_api_key
	@echo or
	@echo $$ $env:DATASH_API_KEY="your_api_key"

