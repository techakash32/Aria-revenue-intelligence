# ARIA — Revenue Guardian

MySQL-backed revenue monitoring agent system. Detects revenue anomalies and
data quality issues, logs every decision, alerts via WhatsApp, and answers
questions through a chat UI. FastAPI + Streamlit + LangGraph-shaped pipeline.

---

## 1. What it does

1. Reads daily sales from MySQL (`daily_sales` table).
2. Computes latest-day revenue vs a rolling baseline → flags statistical anomalies.
3. Runs 9 independent row-level data-quality checks (negative values, future dates, outliers, etc).
4. Decides whether to alert (severity + confidence rules).
5. Sends a WhatsApp message if the bar is cleared.
6. Logs the full decision (input, output, confidence, action) to MySQL.
7. Everything is queryable via chat (Streamlit dashboard or `/chat` API).

---

## 2. Tech stack

| Layer | Tech |
|---|---|
| DB | MySQL (`daily_sales`, `agent_decisions` tables) |
| API | FastAPI |
| Dashboard | Streamlit |
| Agent orchestration | Custom async orchestrator (LangGraph-shaped, see §6) |
| LLM | Groq (`llama-3.1-8b-instant`) |
| Vector memory | ChromaDB (optional, `memory/semantic_store.py`) |
| Alerting | WhatsApp Cloud API (Meta) |
| Automation | GitHub Actions cron (`.github/workflows/daily_trigger.yml`) |
| Charts | matplotlib (Agg backend, base64 PNG) |
| SQL safety | `sqlparse` — SELECT-only validator |

---

## 3. Project layout

```
agents/            analytics, anomaly, data_quality, action agents + orchestrator
api/                FastAPI app: routes for /health, /chat, /trigger
config/             app_config.json (thresholds, model name) + JSON schema + loader
dashboard/          Streamlit app: KPI cards, chat, decision log
data/               sample_sales.csv, seed_db.py
graph/              AgentState typing + router (LangGraph-shaped, not yet wired to langgraph lib)
memory/             short_term (in-process buffer), semantic_store (Chroma), heuristics (recovery rules)
observability/      decision_logger (MySQL), tracer (step timing), langsmith_setup (optional)
pipelines/          monitor_pipeline (main flow), ingest_pipeline (CSV loader), run_pipeline (CLI)
safety/             sql_validator, query_timeout, readonly_user.sql
scripts/            manual_whatsapp_test.py
tools/               sql_tool, whatsapp_tool, chart_tool, llm_tool
tests/               test_agents.py, test_graph.py, test_sql_validator.py, conftest.py
main.py              prints run instructions
app.py               `streamlit run app.py` entry point
Dockerfile, docker-compose.yml
```

---

## 4. Setup

```bash
git clone https://github.com/techakash32/Aria-revenue-intelligence.git
cd Aria-revenue-intelligence
pip install -r requirements.txt
```

Create `.env` in the project root (no `.env.example` is committed — build it from
the variable list below).

### 4.1 Required environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE` | everything DB | connection target |
| `MYSQL_USER`, `MYSQL_PASSWORD` | writes: seed, decision logger, ingest | full-access DB user |
| `MYSQL_READONLY_USER`, `MYSQL_READONLY_PASSWORD` | reads: sql_tool, kpi_cards | read-only user — run `safety/readonly_user.sql` once to create it |
| `GROQ_API_KEY` | `tools/llm_tool.py` | Groq LLM for chat answers |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | `tools/whatsapp_tool.py` | Meta WhatsApp Cloud API creds |
| `WHATSAPP_RECIPIENT_ID` | `tools/whatsapp_tool.py` | phone number alerts are sent to |
| `LANGCHAIN_API_KEY` | `observability/langsmith_setup.py` | optional — enables LangSmith tracing |
| `ANOMALY_THRESHOLD_PERCENT` | overrides `config/app_config.json` | anomaly trigger % (default 10.0) |
| `QUERY_TIMEOUT_SECONDS` | `tools/sql_tool.py` | per-query timeout, default 5s |
| `MAX_ITERATIONS` | api/dependencies.py | pipeline safety cap, default 8 |
| `CHROMA_PERSIST_DIR` | `memory/semantic_store.py` | local Chroma DB path, default `./chroma_db` |
| `API_HOST`, `API_PORT`, `LOG_LEVEL` | FastAPI | server config |

Non-secret defaults (thresholds, model name, allowed categories) live in
`config/app_config.json`, validated against `config/app_config.schema.json`.

### 4.2 Database setup

```bash
mysql -u root -p < safety/readonly_user.sql   # creates readonly_user
python data/seed_db.py                        # creates daily_sales + seeds 20 rows
```

`agent_decisions` table is auto-created on first run by `observability/decision_logger.py`.

---

## 5. Running it

| Goal | Command |
|---|---|
| One-off monitor run (CLI) | `python -m pipelines.run_pipeline monitor` |
| Monitor with a custom query | `python -m pipelines.run_pipeline monitor --query "check today's revenue"` |
| Ingest a CSV | `python -m pipelines.run_pipeline ingest data/sample_sales.csv` |
| API server | `uvicorn api.main:app --reload` → docs at `/docs` |
| Trigger via API | `curl -X POST http://localhost:8000/trigger/daily-monitor` |
| Dashboard | `streamlit run app.py` (or `streamlit run dashboard/app.py`) |
| Everything (Docker) | `docker compose up --build` → API on `:8000`, dashboard on `:8501`, MySQL on `:3306`, Chroma on `:8001` |
| Manual WhatsApp test | `python scripts/manual_whatsapp_test.py` |
| Scheduled daily run | GitHub Actions cron in `.github/workflows/daily_trigger.yml` — needs repo secret `API_BASE_URL` pointing at your deployed API |

---

## 6. How a monitor run works (`pipelines/monitor_pipeline.py`)

Runs `agents/orchestrator.py` in order:

1. **`analytics_agent`** — pulls last 14 distinct dates from `daily_sales`
   (`SELECT date, SUM(total_revenue) ... GROUP BY date`), plus category/top-product
   breakdowns. Builds `latest_revenue`, `baseline_revenue` (avg of up to 7 prior days),
   `change_percent`.
2. **`data_quality_agent`** — runs 9 independent read-only checks (see §7),
   independent of the revenue-trend calc.
3. **`anomaly_agent`** — flags a statistical anomaly if `|change_percent| >=`
   `ANOMALY_THRESHOLD_PERCENT` (default 10%). Severity: `high` if ≥50%, else `medium`.
   Needs ≥3 distinct days of data or returns `insufficient_data`.
4. **`action_agent`** — alerts via WhatsApp if `(severity in [medium, high] AND confidence >= 0.5)`
   **OR** a critical/high data-quality issue exists. Builds the alert text, calls
   `tools/whatsapp_tool.send_whatsapp_alert`.
5. Result + full state logged to `agent_decisions` via `observability/decision_logger.py`.

`graph/` (`state.py`, `router.py`, `agent_graph.py`) defines the same flow in
LangGraph-shaped types (`AgentState` TypedDict, `route_next`) as scaffolding for
a future real LangGraph supervisor — today `run_agent_graph()` just calls
`run_monitor()` directly.

---

## 7. Data quality checks (`agents/data_quality_agent.py`)

All against `daily_sales`, all read-only SELECTs, capped at 5 sample rows each:

| Check | Severity |
|---|---|
| Negative quantity | critical |
| Negative unit price | critical |
| `total_revenue != quantity * unit_price` | high |
| Sale date in the future | high |
| Zero unit price | medium |
| Same `product_id` mapped to >1 `product_name` | medium |
| Quantity >3× std-dev from mean (config: `outlier_std_dev`) | medium |
| `product_name` is NULL | low |
| Category outside allowed list (config: `allowed_categories`) | low |

A failed check (e.g. `STDDEV` needs ≥1 row) is recorded as its own low-severity
issue rather than crashing the pipeline.

---

## 8. Chat / LLM (`tools/llm_tool.py`)

- `answer_business_question(message, context)` builds a prompt from `message` +
  a `context` dict, calls Groq (`llama-3.1-8b-instant`, temp 0.2, max 80 words).
- Prompt instructs the LLM to only use the given context and say what's missing
  if context is empty.
- **Dashboard** (`dashboard/components/chat_interface_fixed.py`) caches the last
  `run_monitor()` result in `st.session_state.last_monitor_result` and passes it
  as context on every non-monitor-triggering message — so follow-up questions
  ("why is it -48%?", "what's the baseline revenue?") get real numbers instead
  of "I need more context."
  - ⚠️ `dashboard/components/chat_interface.py` (original) does **not** do this —
    it calls `answer_business_question(prompt)` with no context at all. Swap the
    import in `dashboard/app.py` to use `chat_interface_fixed` to get this fix.
  - ⚠️ `api/routes/chat.py` has the same original bug — no session cache, no
    context passed. Not yet patched.
- `should_run_monitor(message)` (fixed version) only re-runs the full SQL
  pipeline on an explicit action word (`run`, `check`, `trigger`, `refresh`,
  `recheck`, `rerun`) — not on topic words like "revenue" or "drop", which used
  to force a re-run even for a context question.
- Static greeting handled separately, before the LLM is called.

---

## 9. Safety

- `safety/sql_validator.py` — every SQL string (from any agent) is parsed with
  `sqlparse`: rejects empty/unparseable input, rejects multi-statement input
  (stacked queries), rejects anything that isn't `SELECT`, blocks
  `DROP/DELETE/UPDATE/INSERT/TRUNCATE/ALTER/CREATE/REPLACE` keywords even inside
  a nominally-SELECT statement.
- `safety/query_timeout.py` — every query runs in a thread with a hard timeout
  (`QUERY_TIMEOUT_SECONDS`, default 5s), raises `QueryTimeout` on expiry.
- `tools/sql_tool.py` connects with `MYSQL_READONLY_USER` first, falls back to
  the full-access user only if the read-only connection fails.

---

## 10. Testing / CI

```bash
pip install -r requirements_dev.txt
ruff check .      # lint
pytest -v         # unit tests — mocked, no live MySQL/WhatsApp required
```

`tests/conftest.py` provides a `db_connection` fixture for integration tests
that's skipped (not failed) if MySQL isn't reachable — most of the suite
doesn't need it.

`.github/workflows/ci.yml` — lint, `config/app_config.json` schema validation,
full test suite, on every push/PR.
`.github/workflows/docker-image.yml` — builds the Docker image.
`.github/workflows/daily_trigger.yml` — cron → `POST {API_BASE_URL}/trigger/daily-monitor`.

---

## 11. Known gaps / roadmap

- `api/routes/chat.py` chat endpoint doesn't cache/pass monitor context yet (dashboard fix not ported to API).
- `graph/` types exist but the orchestrator doesn't run through the actual `langgraph` library yet — it's a deterministic async chain shaped to drop `langgraph` in later without an API change.
- `memory/semantic_store.py` (Chroma) and `memory/heuristics.py` (recovery-action rules) are built but not yet wired into the orchestrator's decision path.
- No `.env.example` committed — build `.env` from the variable table in §4.1.
