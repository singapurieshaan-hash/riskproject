# config.py: reads settings from environment variables.
# Loads a local .env file (if present) so running locally is easy.
# Every other module imports the values it needs from here.

import os

from dotenv import load_dotenv

# Load variables from a .env file in the backend folder, if one exists.
load_dotenv()

# Database connection string, for example:
# postgresql://postgres:postgres@localhost:5432/portfolio
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/portfolio")

# Comma-separated list of allowed frontend origins for CORS.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")

# Anthropic API key and model name for the LLM explanation feature.
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
