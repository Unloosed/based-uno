# Makefile for based-uno project

# Default Python interpreter
PYTHON = python3
VENV_DIR = .venv
# For cmd.exe compatibility
ACTIVATE = $(VENV_DIR)\\Scripts\\activate.bat &&

# SHELL variable for GNU Make on Windows often defaults to cmd.exe if not set
# Explicitly setting it can sometimes help if issues arise with complex commands.
# SHELL = cmd.exe

.PHONY: help setup install-dev format lint ruff-lint mypy test coverage run requirements clean

help:
	@echo "Makefile for based-uno"
	@echo ""
	@echo "Usage:"
	@echo "  make setup          - Set up the development environment (create venv, install deps)"
	@echo "  make install-dev    - Install/update development dependencies (after setup)"
	@echo "  make format         - Format code using Ruff Formatter"
	@echo "  make lint           - Lint code using Ruff and MyPy"
	@echo "  make test           - Run tests using Pytest"
	@echo "  make coverage       - Run tests and show coverage report"
	@echo "  make clean          - Remove build artifacts and __pycache__ directories"
	@echo "  make run            - Run the Uno game"
	@echo "  make requirements   - Generate requirements.txt from pyproject.toml"
	@echo ""

setup:
	@echo ">>> Checking for virtual environment in $(VENV_DIR)..."
	@if not exist "$(VENV_DIR)" ( \
		echo ">>> Creating virtual environment in $(VENV_DIR)..." && \
		$(PYTHON) -m venv $(VENV_DIR) \
	) else ( \
		echo ">>> Virtual environment $(VENV_DIR) already exists." \
	)
	@echo ">>> Upgrading pip..."
	$(ACTIVATE) pip install --upgrade pip
	@echo ">>> Installing development dependencies from pyproject.toml..."
	$(ACTIVATE) pip install -e ".[dev]"
	@echo ">>> Setup complete. Activate with: $(VENV_DIR)\\Scripts\\activate.bat (in cmd) or .\\$(VENV_DIR)\\Scripts\\Activate.ps1 (in PowerShell)"

# Other targets depend on 'setup' to ensure the venv is ready.
install-dev: setup
	@echo ">>> Installing/updating development dependencies..."
	$(ACTIVATE) pip install -e ".[dev]"

format: setup
	@echo ">>> Formatting code with Ruff Formatter..."
	$(ACTIVATE) ruff format uno_game/ .

lint: ruff-lint mypy

ruff-lint: setup
	@echo ">>> Linting with Ruff (with auto-fix)..."
	$(ACTIVATE) ruff check uno_game/ . --fix

mypy: setup
	@echo ">>> Type checking with MyPy..."
	$(ACTIVATE) mypy uno_game/ .

test: setup
	@echo ">>> Running tests with Pytest..."
	$(ACTIVATE) pytest

coverage: setup
	@echo ">>> Running tests with coverage..."
	$(ACTIVATE) pytest --cov=uno_game --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

run: setup
	@echo ">>> Running Uno game..."
	$(ACTIVATE) $(PYTHON) -m uno_game.src.game
	@echo ">>> Note: This currently runs the example simulation in game.py."

requirements: setup
	@echo ">>> Generating requirements.txt and requirements-dev.txt..."
	$(ACTIVATE) pip-compile pyproject.toml --output-file=requirements.txt --resolver=backtracking
	$(ACTIVATE) pip-compile pyproject.toml --all-extras --output-file=requirements-dev.txt --resolver=backtracking
	@echo ">>> requirements.txt and requirements-dev.txt generated."

clean:
	@echo ">>> Cleaning up..."
	@REM Use rd for directories and del for files on Windows cmd
	@if exist "$(VENV_DIR)" ( echo ">>> Removing virtual environment $(VENV_DIR)..." && rd /s /q "$(VENV_DIR)" )
	@REM The find commands are Unix-like; for cmd.exe, more complex batch is needed or manual deletion.
	@REM For simplicity, Python can be used for portable cleaning, or stick to basic cmd commands.
	@echo ">>> Removing __pycache__ directories and .pyc files..."
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
	@del /s /q *.pyc
	@if exist ".pytest_cache" ( rd /s /q ".pytest_cache" )
	@if exist "htmlcov" ( rd /s /q "htmlcov" )
	@if exist ".mypy_cache" ( rd /s /q ".mypy_cache" )
	@if exist ".coverage" ( del /f ".coverage" )
	@if exist "build" ( rd /s /q "build" )
	@if exist "dist" ( rd /s /q "dist" )
	@for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d"
	@echo ">>> Clean up process mostly complete. Some files might need manual deletion if errors occurred."
