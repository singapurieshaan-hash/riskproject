# validation.py: checks the holdings a user sends before we save or analyze them.
# This is a pure function (no database access) so it is easy to test.
# It returns a list of error messages; an empty list means everything is fine.


def validate_holdings(holdings, known_tickers, benchmark_ticker):
    errors = []

    # Rule 1: at least 1 holding and at most 35.
    if len(holdings) < 1:
        errors.append("Add at least one stock.")
    if len(holdings) > 35:
        errors.append("You can hold at most 35 stocks.")

    # Rule 2: no ticker appears twice.
    seen_tickers = []
    for holding in holdings:
        ticker = holding["ticker"]
        if ticker in seen_tickers:
            errors.append(f"Ticker {ticker} appears more than once.")
        seen_tickers.append(ticker)

    # Rule 3: every ticker exists and is not the benchmark.
    for holding in holdings:
        ticker = holding["ticker"]
        if ticker == benchmark_ticker:
            errors.append(f"{ticker} is the benchmark and cannot be a holding.")
        elif ticker not in known_tickers:
            errors.append(f"Unknown ticker: {ticker}.")

    # Rule 4: every weight is greater than 0 and at most 1.
    for holding in holdings:
        weight = holding["weight"]
        if weight <= 0 or weight > 1:
            errors.append(f"Weight for {holding['ticker']} must be between 0 and 1.")

    # Rule 5: the weights add up to 1 (accept 0.999 to 1.001).
    total_weight = 0.0
    for holding in holdings:
        total_weight = total_weight + holding["weight"]
    if total_weight < 0.999 or total_weight > 1.001:
        errors.append(f"Weights must add up to 100%. They currently add up to {total_weight * 100:.2f}%.")

    return errors
