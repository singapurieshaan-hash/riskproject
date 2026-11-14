# metrics.py: all risk and performance calculations.
# Inputs are pandas Series of simple daily returns (0.01 means +1 percent).
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def calculate_daily_returns(price_table):
    # price_table: rows = dates, columns = tickers
    # Simple daily return = price_today / price_yesterday - 1
    return price_table.pct_change().dropna()


def calculate_portfolio_returns(asset_returns, weights):
    # weights: dict like {"AAPL": 0.5, "MSFT": 0.5}
    # Constant weights, rebalanced daily.
    weight_series = pd.Series(weights)
    weight_series = weight_series.reindex(asset_returns.columns)
    weighted_returns = asset_returns * weight_series
    return weighted_returns.sum(axis=1)


def total_return(returns):
    # Multiply all the daily growth factors together, then subtract 1.
    growth = (1 + returns).prod()
    return growth - 1


def annualized_return(returns):
    # Geometric: grow the total return to a full 252-day year
    number_of_days = len(returns)
    growth = (1 + returns).prod()
    return growth ** (TRADING_DAYS / number_of_days) - 1


def annualized_volatility(returns):
    # Standard deviation of daily returns scaled up to one year.
    daily_std = returns.std(ddof=1)
    return daily_std * np.sqrt(TRADING_DAYS)


def daily_risk_free(rate_pct_series, dates):
    # rate_pct_series: Series indexed by date, values like 4.85 (percent per year)
    # Match each trading date to the latest known rate.
    rate_pct_series = rate_pct_series.sort_index()
    matched = rate_pct_series.reindex(dates, method="ffill")
    matched = matched.bfill()
    # Convert an annual percent into a daily fraction.
    return matched / 100 / TRADING_DAYS


def sharpe_ratio(returns, daily_rf):
    # daily_rf can be a single number or a Series matching returns.
    # Sharpe = average excess return / its volatility, scaled to one year.
    excess_returns = returns - daily_rf
    daily_std = excess_returns.std(ddof=1)
    if daily_std == 0:
        return None
    return excess_returns.mean() / daily_std * np.sqrt(TRADING_DAYS)


def drawdown_series(returns):
    # Growth of $1, the running peak, and how far below the peak we are.
    wealth = (1 + returns).cumprod()
    running_peak = wealth.cummax()
    return wealth / running_peak - 1


def max_drawdown(returns):
    # The worst (most negative) point of the drawdown series.
    return drawdown_series(returns).min()


def beta_vs_benchmark(returns, benchmark_returns):
    # beta = covariance(portfolio, market) / variance(market)
    covariance_matrix = np.cov(returns, benchmark_returns)
    covariance = covariance_matrix[0, 1]
    benchmark_variance = np.var(benchmark_returns, ddof=1)
    return covariance / benchmark_variance


def historical_var(returns, confidence=0.95):
    # The loss that was only exceeded on (1 - confidence) of days.
    cutoff_percentile = (1 - confidence) * 100
    worst_return = np.percentile(returns, cutoff_percentile)
    return -worst_return


def summarize(returns, daily_rf):
    # Metrics that apply to one return series (portfolio or benchmark)
    return {
        "total_return": total_return(returns),
        "annualized_return": annualized_return(returns),
        "annualized_volatility": annualized_volatility(returns),
        "sharpe_ratio": sharpe_ratio(returns, daily_rf),
        "max_drawdown": max_drawdown(returns),
        "var_95_1day": historical_var(returns, 0.95),
    }
