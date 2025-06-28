# Makefile for based-uno project

# Default Python interpreter
PYTHON = python3
VENV_DIR = .venv
ACTIVATE = . $(VENV_DIR)/bin/activate;
DEACTIVATE = deactivate;

# Check if virtual environment exists
VENV_EXISTS = test -d $(VENV_DIR)

.PHONY: help
help:
	@echo "Makefile for based-uno"
	@echo ""
	@echo "Usage:"
	@echo "  make setup          - Set up the development environment (create venv, install deps)"
	@echo "  make install-dev    - Install/update development dependencies"
	@echo "  make format         - Format code using Black"
	@echo "  make lint           - Lint code using Flake8 and MyPy"
	@echo "  make test           - Run tests using Pytest"
	@echo "  make coverage       - Run tests and show coverage report"
	@echo "  make clean          - Remove build artifacts and __pycache__ directories"
	@echo "  make run            - Run the Uno game (placeholder)"
	@echo "  make requirements   - Generate requirements.txt from pyproject.toml"
	@echo ""

.PHONY: setup
setup: $(VENV_DIR)/bin/activate
$(VENV_DIR)/bin/activate: pyproject.toml
	@if ! $(VENV_EXISTS); then \
		echo ">>> Creating virtual environment in $(VENV_DIR)..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
	else \
		echo ">>> Virtual environment $(VENV_DIR) already exists."; \
	fi
	$(ACTIVATE) \
	echo ">>> Upgrading pip..."; \
	pip install --upgrade pip; \
	echo ">>> Installing development dependencies from pyproject.toml..."; \
	pip install -e ".[dev]"; \
	echo ">>> Setup complete. Activate with: source $(VENV_DIR)/bin/activate"; \
	$(DEACTIVATE)

.PHONY: install-dev
install-dev: $(VENV_DIR)/bin/activate
	@echo ">>> Installing/updating development dependencies..."
	$(ACTIVATE) pip install -e ".[dev]"; $(DEACTIVATE)

.PHONY: format
format: $(VENV_DIR)/bin/activate
	@echo ">>> Formatting code with Ruff Formatter..."
	$(ACTIVATE) ruff format uno_game/ .; $(DEACTIVATE)
	# @echo ">>> Formatting code with Black (if Ruff doesn't cover all)..." # Optional: Black can be run if specific Black-only formatting is desired.
	# $(ACTIVATE) black uno_game/ .; $(DEACTIVATE)

.PHONY: lint
lint: ruff-lint mypy

.PHONY: ruff-lint
ruff-lint: $(VENV_DIR)/bin/activate
	@echo ">>> Linting with Ruff (with auto-fix)..."
	$(ACTIVATE) ruff check uno_game/ . --fix; $(DEACTIVATE)

.PHONY: mypy
mypy: $(VENV_DIR)/bin/activate
	@echo ">>> Type checking with MyPy..."
	$(ACTIVATE) mypy uno_game/ .; $(DEACTIVATE)

.PHONY: test
test: $(VENV_DIR)/bin/activate
	@echo ">>> Running tests with Pytest..."
	$(ACTIVATE) pytest; $(DEACTIVATE)

.PHONY: coverage
coverage: $(VENV_DIR)/bin/activate
	@echo ">>> Running tests with coverage..."
	$(ACTIVATE) pytest --cov=uno_game --cov-report=html; $(DEACTIVATE)
	@echo "Coverage report generated in htmlcov/index.html"

.PHONY: run
run: $(VENV_DIR)/bin/activate
	@echo ">>> Running Uno game..."
	$(ACTIVATE) $(PYTHON) uno_game/src/game.py; $(DEACTIVATE)
	@echo ">>> Note: This currently runs the example simulation in game.py."

.PHONY: requirements
requirements: $(VENV_DIR)/bin/activate
	@echo ">>> Generating requirements.txt and requirements-dev.txt..."
	$(ACTIVATE) \
	pip-compile pyproject.toml --output-file=requirements.txt --resolver=backtracking; \
	pip-compile pyproject.toml --all-extras --output-file=requirements-dev.txt --resolver=backtracking; \
	$(DEACTIVATE)
	@echo ">>> requirements.txt and requirements-dev.txt generated."

.PHONY: clean
clean:
	@echo ">>> Cleaning up..."
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -f .coverage
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

# Setup virtual environment and install dependencies
# This is a common pattern to ensure commands run in the venv
# However, for simplicity, individual targets will activate.
# VENV_CMD = . $(VENV_DIR)/bin/activate &&

# Example of how to ensure venv is active for a command:
# my_command: $(VENV_DIR)/bin/activate
#	$(ACTIVATE) echo "Running in venv"; $(DEACTIVATE)

# Note: The use of $(ACTIVATE) ...; $(DEACTIVATE) in each command ensures that
# if the Makefile is run in a shell that doesn't persist the source command,
# each command execution still operates within the context of the virtual environment.
# This is more robust for different shell environments.
# If you are always running make from a shell where the venv is already activated,
# you might simplify this, but this approach is safer.
