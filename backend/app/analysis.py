# analysis.py: loads price data, calls the metric functions, and builds
# the full JSON response for one portfolio. This is the glue between the
# database, the math (metrics.py / regression.py), and the API (main.py).

import pandas as pd

from app import metrics
from app.database import fetch_all
from app.regression import run_capm_regression

BENCHMARK_TICKER = "SPY"
MINIMUM_TRADING_DAYS = 60


class PortfolioNotFound(Exception):
    # Raised when a portfolio id does not exist in the database.
    pass


class NotEnoughData(Exception):
    # Raised when there are too few overlapping price days to analyze.
    pass


def round6(value):
    # Round a number to 6 decimals, but keep None as None.
    if value is None:
        return None
    return round(float(value), 6)


def get_price_table(tickers, years):
    # Load a price table (rows = dates, columns = tickers) for the given tickers
    # plus the benchmark, covering the most recent "years" of data we have.

    # Always include the benchmark so we can compare against it.
    wanted_tickers = list(tickers)
    if BENCHMARK_TICKER not in wanted_tickers:
        wanted_tickers.append(BENCHMARK_TICKER)

    # Find the latest date we actually have prices for.
    latest_rows = fetch_all("SELECT MAX(price_date) AS latest FROM prices")
    latest_date = latest_rows[0]["latest"]
    if latest_date is None:
        raise NotEnoughData("No price data is loaded in the database.")

    # The window starts "years" years before that latest date.
    start_date = latest_date - pd.DateOffset(years=years)
    start_date = start_date.date()

    # Build a SQL "IN (...)" list safely with placeholders.
    placeholders = ", ".join(["%s"] * len(wanted_tickers))
    sql = (
        "SELECT ticker, price_date, adj_close "
        "FROM prices "
        f"WHERE ticker IN ({placeholders}) AND price_date >= %s "
        "ORDER BY price_date"
    )
    params = wanted_tickers + [start_date]
    rows = fetch_all(sql, params)

    # Turn the flat rows into a table with dates as the index.
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise NotEnoughData("No price data found for the requested tickers.")

    price_table = frame.pivot(index="price_date", columns="ticker", values="adj_close")

    # Keep only dates where every requested ticker has a price.
    price_table = price_table.dropna()

    # Prices come back as Decimal; convert them to plain floats.
    price_table = price_table.astype(float)

    price_table.index = pd.to_datetime(price_table.index)
    return price_table


def load_portfolio(portfolio_id):
    # Load the portfolio header and its holdings (joined with security info).
    portfolio_rows = fetch_all(
        "SELECT id, name FROM portfolios WHERE id = %s",
        (portfolio_id,),
    )
    if not portfolio_rows:
        raise PortfolioNotFound(f"Portfolio {portfolio_id} not found.")

    portfolio = portfolio_rows[0]

    holding_rows = fetch_all(
        "SELECT h.ticker, h.weight, s.name, s.sector "
        "FROM portfolio_holdings h "
        "JOIN securities s ON s.ticker = h.ticker "
        "WHERE h.portfolio_id = %s "
        "ORDER BY h.ticker",
        (portfolio_id,),
    )

    # Convert each weight from Decimal to float for easy math later.
    holdings = []
    for row in holding_rows:
        holdings.append(
            {
                "ticker": row["ticker"],
                "name": row["name"],
                "sector": row["sector"],
                "weight": float(row["weight"]),
            }
        )
    return portfolio, holdings


def load_daily_risk_free(dates, warnings):
    # Load the risk-free-rate history and match it to the given trading dates.
    # If there is no rate data, fall back to 0 and record a warning.
    rate_rows = fetch_all("SELECT rate_date, rate_pct FROM risk_free_rates ORDER BY rate_date")
    if not rate_rows:
        warnings.append("Risk-free rate data unavailable; Sharpe ratio uses 0%.")
        return 0.0

    rate_frame = pd.DataFrame(rate_rows)
    rate_frame["rate_date"] = pd.to_datetime(rate_frame["rate_date"])
    rate_series = pd.Series(
        rate_frame["rate_pct"].astype(float).values,
        index=rate_frame["rate_date"],
    )
    return metrics.daily_risk_free(rate_series, dates)


def build_weights_dict(holdings):
    # Turn the list of holdings into a simple {ticker: weight} dictionary.
    weights = {}
    for holding in holdings:
        weights[holding["ticker"]] = holding["weight"]
    return weights


def build_metrics_block(returns, daily_rf):
    # Run summarize() and round every value for the JSON response.
    summary = metrics.summarize(returns, daily_rf)
    rounded = {}
    for key, value in summary.items():
        rounded[key] = round6(value)
    return rounded


def build_chart_data(portfolio_returns, benchmark_returns):
    # Build the cumulative-return and drawdown series for both lines.
    portfolio_cumulative = (1 + portfolio_returns).cumprod() - 1
    benchmark_cumulative = (1 + benchmark_returns).cumprod() - 1
    portfolio_drawdown = metrics.drawdown_series(portfolio_returns)
    benchmark_drawdown = metrics.drawdown_series(benchmark_returns)

    cumulative = []
    drawdown = []
    for date in portfolio_returns.index:
        date_text = date.strftime("%Y-%m-%d")
        cumulative.append(
            {
                "date": date_text,
                "portfolio": round6(portfolio_cumulative.loc[date]),
                "benchmark": round6(benchmark_cumulative.loc[date]),
            }
        )
        drawdown.append(
            {
                "date": date_text,
                "portfolio": round6(portfolio_drawdown.loc[date]),
                "benchmark": round6(benchmark_drawdown.loc[date]),
            }
        )
    return {"cumulative": cumulative, "drawdown": drawdown}


def build_security_rows(holdings, asset_returns, benchmark_returns, daily_rf):
    # Run a CAPM regression for every holding and collect the key numbers.
    security_rows = []
    for holding in holdings:
        ticker = holding["ticker"]
        stock_returns = asset_returns[ticker]
        regression = run_capm_regression(stock_returns, benchmark_returns, daily_rf)
        security_rows.append(
            {
                "ticker": ticker,
                "beta": round6(regression["beta"]),
                "alpha_annualized": round6(regression["alpha_annualized"]),
                "r_squared": round6(regression["r_squared"]),
                "alpha_p_value": round6(regression["alpha_p_value"]),
                "beta_p_value": round6(regression["beta_p_value"]),
                "n_obs": regression["n_obs"],
            }
        )
    return security_rows


def build_concentration(holdings):
    # Simple arithmetic about how concentrated the portfolio is.
    number_of_holdings = len(holdings)

    # Find the largest single holding.
    largest_holding = holdings[0]
    for holding in holdings:
        if holding["weight"] > largest_holding["weight"]:
            largest_holding = holding

    # Combined weight of the three biggest holdings.
    weights_sorted = sorted(holdings, key=lambda item: item["weight"], reverse=True)
    top3_weight = 0.0
    for holding in weights_sorted[:3]:
        top3_weight = top3_weight + holding["weight"]

    # Total weight in each sector.
    sector_weights = {}
    for holding in holdings:
        sector = holding["sector"]
        current = sector_weights.get(sector, 0.0)
        sector_weights[sector] = current + holding["weight"]

    rounded_sectors = {}
    for sector, weight in sector_weights.items():
        rounded_sectors[sector] = round6(weight)

    return {
        "number_of_holdings": number_of_holdings,
        "largest_holding_ticker": largest_holding["ticker"],
        "largest_holding_weight": round6(largest_holding["weight"]),
        "top3_weight": round6(top3_weight),
        "sector_weights": rounded_sectors,
    }


def build_analysis(portfolio_id, years):
    # The main entry point: build the complete analysis for one portfolio.
    warnings = []

    # Step 1: load the portfolio and its holdings.
    portfolio, holdings = load_portfolio(portfolio_id)
    holding_tickers = [holding["ticker"] for holding in holdings]

    # Step 2: load prices and check we have enough history.
    price_table = get_price_table(holding_tickers, years)
    daily_returns = metrics.calculate_daily_returns(price_table)
    if len(daily_returns) < MINIMUM_TRADING_DAYS:
        raise NotEnoughData("Not enough overlapping price history.")

    # Step 3: split returns into the stocks and the benchmark.
    asset_returns = daily_returns[holding_tickers]
    benchmark_returns = daily_returns[BENCHMARK_TICKER]

    # Step 4: compute the portfolio's daily returns.
    weights = build_weights_dict(holdings)
    portfolio_returns = metrics.calculate_portfolio_returns(asset_returns, weights)

    # Step 5: match the risk-free rate to the return dates.
    daily_rf = load_daily_risk_free(daily_returns.index, warnings)

    # Step 6: metrics for the portfolio and the benchmark.
    portfolio_metrics = build_metrics_block(portfolio_returns, daily_rf)
    benchmark_metrics = build_metrics_block(benchmark_returns, daily_rf)

    # Extra portfolio-only metrics: beta, correlation, and the drawdown date.
    portfolio_beta = metrics.beta_vs_benchmark(portfolio_returns, benchmark_returns)
    correlation = portfolio_returns.corr(benchmark_returns)
    max_drawdown_date = metrics.drawdown_series(portfolio_returns).idxmin()
    portfolio_metrics["beta"] = round6(portfolio_beta)
    portfolio_metrics["correlation_with_benchmark"] = round6(correlation)
    portfolio_metrics["max_drawdown_date"] = max_drawdown_date.strftime("%Y-%m-%d")

    # Step 7: how the portfolio did versus SPY.
    excess_total = portfolio_metrics["total_return"] - benchmark_metrics["total_return"]
    excess_annual = portfolio_metrics["annualized_return"] - benchmark_metrics["annualized_return"]
    comparison = {
        "excess_total_return": round6(excess_total),
        "excess_annualized_return": round6(excess_annual),
    }

    # Step 8: chart data.
    charts = build_chart_data(portfolio_returns, benchmark_returns)

    # Step 9: per-stock CAPM regressions.
    security_rows = build_security_rows(holdings, asset_returns, benchmark_returns, daily_rf)

    # Step 10: concentration facts.
    concentration = build_concentration(holdings)

    # Step 11: assemble the final response.
    start_date = daily_returns.index[0].strftime("%Y-%m-%d")
    end_date = daily_returns.index[-1].strftime("%Y-%m-%d")

    return {
        "portfolio": {
            "id": portfolio["id"],
            "name": portfolio["name"],
            "holdings": [
                {
                    "ticker": holding["ticker"],
                    "name": holding["name"],
                    "sector": holding["sector"],
                    "weight": round6(holding["weight"]),
                }
                for holding in holdings
            ],
        },
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "trading_days": len(daily_returns),
            "years_requested": years,
        },
        "benchmark": BENCHMARK_TICKER,
        "metrics": portfolio_metrics,
        "benchmark_metrics": benchmark_metrics,
        "comparison": comparison,
        "charts": charts,
        "securities": security_rows,
        "concentration": concentration,
        "warnings": warnings,
    }
