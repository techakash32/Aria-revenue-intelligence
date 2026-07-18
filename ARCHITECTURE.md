# Architecture

## Overview

Revenue Guardian is an autonomous agent pipeline: it pulls recent revenue
data from MySQL, statistically detects anomalies, optionally explains them
with an LLM (Groq), and sends a WhatsApp alert when confidence/severity
clear a threshold. Every run is logged to MySQL as a structured decision
record for auditability, and surfaced through a FastAPI service and a
Streamlit dashboard.

## Data flow

```mermaid
flowchart LR
    subgraph Trigger
        A[GitHub Actions cron] -->|POST /trigger/daily-monitor| API
        B[Streamlit "Run Monitor"] --> API
        C[Chat message] --> API
    end

    API[FastAPI] --> ORCH[Orchestrator]

    subgraph Pipeline
        ORCH --> ANALYTICS[Analytics Agent\nSQL: daily/category/product revenue]
        ANALYTICS --> ANOMALY[Anomaly Agent\nstatistical threshold + severity]
        ANOMALY --> ACTION[Action Agent\nWhatsApp alert if severity/confidence pass]
    end

    ANALYTICS -->|SELECT-only, validated| MYSQL[(MySQL\ndaily_sales)]
    ACTION --> WA[WhatsApp Cloud API]
    ACTION --> LOG[Decision Logger]
    LOG --> MYSQL2[(MySQL\nagent_decisions)]

    ORCH --> REPORT[Final report]
    REPORT --> API
    API --> DASH[Streamlit Dashboard]
```

## Why this shape

- **Deterministic-first pipeline.** `graph/agent_graph.py` and `graph/router.py`
  define LangGraph-style routing (`analytics → anomaly → action → report`),
  but the MVP runs it as a plain async pipeline (`pipelines/monitor_pipeline.py`)
  so the product works without depending on LangGraph's runtime being wired
  up. The router logic is unit-tested independently (`tests/test_graph.py`)
  and ready to back a real LangGraph `StateGraph` without changing callers.
- **Safety-first SQL.** All agent-issued SQL goes through
  `safety.sql_validator.validate_query`, which parses with `sqlparse`,
  rejects anything that isn't a single `SELECT`, and blocks mutating
  keywords. Queries also run through `safety.query_timeout` on a worker
  thread with a hard timeout, so a slow query can't hang a request.
  The app additionally tries a dedicated read-only MySQL user first
  (`readonly_user`, see `safety/readonly_user.sql`) and only falls back to
  the app user if that's unavailable.
- **Confidence-gated actions.** The action agent only sends a WhatsApp alert
  when both severity (`medium`/`high`) and confidence (`>= 0.5`) clear the
  bar — see `agents/action_agent.py`. Skipped alerts still record *why*
  (`alert_skip_reason`) for the decision log.
- **Config vs. secrets.** Tunable-but-non-secret values (thresholds,
  iteration caps, model name) live in `config/app_config.json` (schema in
  `config/app_config.schema.json`) so they're reviewable in git history.
  Secrets (`.env`, gitignored) can still override them at runtime.
- **Graceful degradation.** No Groq key → deterministic text explanations
  (`tools/llm_tool.py`). No MySQL → dashboard falls back to
  `data/sample_sales.csv`. No WhatsApp credentials → alerts are skipped with
  a logged reason, not a crash.

## Module map

| Path | Responsibility |
|---|---|
| `agents/` | Analytics, anomaly detection, action (alerting), orchestrator |
| `graph/` | LangGraph-style state/router definitions for the agent pipeline |
| `pipelines/` | Ingest CSV → MySQL, run the monitor pipeline, unified CLI |
| `tools/` | SQL execution, WhatsApp send, Groq LLM calls, chart rendering |
| `safety/` | SQL validation, query timeout enforcement, read-only DB user setup |
| `observability/` | Decision logging to MySQL, LangSmith tracing bootstrap, lightweight tracer |
| `memory/` | Short-term rolling chat buffer, semantic (Chroma) recall, static recovery heuristics |
| `api/` | FastAPI app: health, chat, trigger routes |
| `dashboard/` | Streamlit UI: KPIs, chat, decision log |
| `config/` | Versioned app settings + JSON schema |
| `data/` | Sample CSV + DB seeding script |
| `tests/` | Unit tests (mocked, no live DB required) |
