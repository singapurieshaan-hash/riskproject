# database.py: small helper functions for talking to Postgres with plain SQL.
# No ORM is used here. We open a connection, run a query, and close it.

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import DATABASE_URL


def get_connection():
    # Open a new connection to the database.
    return psycopg2.connect(DATABASE_URL)


def fetch_all(sql, params=None):
    # Run a SELECT and return a list of dictionaries
    connection = get_connection()
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        connection.close()


def save_portfolio(name, holdings):
    # holdings is a list of dicts: {"ticker": "AAPL", "weight": 0.25}
    # Both inserts happen in one transaction: both succeed or neither does.
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO portfolios (name) VALUES (%s) RETURNING id",
                (name,),
            )
            portfolio_id = cursor.fetchone()[0]
            for holding in holdings:
                cursor.execute(
                    "INSERT INTO portfolio_holdings (portfolio_id, ticker, weight) "
                    "VALUES (%s, %s, %s)",
                    (portfolio_id, holding["ticker"], holding["weight"]),
                )
        connection.commit()
        return portfolio_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
