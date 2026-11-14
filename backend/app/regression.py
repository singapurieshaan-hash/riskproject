# regression.py: CAPM regression for one stock against the benchmark.
# CAPM model: stock excess return = alpha + beta x market excess return + error.
import statsmodels.api as sm

from app.metrics import TRADING_DAYS


def run_capm_regression(stock_returns, market_returns, daily_rf):
    # Subtract the risk-free rate so we work with "excess" returns.
    stock_excess = stock_returns - daily_rf
    market_excess = market_returns - daily_rf

    # add_constant gives the regression an intercept (the alpha term).
    x_values = sm.add_constant(market_excess)
    result = sm.OLS(stock_excess, x_values).fit()

    # Position 0 is the intercept (alpha), position 1 is the market slope (beta)
    alpha_daily = result.params.iloc[0]
    beta = result.params.iloc[1]

    return {
        "alpha_daily": float(alpha_daily),
        "alpha_annualized": float(alpha_daily * TRADING_DAYS),
        "beta": float(beta),
        "r_squared": float(result.rsquared),
        "alpha_p_value": float(result.pvalues.iloc[0]),
        "beta_p_value": float(result.pvalues.iloc[1]),
        "n_obs": int(result.nobs),
    }
