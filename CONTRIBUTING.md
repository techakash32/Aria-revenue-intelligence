# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cp .env.example .env        # fill in your own local values
```

## Running checks locally

```bash
ruff check .          # lint
pytest -v             # unit tests (no live DB required)
python data/seed_db.py  # optional: seed MySQL with sample data
```

## Guidelines

- Keep agent/tool functions pure and mockable — no hidden network calls in
  unit-tested code paths (see `tests/test_agents.py` for the pattern).
- Any new SQL path must go through `safety.validate_query`; never build
  string-interpolated SQL.
- Update `config/app_config.json` (and its schema) rather than hardcoding new
  thresholds inside agents.
- Add or update tests for any new agent, route, or pipeline step.
- Run `ruff check .` before opening a PR; CI enforces it.
