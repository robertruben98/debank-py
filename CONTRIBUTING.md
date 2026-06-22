# Contributing to debank-py

Thanks for your interest in improving `debank-py`!

## Development setup

This project targets **Python 3.9+**. The client must run on 3.9 at runtime, so
avoid PEP 604 unions (`X | None`) in runtime annotations — use
`typing.Optional` / `typing.Union` instead.

```bash
git clone https://github.com/robertruben98/debank-py
cd debank-py
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quality gates

All of the following must pass before a change is merged. CI runs them on
Python 3.9–3.13.

```bash
ruff check .          # lint + import order
mypy                  # strict type-checking (targets 3.10)
pytest -q             # unit tests (respx mocks, no network)
```

## Testing

We follow test-driven development: write a failing test first, then the minimal
code to make it pass. Unit tests use [`respx`](https://lundberg.github.io/respx/)
to mock HTTP and never hit the network.

Live integration tests are marked `integration` and are **deselected by
default**. They run only when a real key is present:

```bash
export DEBANK_ACCESS_KEY="your-paid-access-key"
pytest -m integration
```

A DeBank Cloud AccessKey is a paid credential; see the
[DeBank Cloud docs](https://docs.cloud.debank.com).

## Pull requests

- Keep changes focused and covered by tests.
- Update `CHANGELOG.md` under `[Unreleased]`.
- Make sure `ruff`, `mypy` and `pytest` are green.
