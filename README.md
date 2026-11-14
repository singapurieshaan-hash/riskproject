# Portfolio Risk and Performance Analytics Platform

## 1. What it does

This is a web app for analyzing a stock portfolio against the S&P 500 (ticker `SPY`).
You pick stocks from a fixed list of about 34 large US companies, give each a weight that
adds up to 100%, and click **Analyze**. The app then shows performance and risk metrics
(total return, annualized return, volatility, Sharpe ratio, maximum drawdown, beta, and
1-day 95% Value at Risk), two charts (cumulative return and drawdown), a per-stock CAPM
regression table, and a plain-language explanation written by an LLM using only the
numbers the code already calculated.

**Live app:** _(add your deployed Vercel URL here)_

## 2. Screenshot

_(Placeholder — add a real screenshot of the dashboard here once deployed.)_

```
+-----------------------------------------------------------+
|  Portfolio Risk & Performance Analytics                   |
|  [ Build your portfolio ]  [ Analyze ]                    |
|  [ Metric cards ... ]                                     |
|  [ Cumulative chart ]   [ Drawdown chart ]                |
|  [ Regression table ]   [ Explain my results ]           |
+-----------------------------------------------------------+
```

## 3. Architecture

```
Market data (yfinance + FRED CSV)
        |
        v
  Ingestion script  (backend/scripts/ingest.py)   <-- run by hand
        |
        v
     PostgreSQL     (securities, prices, risk_free_rates, portfolios, holdings)
        |
        v
   FastAPI backend  (backend/app) -- validation, metrics, CAPM regression, analysis
        |                                   |
        v                                   v
   React dashboard (frontend)        LLM assistant (Google Gemini)
```

- **Data source:** `yfinance` for adjusted daily prices, FRED's `DTB3` CSV for the 3-month
  T-bill risk-free rate.
- **Ingestion script:** downloads, cleans, and upserts the data into Postgres. Safe to re-run.
- **Postgres:** stores securities, adjusted prices, risk-free rates, and saved portfolios.
- **FastAPI:** validates holdings, loads prices, computes all the math, and serves JSON.
- **React dashboard:** builds the portfolio, shows cards/charts/table, and requests insights.
- **LLM:** explains the already-calculated numbers in plain language (never invents numbers).

## 4. Methodology and assumptions

- **Returns** are simple daily returns: `price_today / price_yesterday - 1`.
- A year has **252 trading days**.
- The portfolio uses **constant weights, rebalanced every day**. The daily portfolio return
  is the sum of (weight × stock return).
- The **risk-free rate** is the 3-month T-bill (FRED `DTB3`), converted to a daily fraction:
  `rate_pct / 100 / 252`. If no rate data is loaded, Sharpe uses 0% and a warning is shown.
- **Beta, Sharpe, and the regressions** are all computed on daily returns.
- **Annualized return** is geometric: the total growth raised to `252 / number_of_days`.
- **Value at Risk (VaR)** is historical (the 5th-percentile daily loss) and reported as a
  positive number meaning a loss (0.02 means a 2% one-day loss).
- **CAPM regression** per stock: `stock excess return = alpha + beta × market excess return`.
  Alpha is reported annualized (daily alpha × 252).
- Only dates where **every holding and SPY** have a price are used (the price table is
  dropped to the common set of dates).

### Assumptions / choices made where the spec left it open

- Company names in `securities` use common full legal names (e.g. "Apple Inc.").
- The analysis window for "N years" is measured back from the latest date in the database,
  not from today's calendar date.
- The default portfolio name is "My portfolio" when the user leaves it blank.
- The LLM model name is read from `LLM_MODEL`; the example uses `gemini-2.5-flash`. Set it to
  a current model available on your Google Gemini (AI Studio) account.

## 5. Limitations

- Historical data does **not** predict the future.
- `yfinance` is an **unofficial** data source and can change or break.
- The fixed 34-stock universe has **survivorship bias** — these are today's large, surviving
  companies, not the companies that existed years ago.
- **Beta estimates change over time**; a single number is only a summary of one window.
- **VaR assumes the past resembles the future**, which may not hold in a crisis.
- Daily rebalancing **ignores trading costs and taxes**.
- The LLM only **explains** the numbers and can still be imperfect; it is not advice.

## 6. How to run locally

### Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer
- A running PostgreSQL database (local install or Docker)

### Backend

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env and set DATABASE_URL, LLM_API_KEY, and LLM_MODEL

# 4. Create the database tables
python scripts/apply_schema.py

# 5. Download and load the market data (needs internet; takes a minute)
python scripts/ingest.py

# 6. Run the tests (all should pass)
pytest -v

# 7. Start the API
uvicorn app.main:app --reload
# Open http://localhost:8000/docs to try the endpoints
```

> Tip: a quick local Postgres with Docker:
> `docker run --name portfolio-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=portfolio -p 5432:5432 -d postgres`

### Frontend

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure the backend URL
cp .env.example .env
# VITE_API_URL should point at the backend, e.g. http://localhost:8000

# 3. Start the dev server
npm run dev
# Open the URL Vite prints (usually http://localhost:5173)
```

### Running the tests

From the `backend` folder, with the virtual environment active:

```bash
pytest -v
```

The tests cover the metric math (`test_metrics.py`), the CAPM regression
(`test_regression.py`), and the holdings validation (`test_validation.py`). They do **not**
need a database or internet connection.

## 7. Tech stack

| Part | Choice |
|---|---|
| Backend language | Python 3.11+ |
| Web framework | FastAPI (run with Uvicorn) |
| Database | PostgreSQL via `psycopg2-binary` (plain SQL, no ORM) |
| Data & math | `pandas`, `numpy`, `statsmodels` |
| Market data | `yfinance` (adjusted prices), FRED CSV (`DTB3` risk-free rate) |
| LLM | Google Gen AI SDK (`google-genai`), model from `LLM_MODEL` |
| Tests | `pytest`, `httpx` |
| Frontend | React + Vite (plain JavaScript), `recharts`, one plain CSS file |
| Hosting | Backend + Postgres on Render/Railway, frontend on Vercel |

## 8. Deployment notes

See section 14 of the build spec. In short: create a hosted Postgres, run
`apply_schema.py` then `ingest.py` against it from your machine, deploy the `backend`
folder as a web service (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`), deploy the
`frontend` folder on Vercel with `VITE_API_URL` set to the backend URL, then update the
backend's `ALLOWED_ORIGINS` to the final frontend URL and redeploy.

Free hosting tiers can go to sleep after inactivity, so the **first request may be slow**
while the service wakes up.
