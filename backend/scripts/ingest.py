# ingest.py: downloads price and risk-free-rate data and stores it in Postgres.
# Run by hand with: python scripts/ingest.py
# Safe to run again and again (uses upserts, so no duplicate rows).

import datetime
import os

import pandas as pd
import psycopg2
import yfinance as yf
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

# How many years of history to download (plus a few extra days for safety).
YEARS_OF_HISTORY = 5
EXTRA_DAYS = 10

# The fixed universe of stocks: ticker -> (company name, sector).
# "SPY" is the benchmark and is marked separately below.
TICKERS = {
    "AAPL": ("Apple Inc.", "Technology"),
    "MSFT": ("Microsoft Corporation", "Technology"),
    "NVDA": ("NVIDIA Corporation", "Technology"),
    "ADBE": ("Adobe Inc.", "Technology"),
    "GOOGL": ("Alphabet Inc.", "Communication"),
    "META": ("Meta Platforms, Inc.", "Communication"),
    "DIS": ("The Walt Disney Company", "Communication"),
    "AMZN": ("Amazon.com, Inc.", "Consumer Discretionary"),
    "HD": ("The Home Depot, Inc.", "Consumer Discretionary"),
    "MCD": ("McDonald's Corporation", "Consumer Discretionary"),
    "NKE": ("NIKE, Inc.", "Consumer Discretionary"),
    "PG": ("The Procter & Gamble Company", "Consumer Staples"),
    "KO": ("The Coca-Cola Company", "Consumer Staples"),
    "WMT": ("Walmart Inc.", "Consumer Staples"),
    "COST": ("Costco Wholesale Corporation", "Consumer Staples"),
    "JNJ": ("Johnson & Johnson", "Health Care"),
    "UNH": ("UnitedHealth Group Incorporated", "Health Care"),
    "PFE": ("Pfizer Inc.", "Health Care"),
    "LLY": ("Eli Lilly and Company", "Health Care"),
    "JPM": ("JPMorgan Chase & Co.", "Financials"),
    "BAC": ("Bank of America Corporation", "Financials"),
    "V": ("Visa Inc.", "Financials"),
    "GS": ("The Goldman Sachs Group, Inc.", "Financials"),
    "XOM": ("Exxon Mobil Corporation", "Energy"),
    "CVX": ("Chevron Corporation", "Energy"),
    "CAT": ("Caterpillar Inc.", "Industrials"),
    "BA": ("The Boeing Company", "Industrials"),
    "UPS": ("United Parcel Service, Inc.", "Industrials"),
    "HON": ("Honeywell International Inc.", "Industrials"),
    "NEE": ("NextEra Energy, Inc.", "Utilities"),
    "DUK": ("Duke Energy Corporation", "Utilities"),
    "LIN": ("Linde plc", "Materials"),
    "PLD": ("Prologis, Inc.", "Real Estate"),
    "AMT": ("American Tower Corporation", "Real Estate"),
    "SPY": ("SPDR S&P 500 ETF Trust", "Benchmark"),
}

BENCHMARK_TICKER = "SPY"


def get_connection():
    # Connect to Postgres using the DATABASE_URL environment variable.
    database_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(database_url)


def save_securities(connection):
    # Insert or update every ticker in the securities table.
    rows = []
    for ticker, (name, sector) in TICKERS.items():
        is_benchmark = ticker == BENCHMARK_TICKER
        rows.append((ticker, name, sector, is_benchmark))

    sql = """
        INSERT INTO securities (ticker, name, sector, is_benchmark)
        VALUES %s
        ON CONFLICT (ticker)
        DO UPDATE SET name = EXCLUDED.name,
                      sector = EXCLUDED.sector,
                      is_benchmark = EXCLUDED.is_benchmark
    """
    with connection.cursor() as cursor:
        execute_values(cursor, sql, rows)
    connection.commit()


def get_start_date():
    # Start date is today minus 5 years and 10 extra days.
    today = datetime.date.today()
    days_back = YEARS_OF_HISTORY * 365 + EXTRA_DAYS
    return today - datetime.timedelta(days=days_back)


def download_prices(all_tickers, start_date):
    # Download adjusted closing prices for all tickers at once.
    # auto_adjust=True means the "Close" column is already split/dividend adjusted.
    raw = yf.download(
        all_tickers,
        start=start_date,
        auto_adjust=True,
        progress=False,
    )
    close_table = raw["Close"]
    return close_table


def clean_prices(close_table):
    problems = []

    # Remove days where nothing traded (holidays)
    close_table = close_table.dropna(how="all")

    # Drop tickers with too many missing days
    for ticker in list(close_table.columns):
        missing_percent = close_table[ticker].isna().mean() * 100
        if missing_percent > 5:
            problems.append(f"Dropped {ticker}: {missing_percent:.1f}% missing days")
            close_table = close_table.drop(columns=[ticker])

    # Fill small gaps by carrying the last price forward (max 3 days)
    close_table = close_table.ffill(limit=3)
    return close_table, problems


def save_prices(connection, close_table):
    rows = []
    for ticker in close_table.columns:
        prices_for_ticker = close_table[ticker].dropna()
        for price_date, price in prices_for_ticker.items():
            rows.append((ticker, price_date.date(), float(price)))

    sql = """
        INSERT INTO prices (ticker, price_date, adj_close)
        VALUES %s
        ON CONFLICT (ticker, price_date)
        DO UPDATE SET adj_close = EXCLUDED.adj_close
    """
    with connection.cursor() as cursor:
        execute_values(cursor, sql, rows, page_size=1000)
    connection.commit()
    return len(rows)


def save_csv_backup(close_table):
    # Save a CSV copy of the prices so the data is not lost if the DB is wiped.
    this_folder = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(this_folder, "..", "data")
    os.makedirs(data_folder, exist_ok=True)
    backup_path = os.path.join(data_folder, "prices_backup.csv")
    close_table.to_csv(backup_path)


def download_risk_free_rate(start_date):
    # Download the 3-month T-bill rate (FRED series DTB3) as a CSV, no API key.
    fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3"
    raw = pd.read_csv(fred_url)

    # Rename the two columns by position to known names.
    raw.columns = ["rate_date", "rate_pct"]

    # Missing values in FRED come as the text ".", so coerce to numbers.
    raw["rate_pct"] = pd.to_numeric(raw["rate_pct"], errors="coerce")
    raw = raw.dropna()

    # Parse dates and keep only recent rows.
    raw["rate_date"] = pd.to_datetime(raw["rate_date"]).dt.date
    cutoff = start_date
    recent = raw[raw["rate_date"] >= cutoff]
    return recent


def save_risk_free_rate(connection, rate_table):
    rows = []
    for _, row in rate_table.iterrows():
        rows.append((row["rate_date"], float(row["rate_pct"])))

    sql = """
        INSERT INTO risk_free_rates (rate_date, rate_pct)
        VALUES %s
        ON CONFLICT (rate_date)
        DO UPDATE SET rate_pct = EXCLUDED.rate_pct
    """
    with connection.cursor() as cursor:
        execute_values(cursor, sql, rows, page_size=1000)
    connection.commit()
    return len(rows)


def print_summary(connection, problems):
    # Print a short report of what is now in the database.
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM prices")
        ticker_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), MIN(price_date), MAX(price_date) FROM prices")
        price_count, earliest, latest = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM risk_free_rates")
        rate_count = cursor.fetchone()[0]

    print("")
    print("=== Ingestion summary ===")
    print(f"Tickers with prices : {ticker_count}")
    print(f"Price rows          : {price_count}")
    print(f"Earliest date       : {earliest}")
    print(f"Latest date         : {latest}")
    print(f"Risk-free rows      : {rate_count}")
    if problems:
        print("Problems found:")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("Problems found     : none")


def main():
    problems = []
    connection = get_connection()

    try:
        # Step 1-2: make sure the securities table is up to date.
        save_securities(connection)

        # Step 3: download prices for every ticker at once.
        all_tickers = list(TICKERS.keys())
        start_date = get_start_date()
        close_table = download_prices(all_tickers, start_date)

        # Note any requested ticker that did not download at all.
        downloaded_tickers = set(close_table.columns)
        for ticker in all_tickers:
            if ticker not in downloaded_tickers:
                problems.append(f"Ticker did not download: {ticker}")

        # Step 4: clean the data.
        close_table, clean_problems = clean_prices(close_table)
        problems.extend(clean_problems)

        # The benchmark is required; stop if it is missing.
        if BENCHMARK_TICKER not in close_table.columns:
            raise SystemExit("ERROR: SPY (benchmark) is missing after cleaning. Cannot continue.")

        # Step 5: save prices to Postgres.
        saved_price_rows = save_prices(connection, close_table)
        print(f"Saved {saved_price_rows} price rows.")

        # Step 6: save a CSV backup.
        save_csv_backup(close_table)

        # Step 7: download and save the risk-free rate (do not crash if it fails).
        try:
            rate_table = download_risk_free_rate(start_date)
            saved_rate_rows = save_risk_free_rate(connection, rate_table)
            print(f"Saved {saved_rate_rows} risk-free-rate rows.")
        except Exception as error:
            problems.append(f"Risk-free rate download failed: {error}")
            print(f"WARNING: risk-free rate download failed: {error}")

        # Step 8: print a summary.
        print_summary(connection, problems)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
