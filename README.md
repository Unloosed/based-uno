# Based-Uno

Based-Uno is a Python implementation of the classic card game Uno, with a focus on modern software development practices, extensibility, and clean code. This project aims to provide a solid foundation for a playable Uno game, potentially with AI players and network capabilities in the future.

## Features

*   Standard Uno gameplay (play cards by color or number, action cards like Skip, Reverse, Draw Two).
*   Wild and Wild Draw Four cards.
*   (Planned) Special house rules or "based" cards.
*   (Planned) CLI for playing the game.
*   (Planned) AI opponents.
*   (Planned) GUI or web interface.

## Project Goals

*   **Modern Python Development**: Utilize current best practices for Python development, including type hinting, linting, formatting, and comprehensive testing.
*   **Modularity and Extensibility**: Design the game logic in a way that is easy to understand, maintain, and extend with new features or card types.
*   **Educational**: Serve as an example of a well-structured Python project.

## Installation

This project uses Python 3.8+ and `make` for managing common development tasks.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/based-uno.git
    cd based-uno
    ```

2.  **Set up the development environment:**
    This command will create a Python virtual environment in `.venv/`, activate it, and install all necessary dependencies (including development tools).
    ```bash
    make setup
    ```

3.  **Activate the virtual environment (if not already active for your current session):**
    ```bash
    source .venv/bin/activate
    ```
    You should do this every time you start a new terminal session to work on the project.

## How to Run the Game

Currently, the game can be run via a simulation script:

```bash
make run
```
This will execute `uno_game/src/game.py`, which might contain a basic game simulation loop.

### Running the Web Server (for API access)

A simple Flask web server is available to expose game logic via an API. This is intended for development and integration with a potential frontend.

1.  **Ensure dependencies are installed:**
    If you haven't already, set up the project and install dependencies:
    ```bash
    make setup
    ```

2.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

3.  **Run the server:**
    ```bash
    ./run.sh
    ```
    This will start the Flask development server, typically on `http://0.0.0.0:5000/`.

    The main API endpoint available is:
    *   `GET /api/game_state`: Returns the current state of the Uno game. You can access this in your browser or with a tool like `curl`:
        ```bash
        curl http://localhost:5000/api/game_state
        ```

(A proper CLI entry point for the game itself is planned for the future).

## Development

This project uses a suite of tools to ensure code quality and consistency.

### Code Quality: Formatting, Linting, and Type Checking

This project uses a suite of tools to ensure code quality and consistency:
*   **Ruff**: For extremely fast Python linting and formatting (Black-compatible).
*   **MyPy**: For static type checking.
*   **Pre-commit Hooks**: To automatically run checks before each commit.

**Setup Pre-commit Hooks (Recommended):**
After setting up the environment with `make setup`, install the pre-commit hooks:
```bash
pre-commit install
```
This will ensure that linters and formatters run on changed files before you commit, helping to maintain code style and catch issues early.

**Manual Checks:**

*   **Format code:**
    ```bash
    make format
    ```
    (This uses `ruff format`)

*   **Lint code and check for type errors:**
    ```bash
    make lint
    ```
    (This runs `ruff check --fix` and `mypy`)

    You can also run Ruff's linter or MyPy individually:
    ```bash
    make ruff-lint
    make mypy
    ```

### Testing

We use Pytest for running tests.

*   **Run all tests:**
    ```bash
    make test
    ```

*   **Run tests with coverage report:**
    ```bash
    make coverage
    ```
    This will generate an HTML coverage report in the `htmlcov/` directory. Open `htmlcov/index.html` in your browser to view it. The project aims for a minimum test coverage (e.g., 80%, as configured in `pyproject.toml`).

### Generating Requirements Files

To update `requirements.txt` and `requirements-dev.txt` from `pyproject.toml`:
```bash
make requirements
```
Commit these files after generating them.

## Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` for more detailed information on how to contribute, report bugs, and suggest features.

A `CODE_OF_CONDUCT.md` is also in place to ensure a welcoming and inclusive environment.

## License

This project is licensed under the terms of the MIT License. See `LICENSE` file for details.
