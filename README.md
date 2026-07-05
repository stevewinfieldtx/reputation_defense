# Reputation Defense

Automated review-reputation audits for local businesses. Enter a business name and
city; the system pulls its Google reviews (and up to 3 competitors'), runs AI theme
extraction with verbatim evidence, computes response-gap and velocity statistics in
plain Python, and produces a client-ready HTML report with a transparent
"revenue left on the table" estimate — every dollar figure shows its formula and
assumptions inline.

## Pipeline

```
intake form -> Outscraper (Google reviews) -> metrics.py (deterministic stats)
            -> Claude (theme clusters, spam flags, fix list; schema-validated)
            -> calculator.py (revenue math from benchmarks or client numbers)
            -> report.html (print-to-PDF friendly)
```

Key properties:
- **LLM never does math.** Response rates, response times, velocity, and all dollar
  figures are computed in Python; the LLM only clusters themes and picks quotes,
  validated against `app/analysis/schemas.py` before anything reaches a report.
- **Demo mode is free.** `/demo` runs the whole pipeline off `tests/fixtures/` with
  zero API spend (fixture dates auto-shift so velocity math stays live).
- **Everything auditable.** Assumptions table in every report labels each number
  as client-provided or benchmark.

## Run locally

```
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\uvicorn app.main:app --reload
```

Open http://localhost:8000 (intake) or http://localhost:8000/demo (sample report).
SQLite (`repdefense.db`) is used when `DATABASE_URL` is unset. Tests: `venv\Scripts\pytest`.

## Deploy (Railway)

1. Service builds from the **Dockerfile at repo root** (railway.json pins this).
2. The container binds `$PORT` (Railway injects it) — do not hardcode a port.
3. Attach a Railway Postgres and set `DATABASE_URL` from it.
4. Set `OPENROUTER_API_KEY`, `OUTSCRAPER_API_KEY`, `ADMIN_TOKEN`.

## Environment

See `.env.example`. Without `OUTSCRAPER_API_KEY` live collection fails cleanly
(demo still works); without `OPENROUTER_API_KEY` live analysis fails cleanly.
LLM calls go to any OpenAI-compatible endpoint (`LLM_BASE_URL`, default OpenRouter)
with any model id (`LLM_MODEL`, default `anthropic/claude-sonnet-4.5`).

## Routes

| Route | What |
|---|---|
| `GET /` | client intake form |
| `POST /audits` | start an audit (runs in background) |
| `GET /audits/{id}` | self-refreshing status page |
| `GET /reports/{id}` | the report (unguessable id = shareable link) |
| `GET /demo` | fixture-driven sample report, zero API cost |
| `GET /admin?token=...` | all audits + status |
| `GET /health` | liveness + which API keys are configured |

## Cost per live audit

Outscraper ~200 reviews + 2 competitors ≈ $1–3; Claude analysis ≈ $0.10–0.30.
Against a $197 audit price point.

## v2 backlog (deliberately out of scope)

Yelp/Facebook collectors (drop into `app/collectors/` per `base.py` contract),
monthly "Guardian" monitoring & alerts, AI review-response drafting, Stripe
payments, multi-user auth, per-client white-label theming.
