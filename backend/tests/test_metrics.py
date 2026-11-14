# test_metrics.py: checks the risk and performance math against hand-calculated values.
# Run with: cd backend && pytest -v

import pandas as pd
import pytest

from app.metrics import (
    annualized_volatility,
    beta_vs_benchmark,
    calculate_daily_returns,
    calculate_portfolio_returns,
    historical_var,
    max_drawdown,
    sharpe_ratio,
    total_return,
)


def test_total_return():
    # 1.1 x 0.9 = 0.99, so the total return is -0.01.
    returns = pd.Series([0.10, -0.10])
    assert total_return(returns) == pytest.approx(-0.01)


def test_max_drawdown():
    # Prices go 100 -> 120 -> 60 -> 90. Peak is 120, low is 60.
    # The worst drawdown is 60/120 - 1 = -0.5.
    prices = pd.Series([100.0, 120.0, 60.0, 90.0])
    returns = calculate_daily_returns(prices.to_frame("x"))["x"]
    assert max_drawdown(returns) == pytest.approx(-0.5)


def test_annualized_volatility():
    returns = pd.Series([0.01, -0.01])
    assert annualized_volatility(returns) == pytest.approx(0.2245, abs=1e-4)


def test_sharpe_ratio():
    # mean 0.02, std 0.014142, times sqrt(252) -> about 22.4499
    returns = pd.Series([0.01, 0.03])
    assert sharpe_ratio(returns, 0) == pytest.approx(22.4499, abs=1e-3)


def test_beta():
    # Portfolio is exactly 2x the market, so beta must be 2.0.
    market = pd.Series([0.01, -0.02, 0.03, 0.00])
    portfolio = market * 2
    assert beta_vs_benchmark(portfolio, market) == pytest.approx(2.0)


def test_historical_var():
    # 95% VaR: the 5th percentile of these returns is -0.09.
    returns = pd.Series([-0.10, -0.05, 0.00, 0.05, 0.10])
    assert historical_var(returns, 0.95) == pytest.approx(0.09)


def test_portfolio_returns():
    # Two stocks, equal weights. Day 1: (0.10+0.00)/2 = 0.05. Day 2: (0.00+0.10)/2 = 0.05.
    asset_returns = pd.DataFrame(
        {
            "AAA": [0.10, 0.00],
            "BBB": [0.00, 0.10],
        }
    )
    weights = {"AAA": 0.5, "BBB": 0.5}
    result = calculate_portfolio_returns(asset_returns, weights)
    assert result.iloc[0] == pytest.approx(0.05)
    assert result.iloc[1] == pytest.approx(0.05)


def test_sharpe_with_no_variance():
    # Constant returns have zero volatility, so Sharpe is undefined (None).
    returns = pd.Series([0.01, 0.01])
    assert sharpe_ratio(returns, 0) is None
