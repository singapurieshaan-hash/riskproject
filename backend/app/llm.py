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
2. Always quote the exact number from the JSON when you mention a metric (for example "annualized return of 13.0%").
3. If something is not in the JSON, say it is not available.
4. Do not give investment advice. Never tell the user to buy, sell, or hold anything. You MAY describe the portfolio's past profile (for example "historically strong risk-adjusted returns" or "highly concentrated"), but frame it as a description of the past, not a recommendation.
5. Write in plain language for a beginner. The first time you use a finance term, briefly explain what it means in everyday words.
6. Never show raw JSON field names (for example never write "var_95_1day_pct"). Always use the friendly names given below. Write percentage values with a "%" sign (for example "56.79%"), not the word "percent".
7. Use the exact plain-text structure below. Write each heading on its own line, in capitals, exactly as written, with no "#" or "*" symbols. For the metric list, start each line with "- ". Do not use any other Markdown. Write complete sentences and finish every section.

OVERALL SUMMARY
Two or three sentences giving a plain-language read on the portfolio based on the numbers: how it performed versus the benchmark, how risky it was, and how concentrated it is. Do not say whether anyone should invest.

EACH METRIC EXPLAINED
Write one line per metric, each starting with "- ". Begin each line with the friendly metric name followed by its value, then a short explanation, then how it compares with SPY. Use these exact friendly names, in this order:
- Total return
- Annualized return
- Annualized volatility
- Sharpe ratio
- Maximum drawdown
- Beta (the benchmark SPY always has a beta of 1.00, so compare against 1.00)
- 1-day 95% VaR (there is no benchmark value for this, so just explain what it means, do not say it is unavailable)

DIVERSIFICATION
Two or three sentences on concentration: the number of holdings, the largest holding and its weight, the combined weight of the top 3, and which sectors dominate.

REMINDER
One sentence reminding the reader that these results are based on past data and do not predict the future."""


class LLMUnavailable(Exception):
    # Raised when the key is missing or the API call fails.
    pass


def to_pct(value):
    # Turn a decimal like 0.1234 into a percentage like 12.34, rounded to 2 decimals.
    if value is None:
        return None
    return round(value * 100, 2)


def round2(value):
    # Round a plain ratio (like a Sharpe ratio or beta) to 2 decimals, keeping None.
    if value is None:
        return None
    return round(value, 2)


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
            "sharpe_ratio": round2(portfolio_metrics["sharpe_ratio"]),
            "max_drawdown_pct": to_pct(portfolio_metrics["max_drawdown"]),
            "beta": round2(portfolio_metrics["beta"]),
            "var_95_1day_pct": to_pct(portfolio_metrics["var_95_1day"]),
        },
        "benchmark_SPY": {
            "total_return_pct": to_pct(benchmark_metrics["total_return"]),
            "annualized_return_pct": to_pct(benchmark_metrics["annualized_return"]),
            "annualized_volatility_pct": to_pct(benchmark_metrics["annualized_volatility"]),
            "sharpe_ratio": round2(benchmark_metrics["sharpe_ratio"]),
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
        insights_text = ask_gemini(client, payload_as_json_text)
    except Exception as error:
        raise LLMUnavailable(str(error))

    return insights_text


def ask_gemini(client, user_text):
    # Send one request to Gemini and return the answer text.
    # max_output_tokens is generous so the full explanation is never cut off.
    # thinking_budget=0 turns off Gemini 2.5's hidden "thinking" tokens, which
    # otherwise eat the token budget and can truncate the visible answer.
    # Some older models do not support the thinking setting, so if that specific
    # call fails we try once more without it.
    try:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=2000,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_text,
            config=config,
        )
        return response.text
    except Exception:
        # Fall back to a plain request (no thinking setting) for models that reject it.
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=2000,
        )
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_text,
            config=config,
        )
        return response.text
