# test_validation.py: checks that validate_holdings accepts good input
# and reports an error for each kind of bad input.
# Run with: cd backend && pytest -v

from app.validation import validate_holdings

KNOWN_TICKERS = ["AAPL", "MSFT", "JPM"]
BENCHMARK = "SPY"


def test_good_holdings_have_no_errors():
    holdings = [
        {"ticker": "AAPL", "weight": 0.5},
        {"ticker": "MSFT", "weight": 0.5},
    ]
    errors = validate_holdings(holdings, KNOWN_TICKERS, BENCHMARK)
    assert errors == []


def test_empty_list_is_rejected():
    errors = validate_holdings([], KNOWN_TICKERS, BENCHMARK)
    assert len(errors) > 0


def test_duplicate_ticker_is_rejected():
    holdings = [
        {"ticker": "AAPL", "weight": 0.5},
        {"ticker": "AAPL", "weight": 0.5},
    ]
    errors = validate_holdings(holdings, KNOWN_TICKERS, BENCHMARK)
    assert len(errors) > 0


def test_unknown_ticker_is_rejected():
    holdings = [{"ticker": "ZZZZ", "weight": 1.0}]
    errors = validate_holdings(holdings, KNOWN_TICKERS, BENCHMARK)
    assert len(errors) > 0


def test_benchmark_as_holding_is_rejected():
    holdings = [{"ticker": "SPY", "weight": 1.0}]
    errors = validate_holdings(holdings, KNOWN_TICKERS, BENCHMARK)
    assert len(errors) > 0


def test_zero_weight_is_rejected():
    holdings = [
        {"ticker": "AAPL", "weight": 0.0},
        {"ticker": "MSFT", "weight": 1.0},
    ]
    errors = validate_holdings(holdings, KNOWN_TICKERS, BENCHMARK)
    assert len(errors) > 0


def test_weights_not_summing_to_one_are_rejected():
    holdings = [
        {"ticker": "AAPL", "weight": 0.4},
        {"ticker": "MSFT", "weight": 0.4},
    ]
    errors = validate_holdings(holdings, KNOWN_TICKERS, BENCHMARK)
    assert len(errors) > 0
