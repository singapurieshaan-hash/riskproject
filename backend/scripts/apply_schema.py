# apply_schema.py: creates the database tables.
# Reads sql/schema.sql and runs it against the database in DATABASE_URL.
# Safe to run many times because the schema uses IF NOT EXISTS.

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Folder that holds this script, so we can find schema.sql next to it.
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(THIS_FOLDER, "..", "sql", "schema.sql")

database_url = os.getenv("DATABASE_URL")

with open(SCHEMA_PATH, "r") as schema_file:
    schema_sql = schema_file.read()

connection = psycopg2.connect(database_url)
with connection.cursor() as cursor:
    cursor.execute(schema_sql)
connection.commit()
connection.close()

print("Schema applied successfully.")
