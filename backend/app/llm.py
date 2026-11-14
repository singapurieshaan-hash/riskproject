# llm.py: turns the already-calculated numbers into a plain-language explanation.
# All Gemini-specific code lives here so the provider can be swapped later.
# The model is told to use ONLY the numbers we pass in; it must not calculate anything.

import json

from google import genai
from google.genai import types

from app.config import LLM_API_KEY, LLM_MODEL

DISCLAIMER = "This is educational analysis based on historical data, not investment advice."

SYSTEM_PROMPT = """You are a portfolio research assistant for a student project.
You receive JSON containing portfolio metrics that were already calculated by code.

Rules:
1. Use ONLY numbers that appear in the JSON. Never calculate, estimate, round differently, or invent any number.
2. If something is not in the JSON, say it is not available.
3. Do not give investment advice. Never tell the user to buy, sell, or hold anything.
4. Write in plain language for a beginner. Briefly explain any finance term the first time you use it.
5. Write exactly four short sections with these headings: Risk, Diversification, Drawdown, Benchmark comparison. Use 2 to 3 sentences each.
6. End with one sentence reminding the reader that results are based on past data and do not predict the future."""


class LLMUnavailable(Exception):
    # Raised when the key is missing or the API call fails.
    pass


def to_pct(value):
    # Turn a decimal like 0.1234 into a percentage like 12.34, rounded to 2 decimals.
    if value is None:
        return None
    return round(value * 100, 2)


def build_llm_payload(analysis):
    # Build a small JSON payload where percentages are already converted,
    # so the model never has to do any math itself.
    portfolio_metrics = analysis["metrics"]
    benchmark_metrics = analysis["benchmark_metrics"]
    concentration = analysis["concentration"]

    # Convert each sector weight to a percentage.
    sector_weights_pct = {}
    for sector, weight in concentration["sector_weights"].items():
        sector_weights_pct[sector] = to_pct(weight)

    return {
        "period_years": analysis["period"]["years_requested"],
        "portfolio": {
            "total_return_pct": to_pct(portfolio_metrics["total_return"]),
            "annualized_return_pct": to_pct(portfolio_metrics["annualized_return"]),
            "annualized_volatility_pct": to_pct(portfolio_metrics["annualized_volatility"]),
            "sharpe_ratio": portfolio_metrics["sharpe_ratio"],
            "max_drawdown_pct": to_pct(portfolio_metrics["max_drawdown"]),
            "beta": portfolio_metrics["beta"],
            "var_95_1day_pct": to_pct(portfolio_metrics["var_95_1day"]),
        },
        "benchmark_SPY": {
            "total_return_pct": to_pct(benchmark_metrics["total_return"]),
            "annualized_return_pct": to_pct(benchmark_metrics["annualized_return"]),
            "annualized_volatility_pct": to_pct(benchmark_metrics["annualized_volatility"]),
            "sharpe_ratio": benchmark_metrics["sharpe_ratio"],
            "max_drawdown_pct": to_pct(benchmark_metrics["max_drawdown"]),
        },
        "excess_annualized_return_pct": to_pct(analysis["comparison"]["excess_annualized_return"]),
        "concentration": {
            "number_of_holdings": concentration["number_of_holdings"],
            "largest_holding": concentration["largest_holding_ticker"],
            "largest_holding_weight_pct": to_pct(concentration["largest_holding_weight"]),
            "top3_weight_pct": to_pct(concentration["top3_weight"]),
            "sector_weights_pct": sector_weights_pct,
        },
    }


def generate_insights(analysis):
    # Send the payload to the LLM and return the explanation text.
    # Raises LLMUnavailable if the key is missing or the call fails.
    if not LLM_API_KEY:
        raise LLMUnavailable("LLM_API_KEY is not set.")

    payload = build_llm_payload(analysis)
    payload_as_json_text = json.dumps(payload)

    try:
        # Create a Gemini client using the API key.
        client = genai.Client(api_key=LLM_API_KEY)

        # The system prompt goes in a config object; the JSON payload is the user message.
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=800,
        )
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=payload_as_json_text,
            config=config,
        )
        insights_text = response.text
    except Exception as error:
        raise LLMUnavailable(str(error))

    return insights_text
