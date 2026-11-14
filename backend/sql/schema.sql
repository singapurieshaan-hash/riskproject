-- schema.sql: database tables for the portfolio analytics app.
-- Holds the stock universe, adjusted daily prices, the risk-free rate,
-- and any portfolios a user saves. Safe to run many times (IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS securities (
    ticker        TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    sector        TEXT,
    is_benchmark  BOOLEAN NOT NULL DEFAULT FALSE
);

-- Split- and dividend-adjusted daily closes
CREATE TABLE IF NOT EXISTS prices (
    ticker      TEXT NOT NULL REFERENCES securities (ticker) ON DELETE CASCADE,
    price_date  DATE NOT NULL,
    adj_close   NUMERIC(18, 6) NOT NULL CHECK (adj_close > 0),
    PRIMARY KEY (ticker, price_date)
);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (price_date);

-- 3-month T-bill rate (FRED series DTB3) as annual percent, for example 4.85
CREATE TABLE IF NOT EXISTS risk_free_rates (
    rate_date  DATE PRIMARY KEY,
    rate_pct   NUMERIC(8, 4) NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolios (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- weight is a fraction: 0.25 means 25 percent
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    portfolio_id  INT  NOT NULL REFERENCES portfolios (id) ON DELETE CASCADE,
    ticker        TEXT NOT NULL REFERENCES securities (ticker),
    weight        NUMERIC(7, 6) NOT NULL CHECK (weight > 0 AND weight <= 1),
    PRIMARY KEY (portfolio_id, ticker)
);
