# main.py: the FastAPI app and all of its routes.
# It wires together validation, the database, the analysis builder, and the LLM.
# Keep route functions short: they parse input, call a helper, and return JSON.

import time

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.analysis import NotEnoughData, PortfolioNotFound, build_analysis
from app.config import ALLOWED_ORIGINS
from app.database import fetch_all, save_portfolio
from app.llm import DISCLAIMER, LLMUnavailable, generate_insights
from app.validation import validate_holdings

BENCHMARK_TICKER = "SPY"

# Simple in-memory rate limit for the insights endpoint:
# at most this many requests per IP per hour.
INSIGHTS_LIMIT_PER_HOUR = 10
ONE_HOUR_IN_SECONDS = 3600

# Maps a client IP to a list of recent request timestamps.
insights_request_times = {}

app = FastAPI(title="Portfolio Risk and Performance Analytics")

# Allow the frontend origins listed in the ALLOWED_ORIGINS env var (comma separated).
allowed_origins_list = [origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Request models ----

class HoldingIn(BaseModel):
    ticker: str
    weight: float


class PortfolioIn(BaseModel):
    name: str = ""
    holdings: list[HoldingIn]


# ---- Helper functions ----

def get_known_tickers():
    # Return the set of tickers that are not the benchmark.
    rows = fetch_all("SELECT ticker FROM securities WHERE is_benchmark = FALSE")
    return {row["ticker"] for row in rows}


def is_rate_limited(client_ip):
    # Return True if this IP has used up its hourly insight requests.
    now = time.time()
    recent_times = insights_request_times.get(client_ip, [])

    # Keep only the timestamps from the last hour.
    still_recent = [t for t in recent_times if now - t < ONE_HOUR_IN_SECONDS]
    insights_request_times[client_ip] = still_recent

    if len(still_recent) >= INSIGHTS_LIMIT_PER_HOUR:
        return True

    still_recent.append(now)
    return False


# ---- Routes ----

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/securities")
def list_securities():
    # Return all non-benchmark securities, sorted by ticker.
    rows = fetch_all(
        "SELECT ticker, name, sector FROM securities "
        "WHERE is_benchmark = FALSE ORDER BY ticker"
    )
    return rows


@app.post("/portfolios")
def create_portfolio(portfolio_in: PortfolioIn):
    # Turn the Pydantic models into plain dictionaries for validation.
    holdings = [{"ticker": h.ticker, "weight": h.weight} for h in portfolio_in.holdings]

    known_tickers = get_known_tickers()
    errors = validate_holdings(holdings, known_tickers, BENCHMARK_TICKER)
    if errors:
        return JSONResponse(status_code=422, content={"errors": errors})

    # Default the name if the user left it blank.
    name = portfolio_in.name.strip() if portfolio_in.name else ""
    if not name:
        name = "My portfolio"

    portfolio_id = save_portfolio(name, holdings)
    return {"id": portfolio_id}


@app.get("/portfolios/{portfolio_id}/analysis")
def get_analysis(portfolio_id: int, years: int = Query(5)):
    # years must be 1, 3, or 5.
    if years not in (1, 3, 5):
        return JSONResponse(status_code=400, content={"error": "years must be 1, 3, or 5."})

    try:
        return build_analysis(portfolio_id, years)
    except PortfolioNotFound:
        return JSONResponse(status_code=404, content={"error": "Portfolio not found"})
    except NotEnoughData as error:
        return JSONResponse(status_code=400, content={"error": str(error)})
    except Exception as error:
        # Log the real details on the server, but do not leak them to the user.
        print(f"Unexpected error in get_analysis: {error}")
        return JSONResponse(status_code=500, content={"error": "Something went wrong"})


@app.post("/portfolios/{portfolio_id}/insights")
def get_insights(portfolio_id: int, request: Request, years: int = Query(5)):
    if years not in (1, 3, 5):
        return JSONResponse(status_code=400, content={"error": "years must be 1, 3, or 5."})

    # Rate limit by client IP to protect the API key.
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Too many explanation requests. Please try again later."},
        )

    try:
        analysis = build_analysis(portfolio_id, years)
    except PortfolioNotFound:
        return JSONResponse(status_code=404, content={"error": "Portfolio not found"})
    except NotEnoughData as error:
        return JSONResponse(status_code=400, content={"error": str(error)})
    except Exception as error:
        print(f"Unexpected error building analysis for insights: {error}")
        return JSONResponse(status_code=500, content={"error": "Something went wrong"})

    try:
        insights_text = generate_insights(analysis)
    except LLMUnavailable as error:
        print(f"LLM unavailable: {error}")
        return JSONResponse(
            status_code=503,
            content={"error": "The explanation service is unavailable right now."},
        )

    return {"insights": insights_text, "disclaimer": DISCLAIMER}
