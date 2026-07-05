# Changelog

## 0.2.0 — Hardening pass

### Security
- Fixed `safety.sql_validator.validate_query` only checking the *first*
  statement of a `sqlparse.parse()` result — a stacked query like
  `SELECT 1; DROP TABLE daily_sales;` previously validated as safe. Now
  rejects any multi-statement input outright. Regression test added.
- Removed real API keys/tokens (Groq, LangSmith, Telegram, WhatsApp) from
  the committed `.env`; added `.env.example` as the template going forward.
  **If you're the project owner: rotate every key that was in the old
  `.env` — they should be treated as compromised.**

### Fixed
- `memory/semantic_store.py`: `NameError` on `datetime` (missing import) in
  `store_decision`.
- `observability/langsmith_setup.py`: read `LANGSMITH_API_KEY`, an env var
  that didn't exist anywhere else in the project (`.env` uses
  `LANGCHAIN_API_KEY`); also crashed on import when unset. Now reads the
  correct variable and degrades gracefully with tracing disabled.

### Added
- Implementations for previously-empty modules: `tools/chart_tool.py`
  (matplotlib revenue-trend/category charts as base64 PNG),
  `pipelines/run_pipeline.py` (unified CLI), `memory/short_term.py`
  (rolling chat buffer), `observability/tracer.py` (lightweight step
  tracing), `api/dependencies.py` (settings/DB-config dependency).
- Real test suite: `tests/test_sql_validator.py`, `tests/test_agents.py`,
  `tests/test_graph.py` — all mocked, no live MySQL/WhatsApp required.
- `config/app_config.json` + `config/app_config.schema.json` — versioned,
  non-secret app settings (thresholds, iteration caps, model name), loaded
  via `config/__init__.py` and wired into the anomaly agent (env var still
  wins if set).
- Filled in the three empty `n8n_workflows/*.json` files with working
  daily-trigger, Telegram-alert, and escalation workflows.
- `LICENSE` (MIT), `CONTRIBUTING.md`, `ARCHITECTURE.md` (with data-flow
  diagram), `.github/workflows/ci.yml` (lint + JSON validation + tests).
- `requirements-dev.txt`, Ruff config in `pyproject.toml`.

### Changed
- `Dockerfile`: runs as a non-root user, exposes 8000/8501.
- `docker-compose.yml`: API service gets a real healthcheck; dashboard now
  waits on API health instead of just process start.
- `requirements.txt`: dropped unused `twilio` dependency (WhatsApp sending
  uses `requests` directly against the Meta Cloud API).
- Moved the stray root-level `TEST.PY` manual smoke test to
  `scripts/manual_whatsapp_test.py`.

## 0.1.0
- Initial MVP: FastAPI + Streamlit + MySQL revenue monitor with anomaly
  detection and WhatsApp alerting.
