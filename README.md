# FinAgent — Multi-Agent Financial Analysis Platform

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)

A multi-agent financial research platform: a LangGraph-orchestrated team of agents (stock/fundamentals,
news sentiment, risk, SEC filings, and an optional bull/bear debate) gathers real market data and
synthesizes it into one cited report, streamed live to a React dashboard.

**⚠️ Disclaimer**: This is an analytical/research tool, **not a financial advisor**. All outputs are
informational and should not be interpreted as personalized financial advice.

## Architecture

```mermaid
flowchart TD
    U[User] --> FE[React Frontend]
    FE -->|SSE stream| API[FastAPI Backend]
    API --> SUP[Supervisor]
    SUP -->|fan out| STOCK[Stock & Fundamentals]
    SUP -->|fan out| NEWS[News & Sentiment]
    SUP -->|fan out| RISK[Risk Analysis]
    SUP -->|fan out| SEC[SEC Filings RAG]
    STOCK & NEWS & RISK & SEC --> JOIN[Evidence Join]
    JOIN -->|debate mode| BULL[Bull Case]
    JOIN -->|debate mode| BEAR[Bear Case]
    BULL & BEAR --> JUDGE[Judge]
    JOIN -->|normal mode| FINAL[Final Analyst]
    JUDGE --> FINAL
    FINAL --> REPORT[Cited Report]

    API --> PG[(Postgres)]
    API --> REDIS[(Redis cache)]
    SEC --> QDRANT[(Qdrant)]
    MCP[MCP Server] -.reuses.-> STOCK
    MCP -.reuses.-> NEWS
    MCP -.reuses.-> RISK
    MCP -.reuses.-> SEC
```

Each agent writes to a distinct slice of a shared LangGraph state; independent agents (stock/news/risk/SEC)
run **in parallel** in the same superstep rather than sequentially. The Final Analyst is the only agent
that synthesizes — it never invents facts, only cites what the other agents actually retrieved.

## Features

- **Real multi-agent orchestration** (LangGraph `StateGraph`, not a scripted chain) — a Supervisor routes
  each query to the agents it actually needs, running them concurrently where possible.
- **Grounded, cited output** — every claim traces back to a real yfinance/Alpha Vantage quote, a NewsAPI
  article, a live SEC EDGAR filing excerpt (via RAG over Qdrant), or a computed risk/technical metric.
  Agents explicitly say "insufficient evidence" rather than filling gaps.
- **SEC filing RAG** — fetches a company's real 10-K/10-Q from SEC EDGAR's submissions API, chunks and
  embeds it locally (sentence-transformers, no external embedding API), and answers questions from
  retrieved excerpts with filing/date citations. Falls back to clearly-labeled sample data (never silently)
  if EDGAR is unreachable.
- **Quantitative risk & portfolio tools** — volatility, Sharpe/Sortino, max drawdown, VaR/CVaR, Monte Carlo
  simulation, and PyPortfolioOpt-based allocation optimization — all computed deterministically in Python,
  not asked of the LLM (the LLM interprets the numbers, never calculates them).
- **Bull vs. Bear debate** (optional) — parallel Bull and Bear agents argue from the same evidence, a Judge
  weighs which case the evidence actually supports.
- **MCP server** — the same market/news/risk/SEC/portfolio tools, exposed over the Model Context Protocol
  (streamable-HTTP) for external MCP clients (Claude Desktop, other agents), independent of the web app.
- **Live streaming UI** — a React dashboard that streams agent progress via SSE, then renders a structured
  report (metrics, price/RSI charts, sentiment, risk, SEC citations, bull/bear cards) — not a wall of text.
- **Optional persistence** — Postgres (via SQLAlchemy async + Alembic) stores past reports, per-agent run
  traces, and saved portfolios when `DATABASE_URL` is configured; the app works with zero DB configured too.
- **Evaluation harness** — a small benchmark of real queries checked structurally (right tickers, right
  agents routed, valid output shape) plus an optional LLM-judge quality pass.

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph, LangChain |
| LLM | Groq (configurable model, e.g. `openai/gpt-oss-120b`) |
| Backend | FastAPI, Pydantic, SQLAlchemy (async) + Alembic |
| Frontend | React 18, TypeScript, Vite, Tailwind, Recharts, React Router |
| Data | yfinance, Alpha Vantage (optional), NewsAPI (optional), SEC EDGAR |
| RAG | sentence-transformers (local CPU embeddings), Qdrant |
| Quant | pandas, numpy, scipy, PyPortfolioOpt, VADER/TextBlob sentiment |
| Protocol | MCP (Model Context Protocol) SDK |
| Infra | PostgreSQL, Redis, Docker Compose |

## Prerequisites

- Python 3.12+, Node 20+
- A [Groq API key](https://console.groq.com/keys) (required — everything else below is optional)
- Docker Desktop, if running the containerized stack

## Quick Start (local, no Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env with your GROQ_API_KEY
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Redis, Qdrant, and Postgres are all **optional** in this mode — the app detects their absence and degrades
gracefully (no caching, in-memory vector search, no report persistence) rather than failing.

To enable persistence (saved reports/portfolios), point `DATABASE_URL` in `backend/.env` at a Postgres
instance (`postgresql+asyncpg://user:pass@host:port/db`) and run migrations once:

```bash
cd backend && alembic upgrade head
```

## Quick Start (Docker Compose)

```bash
# backend/.env holds your secrets; docker compose reads it for variable substitution
docker compose --env-file backend/.env up --build
```

This starts the backend (`:8000`), frontend (`:8080`), MCP server (`:8100`), Postgres (`:5434`),
Redis (`:6380`), and Qdrant (`:6334`) — non-default host ports throughout, so the stack won't collide with
anything else you might already have running locally. First run only, apply migrations:

```bash
docker compose exec backend alembic upgrade head
```

## API

Interactive docs at `http://localhost:8000/api/docs`. Key endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/analyze/stream` | Run the full multi-agent workflow, streaming per-agent progress (SSE). Body: `{"query": "...", "debate": false}` |
| `POST /api/v1/analyze/agent` | Same workflow, non-streaming |
| `GET /api/v1/reports` / `/{id}` | List/fetch persisted reports (requires `DATABASE_URL`) |
| `POST /api/v1/portfolio/analyze` | Risk metrics for a set of positions |
| `POST /api/v1/portfolio/optimize` | Max-Sharpe / min-volatility allocation |
| `GET /api/v1/companies/{ticker}` | Company profile |
| `GET /api/v1/market/{ticker}/chart` | Price/SMA/RSI series for charting |

## MCP Server

```bash
cd .. # repository root
python -m mcp_server.server   # streamable-HTTP on :8100
python mcp_server/check_client.py   # smoke test: lists tools, calls a few live
```

Exposes `get_stock_price`, `get_historical_prices`, `get_company_profile`, `get_financial_metrics`,
`search_news`, `get_sec_filings`, `search_sec_documents`, `calculate_technical_indicators`,
`calculate_risk`, `calculate_portfolio_metrics`, and `optimize_portfolio` — each a thin wrapper around the
same backend services the LangGraph agents use, so there's one implementation of every capability.

## Evaluation

```bash
cd backend
python -m evaluation.runner            # full benchmark, structural checks
python -m evaluation.runner --judge    # + an LLM-judge quality pass (extra Groq calls)
python -m evaluation.runner --case bull_bear_debate
```

Results print as a summary table and persist to `evaluation_runs` when `DATABASE_URL` is configured.

## Testing

```bash
cd backend
pytest              # fast suite (mocked LLM/services), excludes live-service tests
pytest -m slow       # includes a real end-to-end case against live Groq/yfinance
ruff check app
```

## Project Structure

```
finagent/
├── backend/
│   ├── app/
│   │   ├── agents/        # Supervisor, Stock, News, Risk, SEC, Bull, Bear, Judge, FinalAnalyst
│   │   ├── graph/          # LangGraph StateGraph + state schema
│   │   ├── services/       # market/news/risk/SEC/company/cache data access
│   │   ├── tools/          # deterministic technical/financial/portfolio calculations
│   │   ├── rag/             # chunking, local embeddings, Qdrant vector store, retriever
│   │   ├── models/          # Pydantic schemas + SQLAlchemy ORM
│   │   ├── repositories/    # the only layer that touches the ORM
│   │   ├── database/        # async engine/session (optional persistence)
│   │   └── api/             # FastAPI routes
│   ├── alembic/              # DB migrations
│   ├── evaluation/           # benchmark dataset + runner
│   └── tests/
├── mcp_server/                # MCP protocol server (reuses backend/app/services)
├── frontend/                  # React + TypeScript dashboard
└── docker-compose.yml
```

## Known Limitations

- **Groq free-tier rate limits**: a query that fans out to several agents (especially debate mode, which
  adds Bull/Bear/Judge) can involve 5-6 LLM calls; under a free-tier token-per-minute budget some calls may
  be retried or gracefully degrade to a fallback (this is handled — you'll see a warning, not a crash — but
  a paid Groq tier will be noticeably more reliable under load).
- **SEC EDGAR fetch reliability**: EDGAR is fetched live on first request per ticker and cached; if it's
  unreachable or rate-limits the request, the SEC agent explicitly labels its answer as sample/demo data
  rather than presenting it as a live filing.
- **No authentication**: single-tenant by design for this project's scope — no user accounts, all
  persisted reports/portfolios are shared, not per-user.
- **Frontend bundle size**: Recharts pulls the production JS bundle above the default 500KB warning
  threshold; not yet code-split.

## License

MIT
