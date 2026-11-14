# test_regression.py: checks the CAPM regression on data with a known answer.
# Because the stock is an exact straight line of the market, the fit is perfect.
# Run with: cd backend && pytest -v

import pandas as pd
import pytest

from app.regression import run_capm_regression


def test_perfect_capm_fit():
    # stock = 0.001 + 1.5 x market exactly, so beta=1.5, alpha=0.001, R-squared=1.0.
    market = pd.Series([0.01, -0.02, 0.03, 0.00, 0.02])
    stock = 0.001 + 1.5 * market

    result = run_capm_regression(stock, market, 0)

    assert result["beta"] == pytest.approx(1.5)
    assert result["alpha_daily"] == pytest.approx(0.001)
    assert result["r_squared"] == pytest.approx(1.0)
