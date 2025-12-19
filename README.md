# Rationem Opum – Ledger Service

Ledger Service is the REST API service that organizes the ledger with double-entry accounting.

## Terms of usage

By using this project or its source code, for any purpose and in any shape or form, you grant your implicit agreement to all the following statements:

    You condemn Russia and its military aggression against Ukraine
    You recognize that Russia is an occupant that unlawfully invaded a sovereign state
    You support Ukraine's territorial integrity, including its claims over temporarily occupied territories of Crimea and Donbas
    You reject false narratives perpetuated by Russian state propaganda

## Features

- [x] Ledgers
- [x] Commodities (Currencies)
- [x] Accounts (Categories)
- [x] Transactions
- [ ] Tags
- [ ] Balance reports
- [ ] Balance sheet
- [ ] Cash flow statement
- [ ] Net worth statement
- [ ] Import from different/custom formats
- [ ] Export to csv

## License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file for details.

## Contributing

Contributions are welcome! Here's how to get started quickly and efficiently.

### Setup
- Use Python 3.14+.
- Create a virtual environment and install runtime deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Running the server

```bash
source .venv/bin/activate
python run_server.py
```

Configuration is read from `settings.yaml` (see `settings.example.yaml`).

### Testing
- Unit/integration tests:

```bash
pytest -q
```

- With coverage:

```bash
pytest --cov=tmw_ledger --cov-report=term-missing
```

### Linting & Formatting

This project uses `ruff` for both linting and formatting (configured in `pyproject.toml`).

```bash
ruff check tmw_ledger tests
ruff format tmw_ledger tests
```

### Type Checking

```bash
mypy tmw_ledger
```

### Development Workflow
- Create a feature branch from `main`.
- Follow Conventional Commits for messages (e.g., `feat: add ledger summary endpoint`).
- Keep PRs focused and small; include tests for new behavior.
- Ensure CI basics pass locally: lint, format, type-check, and tests.

### Pull Request Checklist
- [ ] Tests added/updated for changes
- [ ] `ruff check` and `ruff format` pass
- [ ] `mypy` passes
- [ ] Brief description of changes and rationale

### Reporting Issues
- Include steps to reproduce, expected vs actual behavior, and environment details.
- Propose a minimal fix or a direction when possible.

Thank you for helping improve Track My Wealth Ledger!
