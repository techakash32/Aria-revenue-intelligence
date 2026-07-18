# ARIA — Revenue Guardian

An autonomous agent that watches your MySQL revenue data, catches anomalies
before you do, explains them in plain language, and alerts your team on
WhatsApp — with every decision logged for audit.

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](api/main.py)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-ff4b4b)](dashboard/app.py)

## Why this project

Most "anomaly detection" demos stop at a Jupyter notebook. Revenue Guardian
is wired end-to-end: a real orchestration pipeline, SQL-injection-safe data
access, confidence-gated alerting, a decision audit log, a dashboard, an API,
and a scheduled trigger for daily monitoring — the shape of an actual
production revenue-ops tool, at MVP scale.

## Features

- **Analytics agent** — pulls daily / category / product revenue from MySQL.
- **Anomaly agent** — statistical drop/spike detection with severity and a
  confidence score; requires a minimum data window before it will ever alert.
- **Action agent** — sends a WhatsApp alert only when severity *and*
  confidence clear a bar; otherwise logs *why* it skipped.
- **LLM explanations (optional)** — Groq-backed plain-language anomaly
  interpretation, with a deterministic text fallback when no key is set.
- **Decision log** — every run is written to MySQL (`agent_decisions`) and
  browsable in the dashboard.
- **SQL safety layer** — every agent-issued query is parsed and validated
  (`SELECT`-only, single statement, blocked-keyword list) and runs with a
  hard timeout on a worker thread.
- **Dashboard** (Streamlit) — live KPIs, revenue trend chart, chat interface,
  decision log viewer. Falls back to bundled sample data if MySQL is down.
- **API** (FastAPI) — `/health`, `/chat`, `/trigger/daily-monitor`.
- **Scheduled trigger** — GitHub Actions cron calls `/trigger/daily-monitor`
  directly (`.github/workflows/daily_trigger.yml`), no extra service to host.
- **Dockerized** — `docker compose up --build` runs MySQL, Chroma, API, and
  dashboard together, with healthchecks.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full data-flow diagram and
design rationale.

## Tech stack

| Layer | Tech |
|---|---|
| Orchestration | Python asyncio pipeline, LangGraph-style state/router |
| Data | MySQL, SQLAlchemy/`mysql-connector-python` |
| LLM | Groq (`llama-3.1-8b-instant`), LangSmith tracing (optional) |
| Vector memory | Chroma |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit |
| Alerting | WhatsApp Cloud API (Meta) |
| Automation | GitHub Actions cron (`daily_trigger.yml`) |
| Testing | pytest, pytest-asyncio |
| Quality | Ruff, GitHub Actions CI |
| Packaging | Docker, docker-compose |

## Project layout

```
revenue-guardian/
├── agents/          # analytics, anomaly, action, orchestrator
├── graph/           # LangGraph-style state + router
├── pipelines/        # ingest CSV, run monitor, unified CLI
├── tools/           # SQL, WhatsApp, Groq LLM, chart rendering
├── safety/          # SQL validation, query timeout, readonly DB user SQL
├── observability/   # decision logger, tracer, LangSmith bootstrap
├── memory/          # short-term buffer, semantic (Chroma) store, heuristics
├── api/             # FastAPI app + routes
├── dashboard/        # Streamlit app + components
├── config/          # app_config.json + JSON schema
├── data/            # sample CSV + DB seed script
├── tests/           # pytest suite (mocked, no live DB required)
└── scripts/         # manual/one-off smoke tests
```

## Quickstart (local Python)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env             # fill in your own values — never commit .env
python data/seed_db.py           # optional: seed MySQL with sample data

python main.py                   # prints available entry points
uvicorn api.main:app --reload    # API on http://localhost:8000
streamlit run app.py             # dashboard on http://localhost:8501
```

The dashboard and API both fall back to `data/sample_sales.csv` when MySQL
isn't reachable, so you can try the product with zero setup.

### Optional integrations

**Groq LLM** (plain-language anomaly explanations):
```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```
Without it, anomaly explanations fall back to deterministic text — the app
still runs.

**WhatsApp Cloud API** (alerts):
```env
WHATSAPP_TOKEN=your_meta_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_RECIPIENT_ID=recipient_number
```
Without it, the action agent logs `alert_skip_reason` instead of sending.

**Read-only MySQL user** (recommended — agents use this first, falling back
to the app user only if it's unavailable):
```sql
CREATE USER IF NOT EXISTS 'readonly_user'@'localhost' IDENTIFIED BY 'readonly_pass';
GRANT SELECT ON revenue.* TO 'readonly_user'@'localhost';
CREATE USER IF NOT EXISTS 'readonly_user'@'%' IDENTIFIED BY 'readonly_pass';
GRANT SELECT ON revenue.* TO 'readonly_user'@'%';
FLUSH PRIVILEGES;
```
(Or just run `safety/readonly_user.sql` — docker-compose does this
automatically on first boot.)

## Docker Compose

```bash
docker compose up --build
```

- API: http://localhost:8000/health
- Dashboard: http://localhost:8501

## Running the pipeline directly

```bash
python -m pipelines.run_pipeline monitor
python -m pipelines.run_pipeline monitor --query "check today's revenue"
python -m pipelines.run_pipeline ingest data/sample_sales.csv
```

## Testing

```bash
pip install -r requirements-dev.txt
ruff check .      # lint
pytest -v         # unit tests — mocked, no live MySQL/WhatsApp required
```

CI (`.github/workflows/ci.yml`) runs lint, JSON validation for the app
config, and the full test suite on every push/PR.

## Security notes

- All agent-issued SQL passes through `safety.sql_validator.validate_query`:
  single `SELECT` statements only, blocked-keyword list, parsed via
  `sqlparse` (not string matching). See `tests/test_sql_validator.py`,
  including a regression test for a stacked-statement bypass that this
  hardening pass fixed.
- Queries run with a hard timeout (`safety/query_timeout.py`) on a worker
  thread so a slow query can't hang a request.
- `.env` is gitignored; `.env.example` is the committed template. If you're
  picking this repo up from an earlier export that had real keys in `.env`,
  rotate them — see `CHANGELOG.md`.

## Roadmap

- [ ] Wire `graph/agent_graph.py` to a real LangGraph `StateGraph` (router
      logic is already unit-tested and ready).
- [ ] Persist `memory.semantic_store` outcomes automatically from the
      decision logger instead of manual calls.
- [ ] Add category/product-level anomaly detection (currently daily-revenue
      only).
- [ ] Auth on the FastAPI routes before any non-local deployment.

## License

MIT — see [LICENSE](LICENSE).
